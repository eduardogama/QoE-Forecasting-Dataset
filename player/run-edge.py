import datetime
import os
import csv
import sys
import argparse
import randomname
import subprocess

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.service import Service


def get_running_wireless_interface():
    result = subprocess.run(['ip', 'link', 'show'], stdout=subprocess.PIPE, text=True)
    output = result.stdout.split('\n')

    for line in output:
        if 'wlan0' in line:  # This indicates a running interface
            interface = line.split(':')[1].strip()
            return interface

    return None

def collect_iw_output(interface):
    command = ['iw', 'dev', interface, 'station', 'dump']
    result = subprocess.run(command, stdout=subprocess.PIPE, text=True)

    output = result.stdout.split('\n')
    
    # Parse the output and extract the metrics, values, and units
    metrics = []
    values = []
    units = []
    for line in output:
        if line: 
            parts = line.split(':', 1)
            if len(parts) == 2:
                metrics.append(parts[0].strip())
                value_unit = parts[1].strip().split(' ', 1)
                values.append(value_unit[0])
                if len(value_unit) > 1:
                    units.append(value_unit[1])
                else:
                    units.append('')

    return metrics, values, units

def save_to_csv(values, filename):
    with open(filename, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(values)  # Write the values as the next row


"""
A simple selenium test example written by python
"""        
class WaitLoad:

    def __init__(self, args, interface):
        self.args = [args.bitratemax, args.video, args.abr]
        self.interface = interface
        self.filename = f'logs/{args.seed}/{args.user}-iw.csv'


    def __call__(self, driver):

        try:
            p = execute_script(driver, "player.time()+0.1 >= player.duration()")
            u = execute_script(driver, "usersqoe")
            
        except Exception as e:
            print(f"Error executing script: {e}")
            p = False
        
        _, values, _ = collect_iw_output(self.interface)

        if u:
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            save_to_csv( [timestamp] + u + self.args + values, self.filename)

            print([timestamp] + u + self.args + values)

        return p if type(p) == bool else False
    

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
    arg_parser.add_argument("--bitratemax", type=int, default=17000)
    
    return arg_parser


def main():
    parser = create_parser()
    args = parser.parse_args()

    seed = args.seed
    user = args.user
    abr = args.abr
    video = args.video

    interface = get_running_wireless_interface()

    # os.makedirs(f'logs/{seed}/{user}', exist_ok = True)


    """Start web driver"""
    chrome_options =  Options()
    
    chrome_options.add_argument('--verbose')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--disable-gpu')
    # chrome_options.add_argument('--enable-logging')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-infobars')
    chrome_options.add_argument('--disable-notifications')
    chrome_options.add_argument('--disable-popup-blocking')
    chrome_options.add_argument('--disable-background-networking')
    chrome_options.add_argument('--disable-component-extensions-with-background-pages')
    chrome_options.add_argument('--disable-default-apps')
    chrome_options.add_argument('--disable-hang-monitor')
    chrome_options.add_argument('--disable-prompt-on-repost')
    chrome_options.add_argument('--disable-sync')
    chrome_options.add_argument('--disable-web-resources')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--allow-running-insecure-content')
    chrome_options.add_argument('--disable-client-side-phishing-detection')
    chrome_options.add_argument('--disable-component-update')
    chrome_options.add_argument('--disable-default-apps')
    chrome_options.add_argument('--disable-domain-reliability') 
    chrome_options.add_argument('--no-user-gesture-required')
    # chrome_options.add_argument(f'--user-data-dir=logs/{seed}/{user}')
    chrome_options.add_argument('--disk-cache-dir=/dev/null')

    chrome_local_state_prefs = {
        "browser.enabled_labs_experiments": [
            "block-insecure-private-network-requests@2"
        ],
    }

    chrome_options.add_experimental_option("localState", chrome_local_state_prefs)

    metrics = [ 
        'Station 02', 
        'inactive time', 
        'rx bytes', 
        'rx packets', 
        'tx bytes', 
        'tx packets', 
        'tx retries', 
        'tx failed', 
        'beacon loss', 
        'beacon rx', 
        'rx drop misc', 
        'signal', 
        'signal avg', 
        'beacon signal avg', 
        'tx bitrate', 
        'tx duration', 
        'rx bitrate', 
        'rx duration', 
        'expected throughput', 
        'authorized', 
        'authenticated', 
        'associated', 
        'preamble', 
        'WMM/WME', 
        'MFP', 
        'TDLS peer', 
        'DTIM period', 
        'beacon interval', 
        'short slot time', 
        'connected time', 
        'associated at [boottime]', 
        'associated at', 
        'current time'
    ]
    
    units = [
        '(on sta1-wlan0)', 'ms', '', '', '', '', '', '', '', '', '', 
        'dBm', 'dBm', 'dBm', 'MBit/s', 'us', 'MBit/s', 'us', '', '', 
        '', '', '', '', '', '', '', '', '', 'seconds', '', 'ms', 'ms'
    ]

    #write the header from csv file
    with open(f'logs/{seed}/{user}-iw.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        header = [
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
            'bitratemax', 
            'video', 
            'abrStrategy'
        ] + [f'{metric} ({unit})' for metric, unit in zip(metrics, units)]
        writer.writerow(header)

    print(f"Watching {args.user} Video Streaming")
    driver = None

    current_dir = os.path.dirname(os.path.abspath(__file__))
    chromedriver_path = os.path.join(current_dir, 'chromedriver')

    while True:
        try:
            driver = webdriver.Chrome(service=Service(chromedriver_path), options=chrome_options)
            
            driver.get(
                f'http://10.0.1.53:30001/player/vod-client-{video}.html?abr={abr}&btrmax={args.bitratemax}'  # 17000 is the 4K resolution
            )

            print("Waiting for the video to finish")
            WebDriverWait(driver, 400, 2).until(WaitLoad(args, interface))
            break  # if successful, break the loop

        except WebDriverException:
            print("Exception triggered, Chrome closed unexpectedly, restarting...")
            driver.quit()
            driver = webdriver.Chrome(options=chrome_options)


    """Stop web driver"""
    driver.get_screenshot_as_file(f'logs/{seed}/{user}-screenshot.png')
        
    driver.close()
    driver.quit()
    
    # client.disconnect()

if __name__ == '__main__':
    main()
