import pandas as pd
from supervised.automl import AutoML
from supervised.ensemble import Ensemble
import os

df = pd.read_csv(
    "https://raw.githubusercontent.com/pplonski/datasets-for-start/master/adult/data.csv",
    skipinitialspace=True,
)

X = df[df.columns[:-1]]
y = df["income"]

results_path = "AutoML_2"
automl = AutoML(
    results_path=results_path,
    total_time_limit=400,
    start_random_models=10,
    hill_climbing_steps=0,
    top_models_to_improve=0,
    train_ensemble=False,
)


models_map = {m.get_name(): m for m in automl._models}

ensemble = Ensemble("logloss", "binary_classification")
ensemble.models_map = models_map

oofs = {}
target = None
for i in range(1, 30):
    oof = pd.read_csv(
        os.path.join(results_path, f"model_{i}", "predictions_out_of_folds.csv")
    )
    prediction_cols = [c for c in oof.columns if "prediction" in c]
    oofs[f"model_{i}"] = oof[prediction_cols]
    if target is None:
        target_columns = [c for c in oof.columns if "target" in c]
        target = oof[target_columns]

ensemble.target = target
ensemble.target_columns = "target"
ensemble.fit(oofs, target)
ensemble.save(os.path.join(results_path, "ensemble"))


predictions = ensemble.predict(X)
print(predictions.head())

"""
    p_<=50K    p_>50K
0  0.982940  0.017060
1  0.722781  0.277219
2  0.972687  0.027313
3  0.903021  0.096979
4  0.591373  0.408627
"""


ensemble2 = Ensemble.load(os.path.join(results_path, "ensemble"), models_map)
predictions2 = ensemble2.predict(X)
print(predictions2.head())

"""
    p_<=50K    p_>50K
0  0.982940  0.017060
1  0.722781  0.277219
2  0.972687  0.027313
3  0.903021  0.096979
4  0.591373  0.408627
"""
