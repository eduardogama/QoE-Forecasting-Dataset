import threading
import requests
import logging
import time

import numpy as np

from time import sleep
from mininet.log import info, error



class NetworkMonitor:
    def __init__(self):
        self.previous_rx_bytes = {}
        self.previous_tx_bytes = {}
        self.previous_time = {}

    def get_network_usage(self, interfaces):
        total_rx_bytes = 0
        total_tx_bytes = 0
        with open('/proc/net/dev', 'r') as f:
            for line in f:
                for intf in interfaces:
                    if intf in line:
                        data = line.split('%s:' % intf)[1].split()
                        rx_bytes, tx_bytes = (int(data[0]), int(data[8]))
                        total_rx_bytes += rx_bytes
                        total_tx_bytes += tx_bytes
        return total_rx_bytes, total_tx_bytes

    def get_network_speed(self, interfaces):
        current_time = time.time()
        rx_bytes, tx_bytes = self.get_network_usage(interfaces)
        interfaces_key = tuple(interfaces)  # Convert list to tuple for dictionary key

        if interfaces_key not in self.previous_rx_bytes:
            self.previous_rx_bytes[interfaces_key] = rx_bytes
            self.previous_tx_bytes[interfaces_key] = tx_bytes
            self.previous_time[interfaces_key] = current_time
            return 0, 0

        time_diff = current_time - self.previous_time[interfaces_key]
        rx_speed = (rx_bytes - self.previous_rx_bytes[interfaces_key]) / time_diff
        tx_speed = (tx_bytes - self.previous_tx_bytes[interfaces_key]) / time_diff

        self.previous_rx_bytes[interfaces_key] = rx_bytes
        self.previous_tx_bytes[interfaces_key] = tx_bytes
        self.previous_time[interfaces_key] = current_time

        return rx_speed, tx_speed

class HandoverMonitor(threading.Thread):
    def __init__(
        self, 
        stas, 
        url='http://steering:30500/receive_data', 
        seed=0, 
        round=200
    ) -> None:
        super().__init__()

        self.url = url
        self.stas = stas
        self.seed = seed
        self.round = round
        self.exit_event = threading.Event()

    def run(self):
        prev_ap = np.array([ None for i in enumerate(self.stas) ])
            
            
        edge1 = [f'e{i}-wlan1' for i in range(1, 4)]
        edge2 = [f'e{i}-wlan1' for i in range(4, 7)]
        edge3 = [f'e{i}-wlan1' for i in range(7, 10)]
        
        monitor = NetworkMonitor()
        
        while not self.exit_event.is_set():
            for i, sta in enumerate(self.stas):
                if sta.wintfs[0].ssid == prev_ap[i]:
                    continue
                
                user_data = {
                    "handover_name": sta.wintfs[0].ssid,
                    "metrics": {
                        "userName": sta.name,
                        "bsName": sta.wintfs[0].ssid,
                        "ip": sta.wintfs[0].ip,
                        "rssi": sta.wintfs[0].rssi
                    }
                }

                try:
                    res = requests.post(self.url, json=user_data)
                    info(f'*** {res.status_code}, {user_data}\n')
                    if res.status_code == 200:
                        prev_ap[i] = sta.wintfs[0].ssid
                except requests.exceptions.RequestException as e:
                    error(f"Request failed: Failed to establish a new connection")
            
            rx_speed_1, tx_speed_1 = monitor.get_network_speed(edge1)
            # print(f'Edge1 -> RX: {rx_speed_1:.2f} bytes/s, TX: {tx_speed_1:.2f} bytes/s')
            
            rx_speed_2, tx_speed_2 = monitor.get_network_speed(edge2)
            # print(f'Edge2 -> RX: {rx_speed_2:.2f} bytes/s, TX: {tx_speed_2:.2f} bytes/s')
            
            rx_speed_3, tx_speed_3 = monitor.get_network_speed(edge3)
            # print(f'Edge3 -> RX: {rx_speed_3:.2f} bytes/s, TX: {tx_speed_3:.2f} bytes/s')
            
            net_data = {
                "network_name": "mn",
                "metrics": {
                    "mn.edge1": {
                        "rx": rx_speed_1,
                        "tx": tx_speed_1
                    },
                    "mn.edge2": {
                        "rx": rx_speed_2,
                        "tx": tx_speed_2
                    },
                    "mn.edge3": {
                        "rx": rx_speed_3,
                        "tx": tx_speed_3
                    }
                }
            }
            
            try:
                res = requests.post(self.url, json=net_data)
                info(f'*** {res.status_code}, {net_data}\n')
            except requests.exceptions.RequestException as e:
                error(f"Request failed: Failed to establish a new connection")

            sleep(4)
            
        info("Exiting handover monitor\n")

    def stop(self):
        self.exit_event.set()