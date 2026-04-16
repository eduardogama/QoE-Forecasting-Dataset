import argparse
import logging
import subprocess
import threading
import docker
import time
import json

import requests


class ContainerMonitor:
    def __init__(self, url='10.0.1.50:30500/receive_data'):
        self.client = docker.from_env()
        self.container_stats = {}
        self.url = f"http://{url}"

    def collect_nodes_stats(self):
        for container in self.client.containers.list():
            if 'player' in container.name:
                continue

            logging.info(f"Collected stats for {container.name} at {time.strftime('%Y-%m-%d %H:%M:%S')}")

            stats = container.stats(stream=False)
            
            if 'edge' in container.name:
                stats['container'] = self.collect_container_stats(container.name, stats)

            self.send_data_to_remote_monitoring(container.name, msg={
                "node_name": container.name,
                "metrics" : stats
            })

    def collect_container_stats(self, container_name, stats):
        cmd_prefix = \
            'docker exec ' + container_name + ' docker stats --no-stream --format "{{json .}}"'
        out = subprocess.check_output(cmd_prefix, shell=True)

        if out:
            return json.loads(out.decode('utf-8'))['Container']

        return None

    def send_data_to_remote_monitoring(self, container_name, msg):
        logging.info(f"Inserting metrics for {container_name}")
        try:
            response = requests.post(self.url, json=msg)
            if response.status_code == 200:
                logging.info("Data sent successfully to remote database")
                return True
            else:
                logging.error("Failed to send data to remote database")
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: Failed to establish a new connection")

        return False
# END CLASS.

def create_parser():
    arg_parser = argparse.ArgumentParser(description="*** Running end-user player")
    arg_parser.add_argument("--url", type=str, default="10.0.1.50:30500/receive_data")
    arg_parser.add_argument("--interval", type=int, default=2)
    
    return arg_parser


if __name__ == '__main__':

    parser = create_parser()
    args = parser.parse_args()

    monitor = ContainerMonitor(url=args.url)
    interval = args.interval
    
    while True:
        monitor.collect_nodes_stats()
        time.sleep(interval)