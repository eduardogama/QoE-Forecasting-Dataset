import randomname
import argparse
import logging

from flask import Flask
from flask import request
from flask import jsonify
from flask_cors import CORS, cross_origin

from dash_parser import DashParser
from selector import ContentAwareRoundRobinBalancer, RegionAware
from monitor import Monitor
# from planner import Planner


### DEFINES
ADDR = '10.0.1.50'
PORT = 30500
BASE_URI = f'http://steering:{PORT}'


def create_parser():
    arg_parser = argparse.ArgumentParser(description="*** Running end-user player")
    arg_parser.add_argument("--seed", type=int, default=0)
    
    return arg_parser

class Main:
    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app)

        @self.app.route('/steering/<name>', methods=['GET'])
        @cross_origin()
        def do_remote_steering(name):
            logging.info(f"Received request from {request.remote_addr} for {name}")

            tar = request.args.get('_DASH_pathway', default='', type=str)
            thr = request.args.get('_DASH_throughput', default=0.0, type=float)
            uid = request.args.get('_DASH_uid', default=randomname.get_name(), type=str)
            vid = request.args.get('_DASH_video', default='', type=str)

            kwargs = {
                'uid': uid,
                'vid': vid,
                'adr': request.remote_addr,
            }

            # logging.info(nodes)
            # logging.info(kwargs)
            
            nodes = selector.solve(**kwargs)
            
            # logging.info(nodes)
            
            data = parser.build(
                target  = tar,
                nodes   = nodes,
                uri     = BASE_URI,
                request = request
            )

#            logging.info(data)
            return jsonify(data), 200

        @self.app.route('/receive_data', methods=['POST'])
        def receive_data():            
            monitor.insert_data(request.json)
            return "Data received", 200
        
        @self.app.route('/update_node', methods=['POST'])
        def update_node():
            print(request.json)
            monitor.update_node(request.json)
            return "Node added", 200
        
        @self.app.route('/network_metrics', methods=['GET'])
        def get_network_metrics():
            n = request.args.get('n', default=10, type=int)
            metrics = monitor.get_last_n_network_rows(n)

            # print(metrics)
            
            return jsonify(metrics), 200
        
        
    def run(self):
        self.app.run(host='0.0.0.0', port=PORT, debug=True)
# END CLASS.


# Create instances of the parsers and the container monitor
main     = None
parser   = None
monitor  = None
selector = None
planner  = None

# MAIN
if __name__ == '__main__':
    parser = create_parser()
    args = parser.parse_args()
    
    main     = Main()
    parser   = DashParser()
    monitor  = Monitor(f'logs/{args.seed}')
    selector = RegionAware(monitor)

    try:
        logging.info("Starting webserver...")
        main.run()

    finally:
        del main
# EOF
 