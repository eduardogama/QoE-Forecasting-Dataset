import datetime
import json
import csv
import os
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error

from monitors.sql_service import Sqlite3ContainerMonitor
from util import flatten_json_and_store, create_csv


# Create a CSV file with the merged data
create_csv()

# Calculate the Spearman correlation
df = pd.read_csv('logs-db/4/merged-result.csv')


a = [np.nan, None, [], {}, 'NaN', 'Null','NULL','None','NA','?','-', '.','', ' ', '   ']
nulldemo = pd.DataFrame(a)

for c in df.columns:
    string_null = np.array([x in a[2:] for x in df[c]])
    print(c, df[c].isnull().sum(), string_null.sum()) 

input()

df = df.drop('read', axis=1)
df = df.drop('preread', axis=1)
df = df.apply(pd.to_numeric, errors='coerce')


kept = []
throw = []

null_counts = pd.Series([df[c].isnull().sum() for c in df.columns])

for i,c in enumerate(df.columns):
    impute = float(null_counts[i])/len(df[c])

    if impute <= 0.5:
        if impute != 0.0:
            kept.append(c)
    else:
        throw.append(c)


features_to_impute = kept
features_to_throw = throw

print(df.info())
print("-------------")
print(len(features_to_impute), features_to_impute)
print("-------------")
print(len(features_to_throw), features_to_throw)
print("-------------")

df = df.drop(features_to_throw, axis = 1)


# remove the columns according to the above result, replace df with the new results
# also remove ID column as it's not a useful feature
print(df)
input()

print(df.corr(method='spearman'))


corr = df.corr()

# # Generate a mask for the upper triangle
mask = np.triu(np.ones_like(corr, dtype=bool))

# # Set up the matplotlib figure
f, ax = plt.subplots(figsize=(11, 9))

# # Generate a custom diverging colormap
cmap = sns.diverging_palette(230, 20, as_cmap=True)

# # Draw the heatmap with the mask and correct aspect ratio
sns.heatmap(corr, mask=mask, cmap=cmap, center=0, annot=True, fmt=".1f", square=True, linewidths=.5, cbar_kws={"shrink": .7})

plt.show()

# # Split the data into a training set and a test set
# X = data.drop('QoE', axis=1)
# y = data['QoE']
# X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# # Normalize the data
# scaler = StandardScaler()
# X_train = scaler.fit_transform(X_train)
# X_test = scaler.transform(X_test)

# # Choose a model
# model = LinearRegression()

# # Train the model
# model.fit(X_train, y_train)

# # Evaluate the model
# y_pred = model.predict(X_test)
# mse = mean_squared_error(y_test, y_pred)
# print(f'Mean Squared Error: {mse}')