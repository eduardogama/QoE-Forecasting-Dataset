import threading
import subprocess
import logging
import docker 
import time
import json 

import numpy as np
from mininet.log import info, error
import requests



class NodeMonitor(threading.Thread):
    def __init__(self, url='http://steering:30500/receive_data', interval=2) -> None:
        super().__init__()
        
        self.client = docker.from_env()
        self.url = url
        self.interval = interval
        self.container_stats = {}

        self.exit_event = threading.Event()

    def collect_container_stats(self, container_name, stats):
        cmd_prefix = \
            'docker exec ' + container_name + \
            ' docker stats --no-stream --format "{{json .}}"'
        out = subprocess.check_output(cmd_prefix, shell=True)

        if out:
            return json.loads(out.decode('utf-8'))['Container']

        return None

    def run(self):
        while not self.exit_event.is_set():
            for container in self.client.containers.list():
                if 'player' in container.name:
                    continue

                stats = container.stats(stream=False)
                # if 'edge' in container.name:
                #     stats['container'] = \
                #         self.collect_container_stats(container.name, stats)

                try:
                    print(f"Stats for {container.name} at {time.strftime('%H:%M:%S')}")
                    requests.post(self.url, json={
                        "node_name": container.name,
                        "metrics" : stats
                    })
                except requests.exceptions.RequestException as e:
                    print(f"Request failed: Failed to establish a new connection")
            time.sleep(self.interval)
            
        info("Exiting node monitor\n")

    def stop(self):
        self.exit_event.set()
        


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    monitor = NodeMonitor()
    monitor.start()
    monitor.join()
    monitor.stop()
    
    info("Exiting node monitor\n")