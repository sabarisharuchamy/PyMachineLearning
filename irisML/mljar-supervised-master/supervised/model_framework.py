import uuid
import numpy as np
import pandas as pd
import time
import zipfile
import os
import copy
import logging
import json

from supervised.callbacks.callback_list import CallbackList
from supervised.validation.validation_step import ValidationStep
from supervised.algorithms.factory import AlgorithmFactory
from supervised.preprocessing.preprocessing import Preprocessing
from supervised.preprocessing.exclude_missing_target import ExcludeRowsMissingTarget
from supervised.algorithms.registry import AlgorithmsRegistry
from supervised.exceptions import AutoMLException
from supervised.utils.config import LOG_LEVEL
from supervised.utils.additional_metrics import AdditionalMetrics

from supervised.algorithms.registry import (
    BINARY_CLASSIFICATION,
    MULTICLASS_CLASSIFICATION,
    REGRESSION,
)

logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)

from supervised.utils.config import mem
from supervised.utils.learning_curves import LearningCurves


class ModelFramework:
    def __init__(self, params, callbacks=[]):
        logger.debug("ModelFramework.__init__")
        self.uid = str(uuid.uuid4())

        for i in ["learner", "validation_strategy"]:  # mandatory parameters
            if i not in params:
                msg = "Missing {0} parameter in ModelFramework params".format(i)
                logger.error(msg)
                raise ValueError(msg)

        self.params = params
        self.callbacks = CallbackList(callbacks)

        self._name = params.get("name", "model")
        self.additional_params = params.get("additional")
        self.preprocessing_params = params.get("preprocessing")
        self.validation_params = params.get("validation_strategy")
        self.learner_params = params.get("learner")

        self._ml_task = params.get("ml_task")
        self._explain_level = params.get("explain_level")
        self._is_stacked = params.get("is_stacked", False)

        self.validation = None
        self.preprocessings = []
        self.learners = []

        self.train_time = None
        self.final_loss = None
        self.metric_name = None
        self.oof_predictions = None
        self._additional_metrics = None
        self._threshold = None  # used only for binary classifiers

    def get_train_time(self):
        return self.train_time

    def predictions(
        self, learner, preproces, X_train, y_train, X_validation, y_validation
    ):
        y_train_true = y_train
        y_train_predicted = learner.predict(X_train)
        y_validation_true = y_validation
        y_validation_predicted = learner.predict(X_validation)

        y_train_true = preproces.inverse_scale_target(y_train_true)
        y_train_predicted = preproces.inverse_scale_target(y_train_predicted)
        y_validation_true = preproces.inverse_scale_target(y_validation_true)
        y_validation_predicted = preproces.inverse_scale_target(y_validation_predicted)

        y_validation_columns = []
        if self._ml_task == MULTICLASS_CLASSIFICATION:
            # y_train_true = preproces.inverse_categorical_target(y_train_true)
            # y_validation_true = preproces.inverse_categorical_target(y_validation_true)
            # get columns, omit the last one (it is label)
            y_validation_columns = preproces.prepare_target_labels(
                y_validation_predicted
            ).columns.tolist()[:-1]

        return {
            "y_train_true": y_train_true,
            "y_train_predicted": y_train_predicted,
            "y_validation_true": y_validation_true,
            "y_validation_predicted": y_validation_predicted,
            "validation_index": X_validation.index,
            "validation_columns": y_validation_columns,
        }

    def train(self, model_path):
        logger.debug(f"ModelFramework.train {self.learner_params.get('model_type')}")

        start_time = time.time()
        np.random.seed(self.learner_params["seed"])

        self.validation = ValidationStep(self.validation_params)

        for k_fold in range(self.validation.get_n_splits()):
            train_data, validation_data = self.validation.get_split(k_fold)
            logger.debug(
                "Data split, train X:{} y:{}, validation X:{}, y:{}".format(
                    train_data["X"].shape,
                    train_data["y"].shape,
                    validation_data["X"].shape,
                    validation_data["y"].shape,
                )
            )

            # the proprocessing is done at every validation step
            self.preprocessings += [Preprocessing(self.preprocessing_params)]

            X_train, y_train = self.preprocessings[-1].fit_and_transform(
                train_data["X"], train_data["y"]
            )
            X_validation, y_validation = self.preprocessings[-1].transform(
                validation_data["X"], validation_data["y"]
            )

            self.learner_params["explain_level"] = self._explain_level
            self.learners += [
                AlgorithmFactory.get_algorithm(copy.deepcopy(self.learner_params))
            ]
            learner = self.learners[-1]

            self.callbacks.add_and_set_learner(learner)
            self.callbacks.on_learner_train_start()

            log_to_file = os.path.join(model_path, f"learner_{k_fold+1}_training.log")

            for i in range(learner.max_iters):

                self.callbacks.on_iteration_start()

                learner.fit(X_train, y_train, X_validation, y_validation, log_to_file)

                self.callbacks.on_iteration_end(
                    {"iter_cnt": i},
                    self.predictions(
                        learner,
                        self.preprocessings[-1],
                        X_train,
                        y_train,
                        X_validation,
                        y_validation,
                    ),
                )

                if learner.stop_training:
                    break
                learner.update({"step": i})

            # end of learner iters loop
            self.callbacks.on_learner_train_end()

            learner.interpret(
                X_train,
                y_train,
                X_validation,
                y_validation,
                model_file_path=model_path,
                learner_name=f"learner_{k_fold+1}",
                class_names=self.preprocessings[-1].get_target_class_names(),
                metric_name=self.get_metric_name(),
                ml_task=self._ml_task,
                explain_level=self._explain_level,
            )

            # save learner and free the memory
            p = os.path.join(
                model_path, f"learner_{k_fold+1}.{learner.file_extension()}"
            )
            learner.save(p)
            del learner.model
            learner.model = None
            # end of learner training

        # end of validation loop
        self.callbacks.on_framework_train_end()
        self.get_additional_metrics()
        self.train_time = time.time() - start_time
        logger.debug("ModelFramework end of training")

    def get_metric_name(self):
        if self.metric_name is not None:
            return self.metric_name
        early_stopping = self.callbacks.get("early_stopping")
        if early_stopping is None:
            return None
        self.metric_name = early_stopping.metric.name
        return early_stopping.metric.name

    def get_out_of_folds(self):
        if self.oof_predictions is not None:
            return self.oof_predictions
        early_stopping = self.callbacks.get("early_stopping")
        if early_stopping is None:
            return None
        self.oof_predictions = early_stopping.best_y_oof

        ###############################################################
        # in case of Neural Network and one-hot coded multiclass target
        target_cols = [
            c for c in self.oof_predictions.columns.tolist() if "target" in c
        ]
        if len(target_cols) > 1:
            target = self.oof_predictions[target_cols[0]].copy()
            target.name = "target"
            for i, t in enumerate(target_cols):
                target[self.oof_predictions[t] == 1] = i
            self.oof_predictions.drop(target_cols, axis=1, inplace=True)

            self.oof_predictions.insert(0, "target", np.array(target))

        return early_stopping.best_y_oof

    def get_final_loss(self):
        if self.final_loss is not None:
            return self.final_loss
        early_stopping = self.callbacks.get("early_stopping")
        if early_stopping is None:
            return None
        self.final_loss = early_stopping.final_loss
        return early_stopping.final_loss

    """
    def get_metric_logs(self):
        metric_logger = self.callbacks.get("metric_logger")
        if metric_logger is None:
            return None
        return metric_logger.loss_values
    """

    def get_type(self):
        return self.learner_params.get("model_type")

    def get_name(self):
        return self._name

    def is_valid(self):
        """ is_valid is used in Ensemble to check if it has more than 1 model in it.
            If Ensemble has only 1 model in it, then Ensemble shouldn't be used as best model """
        return True

    def predict(self, X):
        logger.debug("ModelFramework.predict")

        if self.learners is None or len(self.learners) == 0:
            raise Exception("Learnes are not initialized")
        # run predict on all learners and return the average
        y_predicted = None  # np.zeros((X.shape[0],))
        for ind, learner in enumerate(self.learners):
            # preprocessing goes here
            X_data, _ = self.preprocessings[ind].transform(X.copy(), None)
            y_p = learner.predict(X_data)
            y_p = self.preprocessings[ind].inverse_scale_target(y_p)

            y_predicted = y_p if y_predicted is None else y_predicted + y_p

        y_predicted_average = y_predicted / float(len(self.learners))

        y_predicted_final = self.preprocessings[0].prepare_target_labels(
            y_predicted_average
        )

        return y_predicted_final

    def get_additional_metrics(self):
        if self._additional_metrics is None:
            # 'target' - the target after processing used for model training
            # 'prediction' - out of folds predictions of the model
            oof_predictions = self.get_out_of_folds()
            prediction_cols = [c for c in oof_predictions.columns if "prediction" in c]
            target_cols = [c for c in oof_predictions.columns if "target" in c]

            target = oof_predictions[target_cols]

            oof_preds = None
            if self._ml_task == MULTICLASS_CLASSIFICATION:
                oof_preds = self.preprocessings[0].prepare_target_labels(
                    oof_predictions[prediction_cols].values
                )

            else:
                oof_preds = oof_predictions[prediction_cols]

            self._additional_metrics = AdditionalMetrics.compute(
                target, oof_preds, self._ml_task
            )
            if self._ml_task == BINARY_CLASSIFICATION:
                self._threshold = float(self._additional_metrics["threshold"])
        return self._additional_metrics

    def save(self, model_path):
        start_time = time.time()
        logger.info(f"Save the model {model_path}")

        type_of_predictions = (
            "validation" if "k_folds" not in self.validation_params else "out_of_folds"
        )
        predictions_fname = os.path.join(
            model_path, f"predictions_{type_of_predictions}.csv"
        )
        predictions = self.get_out_of_folds()
        predictions.to_csv(predictions_fname, index=False)

        saved = []
        for i, l in enumerate(self.learners):
            p = os.path.join(model_path, f"learner_{i+1}.{l.file_extension()}")
            # l.save(p)
            saved += [p]

        with open(os.path.join(model_path, "framework.json"), "w") as fout:
            preprocessing = [p.to_json() for p in self.preprocessings]
            learners_params = [learner.get_params() for learner in self.learners]
            desc = {
                "uid": self.uid,
                "name": self._name,
                "preprocessing": preprocessing,
                "learners": learners_params,
                "params": self.params,
                "saved": saved,
                "predictions_fname": predictions_fname,
                "metric_name": self.get_metric_name(),
                "final_loss": self.get_final_loss(),
                "train_time": self.get_train_time(),
                "is_stacked": self._is_stacked,
            }
            if self._threshold is not None:
                desc["threshold"] = self._threshold
            fout.write(json.dumps(desc, indent=4))

        LearningCurves.plot(
            self.validation.get_n_splits(),
            self.get_metric_name(),
            model_path,
            trees_in_iteration=self.additional_params.get("trees_in_step"),
        )

        self._additional_metrics = self.get_additional_metrics()

        AdditionalMetrics.save(
            self._additional_metrics, self._ml_task, self.model_markdown(), model_path
        )

        with open(os.path.join(model_path, "status.txt"), "w") as fout:
            fout.write("ALL OK!")
        # I'm adding save time to total train time
        # there is always save after the training
        self.train_time += time.time() - start_time

    def model_markdown(self):
        long_name = AlgorithmsRegistry.get_long_name(
            self._ml_task, self.learner_params["model_type"]
        )
        short_name = self.learner_params["model_type"]
        desc = f"# Summary of {self.get_name()}\n"
        if long_name == short_name:
            desc += f"\n## {short_name}\n"
        else:
            desc += f"\n## {long_name} ({short_name})\n"
        for k, v in self.learner_params.items():
            if k in ["model_type", "ml_task", "seed"]:
                continue
            desc += f"- **{k}**: {v}\n"
        desc += "\n## Validation\n"
        for k, v in self.validation_params.items():
            if "path" not in k:
                desc += f" - **{k}**: {v}\n"
        desc += "\n## Optimized metric\n"
        desc += f"{self.get_metric_name()}\n"
        desc += "\n## Training time\n"
        desc += f"\n{np.round(self.train_time,1)} seconds\n"
        return desc

    @staticmethod
    def load(model_path):
        logger.info(f"Loading model framework from {model_path}")

        json_desc = json.load(open(os.path.join(model_path, "framework.json")))
        mf = ModelFramework(json_desc["params"])
        mf.uid = json_desc.get("uid", mf.uid)
        mf._name = json_desc.get("name", mf._name)
        mf._threshold = json_desc.get("threshold")
        mf.train_time = json_desc.get("train_time", mf.train_time)
        mf.final_loss = json_desc.get("final_loss", mf.final_loss)
        mf.metric_name = json_desc.get("metric_name", mf.metric_name)
        mf._is_stacked = json_desc.get("is_stacked", mf._is_stacked)
        predictions_fname = json_desc.get("predictions_fname")
        if predictions_fname is not None:
            mf.oof_predictions = pd.read_csv(predictions_fname)

        mf.learners = []
        for learner_desc, learner_path in zip(
            json_desc.get("learners"), json_desc.get("saved")
        ):

            l = AlgorithmFactory.load(learner_desc, learner_path)
            mf.learners += [l]

        mf.preprocessings = []
        for p in json_desc.get("preprocessing"):
            ps = Preprocessing()
            ps.from_json(p)
            mf.preprocessings += [ps]

        return mf
