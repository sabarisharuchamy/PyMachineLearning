import os
import gc
import logging
import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

from sklearn.model_selection import train_test_split
from supervised.validation.validator_base import BaseValidator
from supervised.exceptions import AutoMLException

from supervised.utils.config import mem
import time


class SplitValidator(BaseValidator):
    def __init__(self, params):
        BaseValidator.__init__(self, params)

        self.train_ratio = self.params.get("train_ratio", 0.8)
        self.shuffle = self.params.get("shuffle", True)
        self.stratify = self.params.get("stratify", False)
        self.random_seed = self.params.get("random_seed", 1234)
        log.debug("SplitValidator, train_ratio: {0}".format(self.train_ratio))

        self._results_path = self.params.get("results_path")
        self._X_path = self.params.get("X_path")
        self._y_path = self.params.get("y_path")

        if self._X_path is None or self._y_path is None:
            raise AutoMLException("No data path set in SplitValidator params")

    def get_split(self, k=0):

        X = pd.read_parquet(self._X_path)
        y = pd.read_parquet(self._y_path)
        y = y["target"]

        stratify = None
        if self.stratify:
            stratify = y
        if self.shuffle == False:
            stratify = None

        X_train, X_validation, y_train, y_validation = train_test_split(
            X,
            y,
            train_size=self.train_ratio,
            test_size=1.0 - self.train_ratio,
            shuffle=self.shuffle,
            stratify=stratify,
            random_state=self.random_seed,
        )
        return {"X": X_train, "y": y_train}, {"X": X_validation, "y": y_validation}

    def get_n_splits(self):
        return 1


"""
import numpy as np
import pandas as pd

from sklearn.utils.fixes import bincount
from sklearn.model_selection import train_test_split

import logging
logger = logging.getLogger('mljar')


def validation_split(train, validation_train_split, stratify, shuffle, random_seed):

    if shuffle:
    else:
        if stratify is None:
            train, validation = data_split(validation_train_split, train)
        else:
            train, validation = data_split_stratified(validation_train_split, train, stratify)
    return train, validation


"""
