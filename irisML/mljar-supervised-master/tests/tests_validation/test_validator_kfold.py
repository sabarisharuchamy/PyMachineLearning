import unittest
import numpy as np
import pandas as pd
from supervised.validation.validator_kfold import KFoldValidator

import os
import shutil


class KFoldValidatorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("SETUP CLASS")
        cls._results_path = "/tmp/k_fold_test"
        os.mkdir(cls._results_path)

    @classmethod
    def tearDownClass(cls):
        print("TEAR DOWN CLASS")

        shutil.rmtree(cls._results_path, ignore_errors=True)

    def test_create(self):

        data = {
            "X": pd.DataFrame(
                np.array([[0, 0], [0, 1], [1, 0], [1, 1]]), columns=["a", "b"]
            ),
            "y": pd.DataFrame(np.array([0, 0, 1, 1]), columns=["target"]),
        }

        X_path = os.path.join(self._results_path, "X.parquet")
        y_path = os.path.join(self._results_path, "y.parquet")

        data["X"].to_parquet(X_path, index=False)
        data["y"].to_parquet(y_path, index=False)

        params = {
            "shuffle": False,
            "stratify": False,
            "k_folds": 2,
            "results_path": self._results_path,
            "X_path": X_path,
            "y_path": y_path,
        }
        vl = KFoldValidator(params)

        self.assertEqual(params["k_folds"], vl.get_n_splits())
        # for train, validation in vl.split():
        for k_fold in range(vl.get_n_splits()):
            train, validation = vl.get_split(k_fold)

            X_train, y_train = train.get("X"), train.get("y")
            X_validation, y_validation = validation.get("X"), validation.get("y")

            self.assertEqual(X_train.shape[0], 2)
            self.assertEqual(y_train.shape[0], 2)
            self.assertEqual(X_validation.shape[0], 2)
            self.assertEqual(y_validation.shape[0], 2)

    def test_missing_target_values(self):

        data = {
            "X": pd.DataFrame(
                np.array([[1, 0], [2, 1], [3, 0], [4, 1], [5, 1], [6, 1]]),
                columns=["a", "b"],
            ),
            "y": pd.DataFrame(
                np.array(["a", "b", "a", "b", np.nan, np.nan]), columns=["target"]
            ),
        }

        X_path = os.path.join(self._results_path, "X.parquet")
        y_path = os.path.join(self._results_path, "y.parquet")

        data["X"].to_parquet(X_path, index=False)
        data["y"].to_parquet(y_path, index=False)

        params = {
            "shuffle": True,
            "stratify": True,
            "k_folds": 2,
            "results_path": self._results_path,
            "X_path": X_path,
            "y_path": y_path,
        }
        vl = KFoldValidator(params)

        self.assertEqual(params["k_folds"], vl.get_n_splits())

        for k_fold in range(vl.get_n_splits()):
            train, validation = vl.get_split(k_fold)
            X_train, y_train = train.get("X"), train.get("y")
            X_validation, y_validation = validation.get("X"), validation.get("y")

            self.assertEqual(X_train.shape[0], 2)
            self.assertEqual(y_train.shape[0], 2)
            self.assertEqual(X_validation.shape[0], 2)
            self.assertEqual(y_validation.shape[0], 2)

    def test_create_with_target_as_labels(self):

        data = {
            "X": pd.DataFrame(
                np.array([[0, 0], [0, 1], [1, 0], [1, 1]]), columns=["a", "b"]
            ),
            "y": pd.DataFrame(np.array(["a", "b", "a", "b"]), columns=["target"]),
        }

        X_path = os.path.join(self._results_path, "X.parquet")
        y_path = os.path.join(self._results_path, "y.parquet")

        data["X"].to_parquet(X_path, index=False)
        data["y"].to_parquet(y_path, index=False)

        params = {
            "shuffle": True,
            "stratify": True,
            "k_folds": 2,
            "results_path": self._results_path,
            "X_path": X_path,
            "y_path": y_path,
        }
        vl = KFoldValidator(params)

        self.assertEqual(params["k_folds"], vl.get_n_splits())

        for k_fold in range(vl.get_n_splits()):
            train, validation = vl.get_split(k_fold)
            X_train, y_train = train.get("X"), train.get("y")
            X_validation, y_validation = validation.get("X"), validation.get("y")

            self.assertEqual(X_train.shape[0], 2)
            self.assertEqual(y_train.shape[0], 2)
            self.assertEqual(X_validation.shape[0], 2)
            self.assertEqual(y_validation.shape[0], 2)
