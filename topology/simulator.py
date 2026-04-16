import logging
import os
import random
import signal
import time
import subprocess

import numpy as np
import pexpect


class Simulator:

    def __init__(self, arr_rate, users, seed, child, total_videos=10, alpha=2.0):
        self.arr_rate = arr_rate
        self.users = users
        self.seed = seed
        self.total_videos = total_videos
        self.alpha = alpha
        self.total_time = 10

        self.arrivals = self.poisson_per_time(self.total_time, self.arr_rate)
        self.videos_requests = self.zipf(self.total_videos, len(self.arrivals), self.alpha)
        
        self.available_stations = [f'sta{i}' for i in range(1, self.users + 1)]
        self.occupied_stations = []
        self.idx = 1

        self.child = child
        self.prompt = 'containernet>'


    def poisson_per_time(self, total_time, rate_per_minute):
        lam = rate_per_minute / 60

        # Calculate the total number of events
        total_events = int(total_time * rate_per_minute)

        # Generate inter-event times
        inter_event_times = np.random.exponential(1/lam, total_events)

        return inter_event_times


    def zipf(self, total_videos, samples, alpha):
        zipf_dist = [1.0 / (i ** alpha) for i in range(1, total_videos + 1)]
        zipf_dist = [x / sum(zipf_dist) for x in zipf_dist]

        indices = np.random.choice(total_videos, samples, p=zipf_dist)
        data = np.random.permutation(np.arange(1, total_videos + 1))

        elements = [data[i] for i in indices]

        return elements


    def check_occupied_stations(self):
        for station in self.occupied_stations:
            sta, pid = station

            if not self.is_process_alive(pid):                
                print(f'User {sta} finished watching video')
                self.set_random_position(station)
                self.occupied_stations.remove(station)
                self.available_stations.append(sta)


    def set_random_position(self, station):
        self.child.sendline(
            f"py {station}.setPosition('{random.randint(50,2000)},{random.randint(50,2000)},0')"
        )
        self.child.expect([pexpect.EOF, self.prompt])


    def wait_for_available_stations(self, video_id):
        count = 0
        waiting = True
        while waiting:
            for i, (station, pid) in enumerate(self.occupied_stations):
                
                if self.is_process_alive(pid) and count < 20:
                    print(f'User {station} with {pid} is still watching video (2)')
                else:
                    print(f'User {station} finished watching video (2)')
                    self.set_random_position(station)
                    time.sleep(10)

                    print(f'User {station} is now watching video {video_id} (2)')
                    new_pid = self.start_chrome(station, video_id)
                    
                    self.occupied_stations[i] = (station, new_pid)
                    waiting = False
                    
                    break
            
            count += 1
            if waiting: time.sleep(4)


    def is_process_alive(self, pid):
        try:
            with open(f'/proc/{pid}/status') as f:
                lines = f.readlines()
        except FileNotFoundError:
            return False

        state_line = lines[1]
        state = state_line.split(':')[1].strip().split(' ')[0]

        if state == 'Z':
            return False

        return True

    def start_chrome(self, station, video_id):
        cmd = ' '.join([
            f'google-chrome', 
            f'http://frontend/player/index.html?video={video_id}',
            f'--incognito',
            f'--no-sandbox',
            f'--headless=new',
            f'--disable-dev-shm-usage',
            f'--no-user-gesture-required',
            f'--disable-gpu',
            f'--disable-cache',
            f'--aggressive-cache-discard',
            f'--disk-cache-size=0',
            f'--new-window',
#            f'--enable-logging',
#            f'--user-data-dir=logs/{self.seed}/sta{self.idx}'
        ])

        self.child.sendline(f'x {station} {cmd}')
        self.child.expect(self.prompt)

        pid = -1
        while True:
            try:
                pid = int(subprocess.check_output(
                    f"pgrep -f 'google-chrome.*frontend/player/index.html\?video={video_id}'",
                    shell=True
                ).decode().strip().split()[0])
                if pid:
                    break
            except subprocess.CalledProcessError:
                logging.error('Waiting for Chrome to start')

            time.sleep(4)

        self.idx += 1
        
        logging.info(f'User sta{self.idx} PID:', pid)
        return pid

    def start_video(self, station, video_id):
        python_cmd = ' '.join([
            f'python player/run.py',
            f'--seed={self.seed}',
            f'--user=sta{self.idx}',
            f'--video={video_id}',
            f'--url=frontend:30001/player/edge-cloud.html',
            f'--url_monitor=frontend:30500/receive_data'
        ])

        self.child.sendline(f'x {station} {python_cmd}')
        self.child.expect(self.prompt)
        
        pid = int(subprocess.check_output(
            f'pgrep -f \'{python_cmd}\'', 
            shell=True
        ).decode().split()[0])
        
        self.idx += 1
        
        return pid

    def is_process_alive_xterm(self, pid):
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        else:
            return True

    def run(self):
        for i, arrival in enumerate(self.arrivals):
            logging.info(f'Arrival {i} at {arrival} seconds')
            
            vid = self.videos_requests.pop(0)

            if self.available_stations:
                sta = self.available_stations.pop(0)
                pid = self.start_chrome(sta, vid)

                self.occupied_stations.append((sta, pid))
            else:
                self.wait_for_available_stations(vid)

            if len(self.available_stations) < 10:
                self.check_occupied_stations()

            time.sleep(arrival)

        count = 0
        while self.occupied_stations and count < 30:
        
            for station, pid in self.occupied_stations:
                if self.is_process_alive(pid):
                    print( 
                        f'User {station} with PID {pid} is still watching video [{count}].'
                    )
                else:
                    self.occupied_stations.remove((station, pid))
                    print('Occupied stations [', count, ']:', self.occupied_stations)

            count += 1
            time.sleep(10)

        print('Simulation finished')
