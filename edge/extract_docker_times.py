import re
import csv

# Function to extract real times from a log file
def extract_real_times(log_file):
    real_times = []
    with open(log_file, 'r') as file:
        for line in file:
            match = re.search(r'real\s+(\d+m\d+\.\d+s)', line)
            if match:
                real_times.append(match.group(1))
    return real_times

# Convert time format from '0m1.831s' to seconds
def convert_to_seconds(time_str):
    minutes, seconds = time_str.split('m')
    seconds = seconds.replace('s', '')
    return int(minutes) * 60 + float(seconds)

# Extract real times from log files
pull_times = extract_real_times('docker_pull_times.log')
deploy_times = extract_real_times('docker_deploy_times.log')

print("Pull times:", pull_times)
print("Deploy times:", deploy_times)

# Convert times to seconds
pull_times_seconds = [convert_to_seconds(time) for time in pull_times]
deploy_times_seconds = [convert_to_seconds(time) for time in deploy_times]

# Write to CSV file
with open('docker_times.csv', 'w', newline='') as csvfile:
    fieldnames = ['Pull Time (s)', 'Deploy Time (s)']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()
    for pull_time, deploy_time in zip(pull_times_seconds, deploy_times_seconds):
        writer.writerow({'Pull Time (s)': pull_time, 'Deploy Time (s)': deploy_time})

print("Docker times have been written to docker_times.csv")