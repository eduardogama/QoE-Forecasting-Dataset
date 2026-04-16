#!/usr/bin/python
"""
First, modify the /etc/hosts file and add the following lines:

10.0.1.50       steering
10.0.1.51       frontend
10.0.1.51       mn.cloud-1
10.0.1.1        mn.edge1
10.0.1.2        mn.edge2
10.0.1.3        mn.edge3

The script creates a network topology with the following components:
- 9 Base Stations
- 3 Edge Server
- N User Stations

The script also starts the following services:
- Edge Server
- Container Monitor
"""
import logging
from pyvirtualdisplay import Display

import numpy as np

import yaml
import random
import argparse
import time
import math
import os

from mininet.node import Controller, OVSKernelSwitch, Host
from mininet.log import setLogLevel, info
from mininet.link import TCLink

from containernet.cli import CLI
from containernet.net import Containernet
from containernet.node import DockerSta
from containernet.term import makeTerm
from mn_wifi.link import wmediumd
from mn_wifi.wmediumdConnector import interference
from mn_wifi.node import OVSKernelAP, UserAP

from yaml.loader import SafeLoader
from typing import Dict, Union

import sys
sys.path.append('./services/steering/source/monitors')

from handover_monitor import HandoverMonitor
from node_monitor import NodeMonitor

CPU_SHARES = 20
CPU_QUOTA = 100000

display = Display()
display.start()

def create_parser():
    arg_parser = argparse.ArgumentParser(description="Simulation")

    arg_parser.add_argument("--seed", type=int, default=0)
    arg_parser.add_argument("--users", type=int, default=1)
    arg_parser.add_argument("--abr", type=str, default="abrDynamic")
    arg_parser.add_argument("--scenario_config", type=str, default="scenario_config.yml")

    return arg_parser


def validate_args(arguments: Dict[str, Union[int, str, None]]) -> bool:
    raise NotImplemented("Function not implementesd yet")


def main():

    parser = create_parser()
    args = parser.parse_args()

    bts = []
    svs = []

    os.makedirs(f'logs/{args.seed}', exist_ok = True)

    """Create a network."""
    net = Containernet(link=wmediumd,
                       wmediumd_mode=interference,
                       ipBase='10.0.0.0/16',
                       ac_method='ssf')

    c0 = net.addController(name='c0',
                           controller=Controller,
                           protocol='tcp',
                           port=6653)

    kwargs = {'mode': 'g', 'failMode': 'standalone', 'channel': '1'}
    base_stations = [
        {'name': 'e1', 'position': '400.0,400.0,0.0', 'ssid': 'bs1'}, 
        {'name': 'e2', 'position': '1000.0,400.0,0.0', 'ssid': 'bs2'}, 
        {'name': 'e3', 'position': '1600.0,400.0,0.0', 'ssid': 'bs3'}, 
        {'name': 'e4', 'position': '400.0,1050.0,0.0', 'ssid': 'bs4'},
        {'name': 'e5', 'position': '1000.0,1050.0,0.0', 'ssid': 'bs5'}, 
        {'name': 'e6', 'position': '1600.0,1050.0,0.0', 'ssid': 'bs6'}, 
        {'name': 'e7', 'position': '400.0,1700.0,0.0', 'ssid': 'bs7'}, 
        {'name': 'e8', 'position': '1000.0,1700.0,0.0', 'ssid': 'bs8'}, 
        {'name': 'e9', 'position': '1600.0,1700.0,0.0', 'ssid': 'bs9'}
    ]

    bts.extend([
        net.addAccessPoint(
            cls=OVSKernelAP, 
            **{**bt, **kwargs}
        ) for bt in base_stations 
    ])

    positions = [
        f'{random.randint(50,2000)},{random.randint(50,2000)},0' 
        for _ in range(args.users)
    ]

    users = [{
        'name': 'sta%d' % i,
        'mac' : '00:00:00:00:00:%02d' % i,
        'ip'  : '10.0.0.%d/16' % i,
        'position': pos
    } for i, pos in enumerate(positions, 1)]
    
    for user in users:
        net.addStation(**user) 

    servers = [
        {
            'name': 'edge1', 
            'position': '400.0,1050.0,0.0', 
            'mac': '00:00:00:00:10:01', 
            'ip': '10.0.1.1/16'
        },
        {
            'name': 'edge2', 
            'position': '400.0,1050.0,0.0', 
            'mac': '00:00:00:00:10:02', 
            'ip': '10.0.1.2/16'
        },
        {
            'name': 'edge3', 
            'position': '700.0,1350.0,0.0', 
            'mac': '00:00:00:00:10:03', 
            'ip': '10.0.1.3/16'
        }
    ]

    svs.extend([
        net.addDocker(
            **edge, 
            dimage="dind",
            dcmd="dockerd-entrypoint.sh",
            volumes=["/home/eduardo/workspace/drl-css/edge:/home"],
            privileged=True
        ) for edge in servers
    ])

    steering = net.addHost('steering', cls=Host, ip='10.0.1.50/16')
    cloudcdn = net.addDocker(
        name="cloud-1", 
        mac='00:00:00:01:00:01',
        dimage="cloud/apache",
        ip='10.0.1.51/16',
        volumes=[
             '/home/eduardo/workspace/drl-css/cloud/cdn:/usr/local/apache2/htdocs/'
        ]
    )

    root = net.addSwitch(f'sw-r1', cls=OVSKernelSwitch)
    sw1 = net.addSwitch(f'sw-e1', cls=OVSKernelSwitch)
    sw2 = net.addSwitch(f'sw-e2', cls=OVSKernelSwitch)
    sw3 = net.addSwitch(f'sw-e3', cls=OVSKernelSwitch)

    net.setPropagationModel(model="logDistance", exp=2.5, sL=5)

    net.configureWifiNodes()

    # s2s1 = {'delay':'5ms', 'bw': 175}
    s2s1 = {'delay':'5ms'}
    net.addLink(root, sw1, cls=TCLink, **s2s1)
    net.addLink(root, sw2, cls=TCLink, **s2s1)
    net.addLink(root, sw3, cls=TCLink, **s2s1)

    delay = {'delay':'15ms'}
    net.addLink(root, cloudcdn, **delay)
    net.addLink(root, steering)

    net.addLink(sw1, svs[0])
    net.addLink(sw2, svs[1])
    net.addLink(sw3, svs[2])

    for i in range(0, 3):
        net.addLink(sw1, bts[i])

    for i in range(3, 6):
        net.addLink(sw2, bts[i])

    for i in range(6, 9):
        net.addLink(sw3, bts[i])

    # net.plotGraph(max_x=2200, max_y=2200)

    net.build()
    net.addNAT(name='nat0', linkTo='sw-r1', ip='10.0.0.100').configDefault()

    c0.start()
    root.start([ c0 ])
    sw1.start([ c0 ])
    sw2.start([ c0 ])
    sw3.start([ c0 ])
    for bt in bts: bt.start([ c0 ])

    for st in net.stations:
        st.cmd(f'ip route add default via 10.0.0.100')

    cloudcdn.cmd('apachectl -D FOREGROUND &')

    makeTerm(
        steering, 
        cmd=f"python services/steering/source/app.py --seed={args.seed}"
    )

    for sv in svs:
        # sv.cmd("docker build -t my-apache-server -f Dockerfile.apache .")
        # sv.cmd("docker run -d -p 80:80 --name apache-container my-apache-server")
        print(f"Starting service on {sv.name}")
        sv.cmd(
            "docker load -i edge_apache.tar"
        )

        sv.cmd(
            "docker run -d -p 80:80 --name edge edge/apache"
        )

    mon = HandoverMonitor(net.stations)
    mon.start()

    # nod = NodeMonitor()
    # nod.start()

    info( '*** Starting network\n')
    CLI(net)

    info("*** Stopping network\n")

    # planner.stop()
    mon.stop()
    # nod.stop()

    # planner.join()
    mon.join()
    # nod.join()

    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    main()

display.stop()
