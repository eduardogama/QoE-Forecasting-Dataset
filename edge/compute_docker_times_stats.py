import pandas as pd

# Read the CSV file
file_path = 'docker_times.csv'
df = pd.read_csv(file_path)

# Compute the average and standard deviation for Pull Time (s)
pull_time_mean = df['Pull Time (s)'].mean()
pull_time_std = df['Pull Time (s)'].std()

# Compute the average and standard deviation for Deploy Time (s)
deploy_time_mean = df['Deploy Time (s)'].mean()
deploy_time_std = df['Deploy Time (s)'].std()

# Print the results
print(f"Pull Time (s) - Mean: {pull_time_mean:.3f}, Standard Deviation: {pull_time_std:.3f}")
print(f"Deploy Time (s) - Mean: {deploy_time_mean:.3f}, Standard Deviation: {deploy_time_std:.3f}")