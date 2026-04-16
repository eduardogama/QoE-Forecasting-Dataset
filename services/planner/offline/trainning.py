import argparse
import json
import sqlite3
import numpy as np
import pandas as pd
import tensorflow as tf
import matplotlib.pyplot as plt

import sys
import joblib

from sklearn.preprocessing import MinMaxScaler

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import SimpleRNN, LSTM
from tensorflow.keras.layers import Dense
from tensorflow.keras.losses import MeanSquaredError, MeanAbsolutePercentageError
from tensorflow.keras.optimizers import Adam
import os


sys.path.append('./services/planner/common')
from dataset_utils import plot_real_predict # type: ignore
from dataset_utils import flatten_json_and_store # type: ignore

sys.path.append('./services/steering/source')
from common.sql_service import Sqlite3NodeMonitor # type: ignore


class OfflinePhase():
    def __init__(
        self, 
        path='./', 
        scaler_path='./lstm_scaler.sc', 
        model_path='./lstm_model.h5',
        window=6,
        T=12,
        epochs=1000,
        batch_size=2048
    ):
        super().__init__()
        self.seeds = 10
        self.users = [2, 3, 4, 5, 6]

        self.window = window
        self.T = T

        self.X_test, self.y_test = None, None
        self.n_features = 0

        self.epochs=epochs
        self.batch_size=batch_size
        
    def load_model(self, df):
        self.model, self.scaler = self.train_model(df)

        return self.model, self.scaler
    
    def train_model(self, df):
        self.n_features = len(df.columns)

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

        X_train, y_train = self.df_windowning(df_train_sc, y_tr, self.window, self.T)
        X_test, y_test = self.df_windowning(df_test_sc,y_te, self.window, self.T)

        print(X_train.shape, y_train.shape, X_test.shape, y_test.shape)
        input()

        model = self.build_model(X_train)

        model.compile(
            loss=MeanSquaredError(), 
            optimizer=Adam(learning_rate=0.001), 
            metrics=[MeanAbsolutePercentageError()]
        )

        model.fit(
            X_train, 
            y_train, 
            validation_data=(X_test, y_test), 
            epochs=self.epochs,
            batch_size=self.batch_size
        )

        self.X_test = X_test
        self.y_test = y_test

        return model, scaler

    def build_model(self, x):
        return Sequential([
            LSTM(self.n_features, input_shape=x.shape[1:]),
            Dense(units=1),
            Dense(units=1),
            Dense(units=1)
        ])
    
    def df_windowning(self, df_x, df_y, window_size, future_step):
        X = []
        y = []
        for i in range(len(df_x)-window_size-future_step):
            row = [r for r in df_x[i:i+window_size]]
            label = df_y[i+window_size+future_step]
            
            X.append(row)
            y.append(label)

        return np.array(X), np.array(y)
    
    def store_dataset_in_csv(self, path):
        for s in range(1, self.seeds+1):
            for i in self.users:
                print(f'{path}-{s}/{i}/node_stats.db')
                conn = sqlite3.connect(
                    f'{path}-{s}/{i}/node_stats.db', 
                    check_same_thread=False
                )

                query = f"SELECT * FROM nodeMonitor"
                datas = conn.execute(query).fetchall()
                
                datas.sort(key=lambda x: (x[0], json.loads(x[1])['read']))

                flatten_json_and_store(
                    datas,
                    f'{path}-{s}/{i}/node_stats.csv'
                )

        return datas

    def load_multiple_csv(self, paths):
        dfs = []
    
        for s in range(1, self.seeds+1):
            for path in paths:
                for i in self.users:
                    print(f'{path}-{s}/{i}/node_stats.csv')
                    df = pd.read_csv(f'{path}-{s}/{i}/node_stats.csv')
                    dfs.append(df)

        return pd.concat(dfs)
    
    def filtered_values(self, df):
        df = df.apply(pd.to_numeric, errors='coerce')

        throw = []
        null_counts = pd.Series([df[c].isnull().sum() for c in df.columns])

        for i,c in enumerate(df.columns):
            impute = float(null_counts[i])/len(df[c])
            if impute > 0.3:
                throw.append(c)

        df = df.drop(throw, axis = 1)
        df = df[df['qoe'] != 0.0]
        
        df.fillna(0.0, inplace=True)
        
        if 'blkio_stats.io_service_bytes_recursive_0_value' in df.columns:
            df = df.drop('blkio_stats.io_service_bytes_recursive_0_value', axis=1)
            df = df.drop('blkio_stats.io_service_bytes_recursive_1_value', axis=1)
            df = df.drop('blkio_stats.io_service_bytes_recursive_0_major', axis=1)
            df = df.drop('blkio_stats.io_service_bytes_recursive_1_major', axis=1)
        
        df = df.drop('memory_stats.stats.file_writeback', axis=1) 
        df = df.drop('memory_stats.limit', axis=1)

        # Count the number of unique values in each column
        unique_counts = df.nunique()

        # Get the column names with only one unique value
        single_value_columns = unique_counts[unique_counts == 1].index

        # Remove the columns with only one unique value
        df = df.drop(single_value_columns, axis=1)

        return df

    def plot_real_predict(self, model): 
        plot_real_predict(
            model, 
            self.X_test, 
            self.y_test, 
            'plot_real_predict_multi_edge_cloud.png'
        )

def create_parser():
    arg_parser = argparse.ArgumentParser(description="*** Running end-user player")
    arg_parser.add_argument("--seed", type=int, default=0)

    return arg_parser

if __name__ == '__main__':

    parser = create_parser()
    args = parser.parse_args()

    scaler_file_name = f'services/planner/lstm_scaler_1m.sc'
    model_file_name = f'services/planner/lstm_model_1m.h5'
    offline = OfflinePhase(
        scaler_path = scaler_file_name, 
        model_path = model_file_name,
        window=6,
        T=12
    )

    # paths = [
    #     'logs_incomplete/logs-multi-edge-cloud-10min-40ms-30u-thr-k5-load-fixed-cache-ld25',
    #     'logs_incomplete/logs-multi-edge-cloud-10min-40ms-30u-thr-k5-load-plan-proactive-fixed-cache-ld25'
    # ]
    # for path in paths:
    #     offline.store_dataset_in_csv(path)

    paths = [
        'logs/logs-multi-edge-cloud-10min-20ms-30u-dyn-k5-load-plan-reactive-fixed-cache',
        'logs/2_logs-multi-edge-cloud-10min-20ms-dyn-k5-load-plan-proactive-fixed-cache-pe',
        'logs/logs-multi-edge-cloud-10min-20ms-bola',
        'logs/logs-multi-edge-cloud-10min-20ms-dyn',
        'logs/logs-multi-edge-cloud-10min-20ms-dyn-k5',
        'logs/logs-multi-edge-cloud-10min-20ms-dyn-k5-load',
        'logs/logs-multi-edge-cloud-10min-20ms-dyn-k5-load-plan',
        'logs/logs-multi-edge-cloud-10min-20ms-dyn-k5-load-plan-fixed-cache',
        'logs/logs-multi-edge-cloud-10min-20ms-thr',
        'logs/logs-multi-edge-cloud-10min-20ms-thr-k5',
        'logs/logs-multi-edge-cloud-10min-20ms-thr-k5-load-plan-fixed-cache',
        'logs/logs-multi-edge-cloud-10min-20ms-thr-k5-load-plan-proactive-fixed-cache-pe',
        'logs/logs-multi-edge-cloud-10min-20ms-bola-k5-load-fixed-cache-pe',
        'logs/logs-multi-edge-cloud-10min-20ms-bola-k5-load-plan-fixed-cache'
    ]

    df = offline.load_multiple_csv(paths)
    
    path = 'logs/logs-multi-edge-cloud-10min-20ms-30u-dyn-k5-load-plan-proactive-fixed-cache-pe'
    dfs = []
    for s in range(1, 7):
        for i in [2,3,4,5,6]:
            print(f'{path}-{s}/{i}/node_stats.csv')
            df_aux = pd.read_csv(f'{path}-{s}/{i}/node_stats.csv')
            dfs.append(df_aux)

    path = 'logs/logs-cloud-only-10min-20ms'
    dfs = []
    for s in range(1, 18):
        for i in [2,3,4,5,6]:
            print(f'{path}-{s}/{i}/node_stats.csv')
            df_aux = pd.read_csv(f'{path}-{s}/{i}/node_stats.csv')
            dfs.append(df_aux)
    
    path = 'logs/logs-cloud-only-10min-20ms-bola'
    for s in range(1, 11):
        for i in [2,3,4,5,6]:
            print(f'{path}-{s}/{i}/node_stats.csv')
            df_aux = pd.read_csv(f'{path}-{s}/{i}/node_stats.csv')
            dfs.append(df_aux)
    
    path = 'logs/logs-cloud-only-10min-20ms-thr'
    for s in range(1, 24):
        for i in [2,3,4,5,6]:
            print(f'{path}-{s}/{i}/node_stats.csv')
            df_aux = pd.read_csv(f'{path}-{s}/{i}/node_stats.csv')
            dfs.append(df_aux)
    
    path = 'logs_incomplete/logs-multi-edge-cloud-10min-40ms-30u-dyn-k5-load-plan-proactive'
    for s in range(1, 11):
        for i in [2,3,4,5,6]:
            print(f'{path}-{s}/{i}/node_stats.csv')
            df_aux = pd.read_csv(f'{path}-{s}/{i}/node_stats.csv')
            dfs.append(df_aux)
    
    path = 'logs_incomplete/logs-multi-edge-cloud-10min-40ms-30u-dyn-k5-load-plan-reactive'
    for s in range(1, 11):
        for i in [2,3,4,5,6]:
            print(f'{path}-{s}/{i}/node_stats.csv')
            df_aux = pd.read_csv(f'{path}-{s}/{i}/node_stats.csv')
            dfs.append(df_aux)
    
    path = 'logs_incomplete/logs-multi-edge-cloud-10min-40ms-30u-dyn-k5-load-fixed-cache-ld25'
    for s in range(1, 7):
        for i in [2,3,4,5,6]:
            print(f'{path}-{s}/{i}/node_stats.csv')
            df_aux = pd.read_csv(f'{path}-{s}/{i}/node_stats.csv')
            dfs.append(df_aux)
            
    path = 'logs_incomplete/logs-multi-edge-cloud-10min-40ms-30u-dyn-k5-load-plan-proactive-fixed-cache-ld25'
    for s in range(1, 6):
        for i in [2,3,4,5,6]:
            print(f'{path}-{s}/{i}/node_stats.csv')
            df_aux = pd.read_csv(f'{path}-{s}/{i}/node_stats.csv')
            dfs.append(df_aux)
            
    path = 'logs_incomplete/logs-multi-edge-cloud-10min-40ms-30u-thr-k5-load-fixed-cache-ld25'
    for s in range(1, 10):
        for i in [2,3,4,5,6]:
            print(f'{path}-{s}/{i}/node_stats.csv')
            df_aux = pd.read_csv(f'{path}-{s}/{i}/node_stats.csv')
            dfs.append(df_aux)

    path = 'logs/logs-multi-edge-cloud-10min-20ms-L2A'
    for s in range(1, 11):
        for i in [2,3,4,5,6]:
            print(f'{path}-{s}/{i}/node_stats.csv')
            df_aux = pd.read_csv(f'{path}-{s}/{i}/node_stats.csv')
            dfs.append(df_aux)

    path = 'logs/logs-multi-edge-cloud-10min-20ms-L2A-k5-load-plan-fixed-cache'
    for s in range(1, 11):
        for i in [2,3,4,5,6]:
            print(f'{path}-{s}/{i}/node_stats.csv')
            df_aux = pd.read_csv(f'{path}-{s}/{i}/node_stats.csv')
            dfs.append(df_aux)

    path = 'logs/logs-multi-edge-cloud-10min-20ms-LoLP'
    for s in range(1, 11):
        for i in [2,3,4,5,6]:
            print(f'{path}-{s}/{i}/node_stats.csv')
            df_aux = pd.read_csv(f'{path}-{s}/{i}/node_stats.csv')
            dfs.append(df_aux)

    path = 'logs/logs-multi-edge-cloud-10min-20ms-L2A-k5-load-plan-fixed-cache'
    for s in range(1, 11):
        for i in [2,3,4,5,6]:
            print(f'{path}-{s}/{i}/node_stats.csv')
            df_aux = pd.read_csv(f'{path}-{s}/{i}/node_stats.csv')
            dfs.append(df_aux)

    path = 'logs_incomplete/logs-multi-edge-cloud-10min-40ms-30u-thr-k5-load-plan-reactive-fixed-cache-ld25'
    for s in range(1, 6):
        for i in [2,3,4,5,6]:
            print(f'{path}-{s}/{i}/node_stats.csv')
            df_aux = pd.read_csv(f'{path}-{s}/{i}/node_stats.csv')
            dfs.append(df_aux)

    path = 'logs/logs-multi-edge-cloud-10min-20ms-LoLP-k5-load-plan-fixed-cache'
    for s in range(1, 6):
        for i in [2,3,4,5,6]:
            print(f'{path}-{s}/{i}/node_stats.csv')
            df_aux = pd.read_csv(f'{path}-{s}/{i}/node_stats.csv')
            dfs.append(df_aux)

        
    df = pd.concat([df] + dfs)
    

    df = offline.filtered_values(df)

    df.to_csv('services/planner/models/dataset.csv', index=False)

    model, scaler = offline.train_model(df)

    offline.plot_real_predict(model)


    # Save scaler and model
    joblib.dump(scaler, scaler_file_name)
    model.save(model_file_name, save_format='h5')