import datetime
import json
import os
import csv
import sys
import argparse
import randomname
import subprocess

import requests
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.service import Service


"""
A simple selenium test example written by python
"""        
class WaitLoad:

    def __init__(self, args):
        self.args = [args.btrmax, args.video, args.abr]
        self.url = f"http://{args.url_monitor}"
        self.name = args.user

        self.keys = [
            'timestamp',
            'time', 
            'duration', 
            'thr', 
            'quality', 
            'qoe',
            'cumulativeQoE',
            'repIndex', 
            'repBitrate', 
            'segId', 
            'buffer', 
            'stalls',
            'endpoint',
            'bitratemax', 
            'video', 
            'abrStrategy'
        ]

    def __call__(self, driver):
        try:
            cond = execute_script(
                driver, 
                "player.getBufferLength() + player.time() >= player.duration()"
            )
            user = execute_script(driver, "usersqoe")
            
        except Exception as e:
            print(f"Error executing script: {e}")
            cond = False
        
        if user:
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Merging keys with the data_array
            data_dict = dict(zip(self.keys, [timestamp] + user + self.args))
            
            # Convert the dictionary to a JSON string
            json_data = json.dumps(data_dict)
            print({
                'player_name': self.name,
                'metrics': {
                    'time': data_dict["time"],
                    'qoe': data_dict["qoe"],
                    'thr': data_dict["thr"],
                    'video': data_dict["video"],
                    'repIndex': data_dict["repIndex"],
                    'repBitrate': data_dict["repBitrate"],
                    'segId': data_dict["segId"],
                    'endpoint': data_dict["endpoint"]
                }
            })
            
            if data_dict["time"] >= 20:
                try:
                    requests.post(self.url, json={
                        'player_name': self.name,
                        'metrics': {
                            'time': data_dict["time"],
                            'qoe': data_dict["qoe"],
                            'thr': data_dict["thr"],
                            'video': data_dict["video"],
                            'stalls': data_dict["stalls"],
                            'endpoint': data_dict["endpoint"]
                        }
                    })
                except requests.exceptions.RequestException as e:
                    print(f"Error sending data to the server: {e}")
            else:
                print("Not sending status to the server")
                
        return cond if type(cond) == bool else False


def execute_script(driver, variable):
    return driver.execute_script(
        f"""
        try {{
            return window.{variable};
        }} catch (e) {{
            throw new Error(e.message);
        }}
        """
    )


def create_parser():
    arg_parser = argparse.ArgumentParser(description="*** Running end-user player")

    arg_parser.add_argument("--seed", type=int, default=0)
    arg_parser.add_argument("--video", type=int, default=1)
    arg_parser.add_argument("--abr", type=str, default="abrDynamic")
    arg_parser.add_argument("--user", type=str, default=randomname.get_name())
    arg_parser.add_argument("--btrmax", type=int, default=12000)
    arg_parser.add_argument("--url", type=str, default="frontend/player/edge-cloud.html")
    arg_parser.add_argument("--url_monitor", type=str, default="10.0.1.50:30500/receive_data")

    return arg_parser


def main():
    parser = create_parser()
    args = parser.parse_args()

    seed = args.seed
    user = args.user
    abr = args.abr
    video = args.video
    btrmax = args.btrmax
    url = args.url

    """Start web driver"""
    chrome_options =  Options()

    chrome_options.add_argument('--verbose')
    chrome_options.add_argument('--no-sandbox')
    # chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--incognito')
    chrome_options.add_argument('--no-user-gesture-required')
    chrome_options.add_argument('--disk-cache-dir=/dev/null')


    chrome_local_state_prefs = {
        "browser.enabled_labs_experiments": [
            "block-insecure-private-network-requests@2"
        ]
    }

    chrome_options.add_experimental_option("localState", chrome_local_state_prefs)

    print(f"Watching {args.user} Video Streaming")
    driver = None

    current_dir = os.path.dirname(os.path.abspath(__file__))
    chromedriver_path = os.path.join(current_dir, 'chromedriver')

    while True:
        try:
            driver = webdriver.Chrome(service=Service(chromedriver_path), options=chrome_options)
            
            driver.get(
                f'http://{url}?abr={abr}&video={video}&btrmax={btrmax}'  # 17000 is the 4K resolution
            )

            print("Waiting for the video to finish")
            WebDriverWait(driver, 400, 2).until(WaitLoad(args))
            break  # if successful, break the loop

        except WebDriverException:
            print("Exception triggered, Chrome closed unexpectedly, restarting...")
            driver.quit()
            driver = webdriver.Chrome(options=chrome_options)

    """Stop web driver"""
    driver.get_screenshot_as_file(f'logs/{seed}/{user}-screenshot.png')

    driver.close()
    driver.quit()
    

if __name__ == '__main__':
    main()
