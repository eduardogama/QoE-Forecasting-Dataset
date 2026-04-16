import numpy as np
import pandas as pd
import sqlite3
import json

from sklearn.preprocessing import MinMaxScaler
import tensorflow as tf

from tensorflow.keras import Input, Sequential
from tensorflow.keras.layers import Embedding, Dense, LSTM
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.losses import MeanSquaredError, MeanAbsolutePercentageError



class Journal:
    def __init__(self):
        self.seeds = 21
        self.users = [2, 3, 4, 5, 6]

    def load_dataset_csv(self):
        dfs = []
        path = '/home/Results/logs/logs-cloud-only-10min'
        for s in range(1, self.seeds+1):
            for i in self.users:
                df = pd.read_csv(f'{path}-{s}/{i}/node_stats.csv')
                dfs.append(df)

        return pd.concat(dfs)
    
    def store_dataset_in_csv(self):
        db_path = f'/home/Results/logs/logs-cloud-only-10min'
        for s in range(1, self.seeds+1):
            for i in self.users:
                print(f'{db_path}-{s}/{i}/node_stats.db')
                conn = sqlite3.connect(
                    f'{db_path}-{s}/{i}/node_stats.db', 
                    check_same_thread=False
                )

                query = f"SELECT * FROM nodeMonitor"
                datas = conn.execute(query).fetchall()

                self.flatten_json_and_store(
                    datas,
                    f'{db_path}-{s}/{i}/node_stats.csv'
                )
                
        return datas
    
    def flatten_json_and_store(self, datas, csv_file_path):
        final = pd.DataFrame()

        # Iterate over the list of JSON data
        for data in datas:

            # Convert the JSON string to a Python dictionary
            data_dict = json.loads(data[1])

            # print(data_dict[])
            if data_dict['read'] == '0001-01-01T00:00:00Z':
                continue

            # Flatten the JSON object
            df = pd.json_normalize(data_dict)

            # List to store all flattened DataFrames
            dfs = [df]
            
            # Flatten the nested dictionaries
            for column in df.columns:
                # Check if the column contains null values
                if df[column].isnull().any():
                    continue

                if isinstance(df[column][0], dict):
                    nested_df = pd.json_normalize(df[column])
                    nested_df.columns = [f"{column}_{subcolumn}" for subcolumn in nested_df.columns]
                    dfs.append(nested_df)

                # Check if the column contains an array of dictionaries
                elif isinstance(df[column][0], list) and all(isinstance(item, dict) for item in df[column][0]):
                    for i, item in enumerate(df[column][0]):
                        nested_df = pd.json_normalize(item)
                        nested_df.columns = [f"{column}_{i}_{subcolumn}" for subcolumn in nested_df.columns]
                        dfs.append(nested_df)

            # Concatenate all DataFrames in the list
            df = pd.concat(dfs, axis=1)
            
            df['read'] = pd.to_datetime(df['read']).dt.tz_convert('UTC').dt.tz_convert('America/Sao_Paulo')
            
            final = pd.concat([final, df], ignore_index=True)

        # remove column
        final = final.drop(columns=['blkio_stats.io_service_bytes_recursive'])
        
        # If the file does not exist, write the header
        final.to_csv(csv_file_path, mode='w', index=False)

journal = Journal()

def LSTM_1(rnn_units):
    return tf.keras.layers.LSTM(
        rnn_units,
        return_sequences=True,
        stateful=True,
    )


### Defining the RNN Model ###
def build_model(x):
    model = Sequential([
        LSTM(32, input_shape=x.shape[1:]),
        Dense(units=1),
    ])

    return model


def df_windowning(df_x, df_y, window_size, future_step):
    X = []
    y = []
    for i in range(len(df_x)-window_size-future_step):
        row = [r for r in df_x[i:i+window_size]]
        label = df_y[i+window_size+future_step]
        
        X.append(row)
        y.append(label)

    return np.array(X), np.array(y)

def load_dataset_csv():
    users = [2, 3, 4, 5, 6]
    dfs = []
    seeds = 21
    path = '/home/Results/logs/logs-cloud-only-10min'
    for s in range(1, seeds+1):
        for i in users:
            df = pd.read_csv(f'{path}-{s}/{i}/node_stats.csv')
            dfs.append(df)

    return pd.concat(dfs)

def store_dataset():
    journal.store_dataset_in_csv()

def load_model():
    df = load_dataset_csv()
    
    df = df.apply(pd.to_numeric, errors='coerce')

    kept = []
    throw = []

    null_counts = pd.Series([df[c].isnull().sum() for c in df.columns])

    for i,c in enumerate(df.columns):
        impute = float(null_counts[i])/len(df[c])
        
        if impute <= 0.30:
            if impute != 0.0:
                kept.append(c)
        else:
            throw.append(c)


    df = df.drop(throw, axis = 1)    
    df = df[df['qoe'] != 0.0]
    
    df.fillna(0.0, inplace=True)
    
    # Count the number of unique values in each column
    unique_counts = df.nunique()

    # Get the column names with only one unique value
    single_value_columns = unique_counts[unique_counts == 1].index

    # Remove the columns with only one unique value
    df = df.drop(single_value_columns, axis=1)

    size = len(df) * 0.7

    df_train = df[:int(size)]
    df_test = df[int(size):]

    X_tr = df_train.values
    y_tr = df_train["qoe"].values

    X_te = df_test.values
    y_te = df_test["qoe"].values
    
    scaler = MinMaxScaler(feature_range=(-1,1))

    df_train_sc = scaler.fit_transform(X_tr)
    df_test_sc = scaler.transform(X_te)
    df_train_sc.shape
    
    X_train, y_train = df_windowning(df_train_sc, y_tr, 10, 14)
    X_test, y_test = df_windowning(df_test_sc,y_te, 10, 14)

    X_train.shape, y_train.shape, X_test.shape, y_test.shape
    
    model = build_model(X_train)

    model.compile(loss=MeanSquaredError(), optimizer=Adam(learning_rate=0.005), metrics=[MeanAbsolutePercentageError()])
    
    loss_history = model.fit(X_train, y_train, validation_data=(X_test, y_test), epochs=10, batch_size=1024)
    
    return model, scaler