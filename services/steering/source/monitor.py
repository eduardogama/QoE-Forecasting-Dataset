import json
import logging

from common.util import filtered_values
from common.sql_service import Sqlite3PlayerMonitor, Sqlite3ContainerMonitor, Sqlite3NetworkMonitor, Sqlite3NodeMonitor, Sqlite3HandoverMonitor

logging.basicConfig(level=logging.INFO)


class Monitor():
    def __init__(self, path='.'):        
        self.player_db = Sqlite3PlayerMonitor(f'{path}/player_stats.db')
        self.player_db.connect()
        self.player_db.create_table()

        self.container_db = Sqlite3ContainerMonitor(f'{path}/container_stats.db')
        self.container_db.connect()
        self.container_db.create_table()

        self.node_db = Sqlite3NodeMonitor(f'{path}/node_stats.db')
        self.node_db.connect()
        self.node_db.create_table()
        
        self.hand_db = Sqlite3HandoverMonitor(f'{path}/handover_stats.db')
        self.hand_db.connect()
        self.hand_db.create_table()
        
        self.net_db = Sqlite3NetworkMonitor(f'{path}/network_stats.db')
        self.net_db.connect()
        self.net_db.create_table()

        self.cumulative_qoe = {}
        self.containers = {}
        self.players = []
        self.handover = {}
        
        with open('./topology/5G/mapping.json', 'r') as f:
            data = json.load(f)

            self.mappings = data['mappings']
            self.nodes    = data['nodes']


    def insert_data(self, data):
        logging.info(f"Inserting data {data.keys()}")
        
        if 'player_name' in data:
            self.insert_player(data)
        elif 'node_name' in data:
            self.insert_node(data)
        elif 'container_name' in data:
            self.insert_container(data)
        elif 'handover_name' in data:
            self.insert_handover(data)
        elif 'network_name' in data:
            self.insert_network(data)
        else:
            logging.error("Data does not have a valid key")


    def insert_player(self, data):
        metrics = data['metrics']
        self.player_db.insert_player_metrics(data['player_name'], metrics)
        
        #logging.info(f"Player {data['player_name']}: {metrics}")

        node_name = metrics['endpoint'] if metrics['endpoint'] != '' else 'mn.cloud-1'
        player_qoe = metrics['qoe']
                
        if metrics['K'] > 4:
            if node_name not in self.cumulative_qoe:
                self.cumulative_qoe[node_name] = []
            # elif len(self.cumulative_qoe[node_name]) > 10:
            #     self.cumulative_qoe[node_name].pop(0)

            self.cumulative_qoe[node_name].append(player_qoe)    
            logging.info(f"[{node_name}] Cumulative QoE: {self.cumulative_qoe[node_name]}")

    def insert_node(self, data):
        endpoint = data['node_name']
        metrics = data['metrics']
        
        if endpoint not in self.cumulative_qoe:
            metrics['qoe'] = 0.0
        else:
            metrics['qoe'] = sum(self.cumulative_qoe[endpoint]) / len(self.cumulative_qoe[endpoint])
            metrics['load'] = len(self.cumulative_qoe[endpoint])
            
            del self.cumulative_qoe[endpoint]

        self.node_db.insert_node_metrics(endpoint, metrics)

    def insert_container(self, data):
        self.containers = data['video_containers']

    def insert_handover(self, data):
        player = data['metrics']['ip']
        bstation = data['metrics']['bsName']
        
        self.handover[player] = bstation
        
        self.hand_db.insert_handover_metrics(player, data['metrics'])
        logging.info(f"Handover for {player} to {bstation}")
        
    def insert_network(self, data):
        self.net_db.insert_network_metrics(data['network_name'], data['metrics'])
        logging.info(f"Network metrics: {data['metrics']}")

    def get_nodes(self):
        return [ node for node in self.nodes ]

    def get_available_nodes(self):
        return [ node for node in self.nodes if self.nodes[node] == 'UP' ]
        
    def get_container_from_node(self, node):
        return self.node_db.get_last_n_rows(node, 1)
    
    def locate_region_server(self, player):
        data = json.loads(self.hand_db.get_last_n_rows(player, 1)[0][1])
        bs = data['bsName']
                
        print(f"Locating region server for {player} at {bs}")
        print(f"Mapping: {self.get_mapping(bs)}")

        return self.get_mapping(bs)


    def get_mapping(self, bs):
        for key, values in self.mappings.items():
            if bs in values:
                return key
        return 'mn.cloud-1'


    def get_last_n_network_rows(self, n):
        return self.net_db.get_last_n_rows('mn', n)
        
    def update_node(self, node):
        name = node['node_name']
        status = node['status']
        
        self.nodes[name] = status
        # print(f"Nodes: {self.nodes}")
# END CLASS.

# MAIN
if __name__ == '__main__':
    monitor = Monitor()
    
    bs = 'sw5'
    result = monitor.get_mapping(bs)
    print(result)  # Output: mn.edge2
    
    print(monitor.mappings)
    print(monitor.nodes)
# EOF
