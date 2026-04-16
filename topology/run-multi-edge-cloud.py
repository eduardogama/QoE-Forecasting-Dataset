import os
import time
import pexpect
import argparse

from simulator import Simulator

from utils import poisson_per_time, zipf



prompt = 'containernet>'

def create_parser():
    arg_parser = argparse.ArgumentParser(description="Simulation")

    arg_parser.add_argument("--seed", type=int, default=0)
    arg_parser.add_argument("--users", type=int, default=1)
    arg_parser.add_argument("--abr", type=str, default="abrDynamic")
    arg_parser.add_argument("--scenario_config", type=str, default="scenario_config.yml")
    arg_parser.add_argument("--arr_rate", type=int, default=5)

    return arg_parser

def main():
    parser = create_parser()
    args = parser.parse_args()

    child = pexpect.spawn(f'python topology/multi-edge-cloud.py --users={args.users} --seed={args.seed}')
    
    while True:
        index = child.expect([pexpect.EOF, prompt], timeout=180)
        print(child.before.decode(), flush=True)
        
        time.sleep(5)
        if index == 1: break
        

    child.sendline(f'px from containernet.term import makeTerm')
    child.expect([pexpect.EOF, prompt])
    print(child.before.decode(), flush=True)
    print('Importing MakeTerm', flush=True)

    sim = Simulator(args.arr_rate, args.users, args.seed, child)
    sim.run()

    child.close()
    
    os.system('mn -c')
    os.system('pkill xterm')
    os.system('pkill python')

if __name__ == '__main__':
    main()
