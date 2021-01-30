import pandas as pd
df = pd.read_csv('cricket.csv')
import numpy as np
print(np.mean(df.Height_cm))
print(np.median(df.Height_cm))
from scipy import stats
print(stats.mode(df.Height_cm))
print(df.Height_cm.describe())
print(np.min(df.Height_cm))
print(np.max(df.Height_cm))
print(np.std(df.Height_cm))
print(np.var(df.Height_cm))
print(np.percentile(df.Height_cm, 25))
print(np.percentile(df.Height_cm, 50))
print(np.percentile(df.Height_cm, 75))
import matplotlib.pyplot as plt
x = df.Height_cm
y = df.Student_ID
plt.hist(x)
plt.show()
plt.scatter(y,x)
plt.show()
