import argparse
import csv
import json
import logging
import random
import sqlite3
import time
from typing import Dict, Union
import numpy as np
import requests
import tensorflow as tf
from tensorflow.keras.losses import MeanAbsolutePercentageError # type: ignore

import sys
import joblib
import os

sys.path.append('./services/steering/source')
from common.sql_service import Sqlite3NodeMonitor # type: ignore

sys.path.append('./services/planner/')
from common.dataset_utils import filtered_values, filtered_values_1, filtered_values_2, filtered_values_3, filtered_values_cloud_all_datas_v2, filtered_values_cloud_all_datas_v3, filtered_values_cloud_all_datas_v4 # type: ignore


# Custom function to handle deserialization
def custom_objects():
    return {
        'MeanAbsolutePercentageError': MeanAbsolutePercentageError
    }

class Main:
    def __init__(
        self, 
        path='./logs/0', 
        scaler_path = './services/planner/models/lstm_scaler.sc', 
        model_path = './services/planner/models/lstm_model.h5',
        window_size = 6,
        features = 34,
        deploy_csv = './edge/docker_times.csv'
    ):
        self.model = tf.keras.models.load_model(
            model_path, 
            custom_objects=custom_objects()
        )
        self.scaler = joblib.load(scaler_path)

        self.nodefile = f'{path}/node_stats.db'

        self.features = features
        self.window_size = window_size
        self.slo_threshold = 3.0
        self.edge_nodes = {
            'mn.edge1': 'DOWN',
            'mn.edge2': 'DOWN',
            'mn.edge3': 'DOWN'
        }

        self.pull_times, self.deploy_times = self.read_times_from_csv(deploy_csv)
        

    def scaleContainerUp(self, node_name):
        print(f"Scale Up Response for {node_name}")

        response = requests.get(f'http://steering:30500/network_metrics')
        if response.status_code == 200:
            last_stats = response.json()

            metrics = {
                'mn.edge1': {},
                'mn.edge2': {},
                'mn.edge3': {}
            }

            for nm, stats in last_stats:
                stats_dict = json.loads(stats)
                
                for stat in stats_dict:

                    metrics[stat] = {}
                    
                    if 'rx' not in metrics[stat]:
                        metrics[stat]['rx'] = []
                        metrics[stat]['tx'] = []
                    
                    metrics[stat]['rx'].append(stats_dict[stat]['rx'])
                    metrics[stat]['tx'].append(stats_dict[stat]['tx'])
            
            mean_tx = {node: np.mean(metrics[node]['tx']) for node in metrics}
            mean_rx = {node: np.mean(metrics[node]['rx']) for node in metrics}

            down_nodes = {
                node: mean_tx[node] 
                for node in metrics if self.edge_nodes.get(node) == 'DOWN' and mean_rx[node] > 0
            }

            if down_nodes:
                chosen_node = max(down_nodes, key=down_nodes.get)

                new_node = {
                    'node_name': chosen_node,
                    'status': 'UP'
                }

                self.edge_nodes[chosen_node] = 'UP'

                timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                print(f"{timestamp} -> Scaling up {chosen_node}")
                
                self.deployment(chosen_node)
                return requests.post('http://steering:30500/update_node', json=new_node)
            else:
                print("No nodes are currently DOWN.")
                return None
        else:
            logging.error(f"Failed to get last stats for node {node_name}: {response.status_code}")
            return None

    def convert_to_values(self, tuples):
        return [ filtered_values_cloud_all_datas_v4(json.loads(stats)) for nm, stats in tuples ]

    def predictor(self, node):
        lastStats = self.db.get_last_n_rows(node, self.window_size)
        lastStats.reverse()
        
        vals = [json.loads(stats)['qoe'] for nm, stats in lastStats ]
        print(f"Values for {node}: {vals}")

        if len(vals) < self.window_size or any(v == 0 for v in vals):
            return 5.0
        
        train_values = self.convert_to_values(lastStats)
        
        return self.model.predict(
            self.scaler.transform(train_values).reshape(1, self.window_size, self.features)
        )
    
    def run(self):
        alpha = 0.5
        scale_up_delay = 0

        flag = True
        while flag:
            try:
                print("Connecting to the database...")
                
                self.db = Sqlite3NodeMonitor(self.nodefile)
                self.db.connect(timeout=5)
                flag = False
            except Exception as e:
                logging.error(f"Failed to connect to the database: {e}")
                time.sleep(5)
        
        while True:
            
            try:
                for node in ['mn.cloud-1']:
                    cloud = self.db.get_last_n_rows('mn.cloud-1', self.window_size)
                    
                    # qoe = sum(json.loads(stats)['qoe'] for nm, stats in cloud) / len(cloud)
                    qoe = self.predictor(node)
                    
                    timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())               
                    print(f"{timestamp} -> QoE Predictor for {node}: {qoe} | Status: UP")
                    
                    if len(cloud) < self.window_size or any(json.loads(stats)['qoe'] == 0.0 for nm, stats in cloud):
                        continue
                    
                    if qoe != 0.0 and qoe < self.slo_threshold:
                        if scale_up_delay == 0:
                            self.scaleContainerUp(node)
                        scale_up_delay = (scale_up_delay + 1) % 7

                for edge in self.edge_nodes:
                    if self.edge_nodes[edge] == 'DOWN':
                        continue

                    edgeStats = self.db.get_last_n_rows(edge, 1)
                    cloudStats = self.db.get_last_n_rows('mn.cloud-1', 1)

                    qoe_edge = json.loads(edgeStats[0][1])['qoe']
                    qoe_cloud = json.loads(cloudStats[0][1])['qoe']
                    
                    qoe_cloud = 5.0 if qoe_cloud == 0.0 else qoe_cloud
                    

                    if (qoe_edge + qoe_cloud)/2 >= self.slo_threshold + alpha:
                        timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                        print(f"{timestamp} -> Scaling down {edge}")
                        
                        self.edge_nodes[edge] = 'DOWN'
                        
                        new_node = {
                            'node_name': edge,
                            'status': 'DOWN'
                        }

                        requests.post('http://steering:30500/update_node', json=new_node)

            except KeyboardInterrupt as e:
                logging.error(f"KeyboardInterrupt: {e}")
            except sqlite3.OperationalError as e:
                logging.error(f"OperationalError: {e}")
            except Exception as e:
                logging.error(f"An error occurred: {e}")

            time.sleep(10)

    def read_times_from_csv(self, file_path):
        pull_times = []
        deploy_times = []
        with open(file_path, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                pull_times.append(float(row['Pull Time (s)']))
                deploy_times.append(float(row['Deploy Time (s)']))
        return pull_times, deploy_times

    def deployment(self, node):
        random_pull_time = random.choice(self.pull_times)
        random_deploy_time = random.choice(self.deploy_times)
        

        time.sleep(random_pull_time+random_deploy_time)
        # return random_pull_time, random_deploy_time


def create_parser():
    arg_parser = argparse.ArgumentParser(description="Simulation")

    arg_parser.add_argument("--seed", type=int, default=0)
    arg_parser.add_argument("--users", type=int, default=1)
    arg_parser.add_argument("--abr", type=str, default="abrDynamic")
    arg_parser.add_argument("--scenario_config", type=str, default="scenario_config.yml")

    return arg_parser


def validate_args(arguments: Dict[str, Union[int, str, None]]) -> bool:
    raise NotImplemented("Function not implementesd yet")

if __name__ == '__main__':
    parser = create_parser()
    args = parser.parse_args()

    
    print(f"Current working directory: {os.getcwd()}")
    main = Main(
        path = f'./logs/{args.seed}',
        # #### LSTM Model used in journal paper ####
        # scaler_path = './services/planner/lstm_scaler_1m.sc',
        # model_path = './services/planner/lstm_model_1m.h5',
        # #### RNN Model with 40 epochs and batch size of 512 ####
        # scaler_path = './services/planner/models/rnn_prediction_e40_b512.sc',
        # model_path = './services/planner/models/rnn_prediction_e40_b512.h5',
        # #### LSTM Model with 40 epochs and batch size of 512 ####
        # scaler_path = './services/planner/models/rnn_prediction_e40_b512.sc',
        # model_path = './services/planner/models/rnn_prediction_e40_b512.h5',
        # #### GRU Model with 40 epochs and batch size of 512 ####
        # scaler_path = './services/planner/models/gru_prediction_e40_b512.sc',
        # model_path = './services/planner/models/gru_prediction_e40_b512.h5',
        # #### Bi-GRU Model with 40 epochs and batch size of 64 ####
        scaler_path = './services/planner/models/bi-gru_prediction_relu_e40_b64_w6_T1.sc',
        model_path = './services/planner/models/bi-gru_prediction_relu_e40_b64_w6_T1.h5',
        window_size = 6,
        deploy_csv = './edge/docker_times.csv',
        features = 34
    )
    main.run()
