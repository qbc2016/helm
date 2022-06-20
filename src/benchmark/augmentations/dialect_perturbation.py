from dataclasses import dataclass
import json
import os
import random
import re
from pathlib import Path
from typing import Dict, Optional, List

from benchmark.scenario import Instance
from common.general import match_case, ensure_file_downloaded
from .perturbation_description import PerturbationDescription
from .perturbation import Perturbation


class DialectPerturbation(Perturbation):
    """ Individual fairness perturbation for dialect. """

    """ Short unique identifier of the perturbation (e.g., extra_space) """
    name: str = "dialect"

    """ Output path to store external files and folders """
    OUTPUT_PATH = os.path.join("benchmark_output", "perturbations", name)

    """ Dictionary mapping dialects to one another """
    SAE = "SAE"
    AAVE = "AAVE"

    """ Dictionary containing the URIs for the dialect mapping dictionaries

    Keys are tuples of the form (source_class, target_class), such as
    ("SAE", "AAVE"). Mapping dictionaries are from the sources listed below,
    converted to JSON and stored in CodaLab.

        (1) SAE to AAVE dictionary is from Ziems et al. (2022)

                Paper: https://arxiv.org/abs/2204.03031
                GitHub: https://github.com/GT-SALT/value/

    """
    MAPPING_DICT_URIS = {
        (SAE, AAVE): "https://worksheets.codalab.org/rest/bundles/0x3523e02bd46b42bcad783292b40b4e38/contents/blob/"
    }

    @dataclass(frozen=True)
    class Description(PerturbationDescription):
        """ Description for the DialectPerturbation class. """

        name: str
        robustness: bool
        fairness: bool
        prob: float
        source_class: str
        target_class: str
        mapping_file_path: Optional[str]

    def __init__(self, prob: float, source_class: str, target_class: str, mapping_file_path: Optional[str] = None):
        """ Initialize the dialect perturbation.

        If mapping_file_path is not provided, (source_class, target_class)
        should be ("SAE", "AAVE").

        Args:
            prob: Probability of substituting a word in the original class with
                a word in the target class given that a substitution is
                available.
            source_class: The source dialect that will be substituted with
                the target dialect. Case-insensitive.
            target_class: The target dialect.
            mapping_file_path: The absolute path to a file containing the
                word mappings from the source dialect to the target dialect in
                a json format. The json dictionary must be of type
                Dict[str, List[str]]. Otherwise, the default dictionary in
                self.MAPPING_DICTS for the provided source and target classes
                will be used, if available.
        """
        # @TODO: This field should be inherited from the base perturbation class
        self.output_path: str = self.OUTPUT_PATH
        Path(self.output_path).mkdir(parents=True, exist_ok=True)

        # Random generator specific to this class, will be set in the apply function
        self.random: random.Random

        # Assign parameters to instance variables
        assert 0 <= prob <= 1
        self.prob = prob
        self.source_class: str = source_class.upper()
        self.target_class: str = target_class.upper()

        if mapping_file_path:
            self.mapping_file_path: str = mapping_file_path
        else:
            self.mapping_file_path = self.retrieve_mapping_dict()
        self.mapping_dict: Dict[str, List[str]] = self.load_mapping_dict()

    @property
    def description(self) -> PerturbationDescription:
        """ Return a perturbation description for this class. """
        return DialectPerturbation.Description(
            name=self.name,
            robustness=False,
            fairness=True,
            prob=self.prob,
            source_class=self.source_class,
            target_class=self.target_class,
            mapping_file_path=self.mapping_file_path,
        )

    def retrieve_mapping_dict(self) -> str:
        """ Download the mapping dict for self.source_class to self.target_class, if available. """
        mapping_tuple = (self.source_class, self.target_class)
        if mapping_tuple not in self.MAPPING_DICT_URIS:
            msg = f"""The mapping from the source class {self.source_class} to the
                      target class {self.target_class} isn't available in {self.MAPPING_DICT_URIS}.
                   """
            raise ValueError(msg)
        file_name = f"{self.source_class}_to_{self.target_class}_mapping.json"
        target_file_path: str = os.path.join(self.output_path, file_name)
        ensure_file_downloaded(source_url=self.MAPPING_DICT_URIS[mapping_tuple], target_path=target_file_path)
        return target_file_path

    def load_mapping_dict(self) -> Dict[str, List[str]]:
        """ Load the mapping dict. """
        with open(self.mapping_file_path, "r") as f:
            return json.load(f)

    def substitute_dialect(self, text: str) -> str:
        """ Substitute the source dialect in text with the target dialect with probability self.prob. """

        # Pattern capturing any occurence of the given words in the text, surrounded by characters other than
        # alphanumeric characters and '-'. We use re.escape since the words in our dictionary may
        # contain special RegEx characters.
        words = [re.escape(w) for w in self.mapping_dict.keys()]
        words_string = "|".join(words)
        pattern = f"[^\\w-]({words_string})[^\\w-]"

        # Substitution function
        def sub_func(m: re.Match):
            match_str = m.group(0)  # The full match (e.g. " With ", " With,", " With.")
            word = m.group(1)  # Captured group (e.g. "With")
            if self.random.uniform(0, 1) < self.prob:
                synonyms = self.mapping_dict[word.lower()]
                synonym = self.random.choice(synonyms)  # Synonym (e.g. "wit")
                synonym = match_case(word, synonym)  # Synoynm with matching case (e.g. "Wit")
                match_str = match_str.replace(
                    word, synonym
                )  # Synonym placed in the matching group (e.g. " Wit ", " Wit,", " Wit.")
            return match_str

        # Execute the RegEx
        return re.sub(pattern, sub_func, text, flags=re.IGNORECASE)

    def apply(self, instance: Instance, should_perturb_references: bool = True) -> Instance:
        """ Apply the perturbation to the provided instance. """
        assert instance.id is not None
        self.random = random.Random(int(instance.id[2:]))
        return super().apply(instance, should_perturb_references)

    def perturb(self, text: str) -> str:
        """ Perturb the provided text. """
        return self.substitute_dialect(text)
