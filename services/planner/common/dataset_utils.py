import json
import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker


def flatten_json_and_store(datas, csv_file_path):
    final = pd.DataFrame()

    # Iterate over the list of JSON data
    for data in datas:

        # Convert the JSON string to a Python dictionary
        data_dict = json.loads(data[1])

        # print(data_dict[])
        if data_dict['read'] == '0001-01-01T00:00:00Z':
            continue

        # Flatten the JSON object
        df = pd.json_normalize(data_dict)

        # List to store all flattened DataFrames
        dfs = [df]

        # Flatten the nested dictionaries
        for column in df.columns:
            # Check if the column contains null values
            if df[column].isnull().any():
                continue

            if isinstance(df[column][0], dict):
                nested_df = pd.json_normalize(df[column])
                nested_df.columns = [f"{column}_{subcolumn}" for subcolumn in nested_df.columns]
                dfs.append(nested_df)

            # Check if the column contains an array of dictionaries
            elif isinstance(df[column][0], list) and all(isinstance(item, dict) for item in df[column][0]):
                for i, item in enumerate(df[column][0]):
                    nested_df = pd.json_normalize(item)
                    nested_df.columns = [f"{column}_{i}_{subcolumn}" for subcolumn in nested_df.columns]
                    dfs.append(nested_df)

        # Concatenate all DataFrames in the list
        df = pd.concat(dfs, axis=1)
        
        df['read'] = pd.to_datetime(df['read']).dt.tz_convert('UTC').dt.tz_convert('America/Sao_Paulo')
        
        final = pd.concat([final, df], ignore_index=True)

    # remove column
    # final = final.drop(columns=['blkio_stats.io_service_bytes_recursive'])
    
    # If the file does not exist, write the header
    final.to_csv(csv_file_path, mode='w', index=False)

def load_dataset():
    seeds = 20
    users = [2, 3, 4, 5, 6]
    dfs = []

    for s in range(1, seeds+1):
        path = f'/home/Results/logs/logs-cloud-10min-{s}'
        for i in users:
            df = pd.read_csv(f'{path}/{i}/aggregated_result.csv')
            dfs.append(df)
            
        path = f'/home/Results/logs/logs-edge-cloud-10min-{s}'
        for i in [2, 3]:
            df = pd.read_csv(f'{path}/{i}/aggregated_cloud_result.csv')
            dfs.append(df)

    return pd.concat(dfs)

def load_dataset_dionisio():
    seeds = 20
    users = [2, 3, 4]
    dfs = []

    for s in range(1, seeds+1):
        path = f'/home/Results/logs/logs-one-edge-10min-{s}'
        for i in users:
            df = pd.read_csv(f'{path}/{i}/node_stats.csv')
            dfs.append(df)

    return pd.concat(dfs)

def df_windowning(df_x, df_y, window_size, future_step):
    X = []
    y = []
    for i in range(len(df_x)-window_size-future_step):
        row = [r for r in df_x[i:i+window_size]]
        label = df_y[i+window_size+future_step]
        
        X.append(row)
        y.append(label)

    return np.array(X), np.array(y)

def plot_mape(history_model):
    plt.plot(history_model.history['mean_absolute_percentage_error'])
    plt.plot(history_model.history['val_mean_absolute_percentage_error'])
    plt.title('Model MAPE')
    plt.ylabel('MAPE')
    plt.xlabel('Epoch')
    plt.legend(['Train', 'Test'], loc='upper left')
    plt.show()

import matplotlib.pyplot as plt

def plot_real_predict_new(model, x_test, y_test, figure='plot_real_predict.png'):
    y_pred_test = model.predict(x_test)
    
    # Set up the figure size to match the provided style (wide and slim)
    plt.figure(figsize=(12, 3))
    
    # Adjust the plot style to match the example
    plt.plot(y_test, color='red', linestyle='-', linewidth=1, label='Actual')
    plt.plot(y_pred_test, color='blue', linestyle='-', linewidth=1, label='Predicted')
    
    # Remove title and add axis labels to match the given graph
    plt.xlabel('Time', fontsize=12)
    plt.ylabel('QoE', fontsize=12)
    
    # Set consistent y-limits if necessary (adjust or remove as per your actual data range)
    plt.ylim([0, 5]) # Example uses dynamic range based on the data

    # Customize legend to match the example style
    plt.legend(loc='upper right', fontsize=10)
    
    # Tight layout to remove extra margins
    plt.tight_layout()
    
    # Save the plot to a file
    plt.savefig(figure, dpi=300)
    
    # Show the plot
    plt.show()


def plot_real_predict(model, x_test, y_test, figure='plot_real_predict.png'):
    y_pred_test = model.predict(x_test)
    plt.figure(figsize=(10, 6))
    
    # Improved color scheme and line styles
    plt.plot(y_test, color='navy', linestyle='-', linewidth=2, label='Real (Test)')
    plt.plot(y_pred_test, color='darkorange', linestyle='--', linewidth=2, label='Predicted (Test)')
    
    # Title and labels with increased font sizes
    plt.title('Predicted and Real Values (Test)', fontsize=14)
    plt.xlabel('Time', fontsize=12)
    plt.ylabel('Value', fontsize=12)
    
    # Adding gridlines
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    
    # Improving the legend
    plt.legend(fontsize=12)
    
    plt.ylim([0, 5])
    
    # Setting the tick parameters
    plt.tick_params(axis='both', which='major', labelsize=10)
    plt.tick_params(axis='both', which='minor', labelsize=8)
    
    # Tight layout for better spacing
    plt.tight_layout()
    
    # Export the plot in high resolution for publication
    plt.savefig(figure, dpi=300)
    
    plt.show()
    
def plot_real_predict_enhanced(model, x_test, y_test):
    # Predicting the test dataset
    y_pred_test = model.predict(x_test)
    
    # Using a professional style
    plt.style.use('seaborn-darkgrid')
    
    # Creating the plot with optimized sizes
    plt.figure(figsize=(12, 7))
    
    # Plotting real and predicted values with confidence intervals (dummy values for illustration)
    confidence_interval = np.std(y_pred_test) / np.sqrt(len(y_pred_test))
    plt.fill_between(np.arange(len(y_test)), (y_pred_test - confidence_interval).flatten(), (y_pred_test + confidence_interval).flatten(), color='orange', alpha=0.2, label='Prediction Confidence Interval')
    plt.plot(y_test, 'o-', color='navy', markersize=5, label='Real (Test)', linewidth=2)
    plt.plot(y_pred_test, 's--', color='darkorange', markersize=5, label='Predicted (Test)', linewidth=2)
    
    # Enhancing title, labels, and legend
    plt.title('Comparison of Predicted and Real Values', fontsize=16, fontweight='bold')
    plt.xlabel('Time Steps', fontsize=14, fontweight='bold')
    plt.ylabel('Values', fontsize=14, fontweight='bold')
    plt.legend(fontsize=12, loc='best', fancybox=True, framealpha=0.5)
    
    # Annotating a key point (example)
    key_point = np.argmax(y_test)
    plt.annotate('Highest Real Value', xy=(key_point, y_test[key_point]), xytext=(key_point+10, y_test[key_point]+0.1),
                 arrowprops=dict(facecolor='black', shrink=0.05), fontsize=12)
    
    # Further improving gridlines and tick parameters
    plt.grid(True, which='major', linestyle='--', linewidth=0.5)
    plt.tick_params(axis='both', which='major', labelsize=12)
    plt.tick_params(axis='both', which='minor', labelsize=10)
    
    # Adjusting layout for better spacing and saving in high resolution
    plt.tight_layout()
    plt.savefig('enhanced_plot_real_vs_predicted.png', dpi=300)
    
    plt.show()
    
def filtered_data(stats):
    return {
        "cpu_stats.cpu_usage.total_usage": stats["cpu_stats"]["cpu_usage"]["total_usage"],
        "cpu_stats.cpu_usage.usage_in_kernelmode": stats["cpu_stats"]["cpu_usage"]["usage_in_kernelmode"],
        "cpu_stats.cpu_usage.usage_in_usermode": stats["cpu_stats"]["cpu_usage"]["usage_in_usermode"],
        "cpu_stats.system_cpu_usage": stats["cpu_stats"]["system_cpu_usage"],
        "precpu_stats.cpu_usage.total_usage": stats["precpu_stats"]["cpu_usage"]["total_usage"],
        "precpu_stats.cpu_usage.usage_in_kernelmode": stats["precpu_stats"]["cpu_usage"]["usage_in_kernelmode"],
        "precpu_stats.cpu_usage.usage_in_usermode": stats["precpu_stats"]["cpu_usage"]["usage_in_usermode"],
        "precpu_stats.system_cpu_usage": stats["precpu_stats"]["system_cpu_usage"],
        "memory_stats.usage": stats["memory_stats"]["usage"],
        "memory_stats.stats.active_anon": stats["memory_stats"]["stats"]["active_anon"],
        "memory_stats.stats.active_file": stats["memory_stats"]["stats"]["active_file"],
        "memory_stats.stats.anon": stats["memory_stats"]["stats"]["anon"],
        "memory_stats.stats.file": stats["memory_stats"]["stats"]["file"],
        "memory_stats.stats.file_dirty": stats["memory_stats"]["stats"]["file_dirty"],
        "memory_stats.stats.file_mapped": stats["memory_stats"]["stats"]["file_mapped"],
        "memory_stats.stats.inactive_anon": stats["memory_stats"]["stats"]["inactive_anon"],
        "memory_stats.stats.inactive_file": stats["memory_stats"]["stats"]["inactive_file"],
        "memory_stats.stats.kernel_stack": stats["memory_stats"]["stats"]["kernel_stack"],
        "memory_stats.stats.pgfault": stats["memory_stats"]["stats"]["pgfault"],
        "memory_stats.stats.pgmajfault": stats["memory_stats"]["stats"]["pgmajfault"],
        "memory_stats.stats.pgrefill": stats["memory_stats"]["stats"]["pgrefill"],
        "memory_stats.stats.pgscan": stats["memory_stats"]["stats"]["pgscan"],
        "memory_stats.stats.pgsteal": stats["memory_stats"]["stats"]["pgsteal"],
        "memory_stats.stats.slab": stats["memory_stats"]["stats"]["slab"],
        "memory_stats.stats.slab_reclaimable": stats["memory_stats"]["stats"]["slab_reclaimable"],
        "memory_stats.stats.slab_unreclaimable": stats["memory_stats"]["stats"]["slab_unreclaimable"],
        "memory_stats.stats.sock": stats["memory_stats"]["stats"]["sock"],
        "networks.eth0.rx_bytes": stats["networks"]["eth0"]["rx_bytes"],
        "networks.eth0.rx_packets": stats["networks"]["eth0"]["rx_packets"],
        "blkio_stats.io_service_bytes_recursive_0_value": stats["blkio_stats"]["io_service_bytes_recursive"][0]["value"],
    }

def filtered_values(stats):
    return [
        stats['qoe'],
        stats['pids_stats']['current'],
        stats['cpu_stats']['cpu_usage']['total_usage'],
        stats['cpu_stats']['cpu_usage']['usage_in_kernelmode'],
        stats['cpu_stats']['cpu_usage']['usage_in_usermode'],
        stats['cpu_stats']['system_cpu_usage'],
        stats['precpu_stats']['cpu_usage']['total_usage'],
        stats['precpu_stats']['cpu_usage']['usage_in_kernelmode'],
        stats['precpu_stats']['cpu_usage']['usage_in_usermode'],
        stats['precpu_stats']['system_cpu_usage'],
        stats['memory_stats']['usage'],
        stats['memory_stats']['stats']['active_anon'],
        stats['memory_stats']['stats']['active_file'],
        stats['memory_stats']['stats']['anon'],
        stats['memory_stats']['stats']['file'],
        stats['memory_stats']['stats']['file_dirty'],
        stats['memory_stats']['stats']['file_mapped'],
        stats['memory_stats']['stats']['inactive_anon'],
        stats['memory_stats']['stats']['inactive_file'],
        stats['memory_stats']['stats']['kernel_stack'],
        stats['memory_stats']['stats']['pgactivate'],
        stats['memory_stats']['stats']['pgfault'],
        stats['memory_stats']['stats']['pgmajfault'],
        stats['memory_stats']['stats']['pgrefill'],
        stats['memory_stats']['stats']['pgscan'],
        stats['memory_stats']['stats']['pgsteal'],
        stats['memory_stats']['stats']['slab'],
        stats['memory_stats']['stats']['slab_reclaimable'],
        stats['memory_stats']['stats']['slab_unreclaimable'],
        stats['memory_stats']['stats']['sock'],
        stats['memory_stats']['stats']['workingset_nodereclaim'],
        stats['networks']['eth0']['rx_bytes'],
        stats['networks']['eth0']['rx_packets'],
    ]

def filtered_values_1(stats):
    return [
        stats['qoe'],
        stats['pids_stats']['current'],
        stats['cpu_stats']['cpu_usage']['total_usage'],
        stats['cpu_stats']['cpu_usage']['usage_in_kernelmode'],
        stats['cpu_stats']['cpu_usage']['usage_in_usermode'],
        stats['cpu_stats']['system_cpu_usage'],
        stats['precpu_stats']['cpu_usage']['total_usage'],
        stats['precpu_stats']['cpu_usage']['usage_in_kernelmode'],
        stats['precpu_stats']['cpu_usage']['usage_in_usermode'],
        stats['precpu_stats']['system_cpu_usage'],
        stats['memory_stats']['usage'],
        stats['memory_stats']['stats']['active_anon'],
        stats['memory_stats']['stats']['active_file'],
        stats['memory_stats']['stats']['anon'],
        stats['memory_stats']['stats']['file'],
        stats['memory_stats']['stats']['file_dirty'],
        stats['memory_stats']['stats']['file_mapped'],
        stats['memory_stats']['stats']['file_writeback'],
        stats['memory_stats']['stats']['inactive_anon'],
        stats['memory_stats']['stats']['inactive_file'],
        stats['memory_stats']['stats']['kernel_stack'],
        stats['memory_stats']['stats']['pgactivate'],
        stats['memory_stats']['stats']['pgfault'],
        stats['memory_stats']['stats']['pgmajfault'],
        stats['memory_stats']['stats']['pgrefill'],
        stats['memory_stats']['stats']['pgscan'],
        stats['memory_stats']['stats']['pgsteal'],
        stats['memory_stats']['stats']['slab'],
        stats['memory_stats']['stats']['slab_reclaimable'],
        stats['memory_stats']['stats']['slab_unreclaimable'],
        stats['memory_stats']['stats']['sock'],
        stats['memory_stats']['stats']['workingset_nodereclaim'],
        stats['memory_stats']['limit'],
        stats['networks']['eth0']['rx_bytes'],
        stats['networks']['eth0']['rx_packets'],
        # stats['blkio_stats']['io_service_bytes_recursive'][0]['value'],
        # stats['blkio_stats']['io_service_bytes_recursive'][1]['value']
    ]

def filtered_values_2(stats):
    return [
        stats['qoe'],
        stats['pids_stats']['current'],
        stats['cpu_stats']['cpu_usage']['total_usage'],
        stats['cpu_stats']['cpu_usage']['usage_in_kernelmode'],
        stats['cpu_stats']['cpu_usage']['usage_in_usermode'],
        stats['cpu_stats']['system_cpu_usage'],
        stats['precpu_stats']['cpu_usage']['total_usage'],
        stats['precpu_stats']['cpu_usage']['usage_in_kernelmode'],
        stats['precpu_stats']['cpu_usage']['usage_in_usermode'],
        stats['precpu_stats']['system_cpu_usage'],
        stats['memory_stats']['usage'],
        stats['memory_stats']['stats']['active_anon'],
        stats['memory_stats']['stats']['active_file'],
        stats['memory_stats']['stats']['anon'],
        stats['memory_stats']['stats']['file'],
        stats['memory_stats']['stats']['file_dirty'],
        stats['memory_stats']['stats']['file_mapped'],
        stats['memory_stats']['stats']['inactive_anon'],
        stats['memory_stats']['stats']['inactive_file'],
        stats['memory_stats']['stats']['kernel_stack'],
        stats['memory_stats']['stats']['pgactivate'],
        stats['memory_stats']['stats']['pgfault'],
        stats['memory_stats']['stats']['pgmajfault'],
        stats['memory_stats']['stats']['pgrefill'],
        stats['memory_stats']['stats']['pgscan'],
        stats['memory_stats']['stats']['pgsteal'],
        stats['memory_stats']['stats']['shmem'],
        stats['memory_stats']['stats']['slab'],
        stats['memory_stats']['stats']['slab_reclaimable'],
        stats['memory_stats']['stats']['slab_unreclaimable'],
        stats['memory_stats']['stats']['sock'],
        # stats['memory_stats']['stats']['workingset_nodereclaim'],
        stats['networks']['eth0']['rx_bytes'],
        stats['networks']['eth0']['rx_packets']
    ]
    
    

def filtered_values_3(stats):
    def filtered_values_3(stats):
        return [
            stats['read'],
            stats['preread'],
            stats['num_procs'],
            stats['name'],
            stats['id'],
            stats['qoe'],
            stats['pids_stats']['current'],
            stats['pids_stats']['limit'],
            stats['blkio_stats']['io_serviced_recursive'],
            stats['blkio_stats']['io_queue_recursive'],
            stats['blkio_stats']['io_service_time_recursive'],
            stats['blkio_stats']['io_wait_time_recursive'],
            stats['blkio_stats']['io_merged_recursive'],
            stats['blkio_stats']['io_time_recursive'],
            stats['blkio_stats']['sectors_recursive'],
            stats['cpu_stats']['cpu_usage']['total_usage'],
            stats['cpu_stats']['cpu_usage']['usage_in_kernelmode'],
            stats['cpu_stats']['cpu_usage']['usage_in_usermode'],
            stats['cpu_stats']['system_cpu_usage'],
            stats['cpu_stats']['online_cpus'],
            stats['cpu_stats']['throttling_data']['periods'],
            stats['cpu_stats']['throttling_data']['throttled_periods'],
            stats['cpu_stats']['throttling_data']['throttled_time'],
            stats['precpu_stats']['cpu_usage']['total_usage'],
            stats['precpu_stats']['cpu_usage']['usage_in_kernelmode'],
            stats['precpu_stats']['cpu_usage']['usage_in_usermode'],
            stats['precpu_stats']['system_cpu_usage'],
            stats['precpu_stats']['online_cpus'],
            stats['precpu_stats']['throttling_data']['periods'],
            stats['precpu_stats']['throttling_data']['throttled_periods'],
            stats['precpu_stats']['throttling_data']['throttled_time'],
            stats['memory_stats']['usage'],
            stats['memory_stats']['stats']['active_anon'],
            stats['memory_stats']['stats']['active_file'],
            stats['memory_stats']['stats']['anon'],
            stats['memory_stats']['stats']['anon_thp'],
            stats['memory_stats']['stats']['file'],
            stats['memory_stats']['stats']['file_dirty'],
            stats['memory_stats']['stats']['file_mapped'],
            stats['memory_stats']['stats']['file_writeback'],
            stats['memory_stats']['stats']['inactive_anon'],
            stats['memory_stats']['stats']['inactive_file'],
            stats['memory_stats']['stats']['kernel_stack'],
            stats['memory_stats']['stats']['pgactivate'],
            stats['memory_stats']['stats']['pgdeactivate'],
            stats['memory_stats']['stats']['pgfault'],
            stats['memory_stats']['stats']['pglazyfree'],
            stats['memory_stats']['stats']['pglazyfreed'],
            stats['memory_stats']['stats']['pgmajfault'],
            stats['memory_stats']['stats']['pgrefill'],
            stats['memory_stats']['stats']['pgscan'],
            stats['memory_stats']['stats']['pgsteal'],
            stats['memory_stats']['stats']['shmem'],
            stats['memory_stats']['stats']['slab'],
            stats['memory_stats']['stats']['slab_reclaimable'],
            stats['memory_stats']['stats']['slab_unreclaimable'],
            stats['memory_stats']['stats']['sock'],
            stats['memory_stats']['stats']['thp_collapse_alloc'],
            stats['memory_stats']['stats']['thp_fault_alloc'],
            stats['memory_stats']['stats']['unevictable'],
            stats['memory_stats']['stats']['workingset_activate'],
            stats['memory_stats']['stats']['workingset_nodereclaim'],
            stats['memory_stats']['stats']['workingset_refault'],
            stats['memory_stats']['limit'],
            stats['networks']['eth0']['rx_bytes'],
            stats['networks']['eth0']['rx_packets'],
            stats['networks']['eth0']['rx_errors'],
            stats['networks']['eth0']['rx_dropped'],
            stats['networks']['eth0']['tx_bytes'],
            stats['networks']['eth0']['tx_packets'],
            stats['networks']['eth0']['tx_errors'],
            stats['networks']['eth0']['tx_dropped'],
        ]

def filtered_values_4(stats):
    return [
        stats['qoe'],
        stats['pids_stats']['current'],
        stats['cpu_stats']['cpu_usage']['total_usage'],
        stats['cpu_stats']['cpu_usage']['usage_in_kernelmode'],
        stats['cpu_stats']['cpu_usage']['usage_in_usermode'],
        stats['cpu_stats']['system_cpu_usage'],
        stats['precpu_stats']['cpu_usage']['total_usage'],
        stats['precpu_stats']['cpu_usage']['usage_in_kernelmode'],
        stats['precpu_stats']['cpu_usage']['usage_in_usermode'],
        stats['precpu_stats']['system_cpu_usage'],
        stats['memory_stats']['usage'],
        stats['memory_stats']['stats']['active_anon'],
        stats['memory_stats']['stats']['active_file'],
        stats['memory_stats']['stats']['anon'],
        stats['memory_stats']['stats']['file'],
        stats['memory_stats']['stats']['file_dirty'],
        stats['memory_stats']['stats']['file_mapped'],
        stats['memory_stats']['stats']['inactive_anon'],
        stats['memory_stats']['stats']['inactive_file'],
        stats['memory_stats']['stats']['kernel_stack'],
        stats['memory_stats']['stats']['pgfault'],
        stats['memory_stats']['stats']['pgmajfault'],
        stats['memory_stats']['stats']['pgrefill'],
        stats['memory_stats']['stats']['pgscan'],
        stats['memory_stats']['stats']['pgsteal'],
        stats['memory_stats']['stats']['slab'],
        stats['memory_stats']['stats']['slab_reclaimable'],
        stats['memory_stats']['stats']['slab_unreclaimable'],
        stats['memory_stats']['stats']['sock'],
        stats['networks']['eth0']['rx_bytes'],
        stats['networks']['eth0']['rx_packets'],
    ]
    
def filtered_values_cloud_all_datas_v2(stats):
    return [
        stats['qoe'],
        stats['pids_stats']['current'],
        stats['cpu_stats']['cpu_usage']['total_usage'],
        stats['cpu_stats']['cpu_usage']['usage_in_kernelmode'],
        stats['cpu_stats']['cpu_usage']['usage_in_usermode'],
        stats['cpu_stats']['system_cpu_usage'],
        stats['precpu_stats']['cpu_usage']['total_usage'],
        stats['precpu_stats']['cpu_usage']['usage_in_kernelmode'],
        stats['precpu_stats']['cpu_usage']['usage_in_usermode'],
        stats['precpu_stats']['system_cpu_usage'],
        stats['memory_stats']['usage'],
        stats['memory_stats']['stats']['active_anon'],
        stats['memory_stats']['stats']['active_file'],
        stats['memory_stats']['stats']['anon'],
        stats['memory_stats']['stats']['file'],
        stats['memory_stats']['stats']['file_dirty'],
        stats['memory_stats']['stats']['file_mapped'],
        stats['memory_stats']['stats']['inactive_anon'],
        stats['memory_stats']['stats']['inactive_file'],
        stats['memory_stats']['stats']['kernel_stack'],
        stats['memory_stats']['stats']['pgactivate'],
        stats['memory_stats']['stats']['pgfault'],
        stats['memory_stats']['stats']['pgmajfault'],
        stats['memory_stats']['stats']['pgrefill'],
        stats['memory_stats']['stats']['pgscan'],
        stats['memory_stats']['stats']['pgsteal'],
        stats['memory_stats']['stats']['shmem'],
        stats['memory_stats']['stats']['slab'],
        stats['memory_stats']['stats']['slab_reclaimable'],
        stats['memory_stats']['stats']['slab_unreclaimable'],
        stats['memory_stats']['stats']['sock'],
        stats['networks']['eth0']['rx_bytes'],
        stats['networks']['eth0']['rx_packets']
    ]

def filtered_values_cloud_all_datas_v3(stats):
    return [
        stats['qoe'],
        stats['pids_stats']['current'],
        stats['cpu_stats']['cpu_usage']['total_usage'],
        stats['cpu_stats']['cpu_usage']['usage_in_kernelmode'],
        stats['cpu_stats']['cpu_usage']['usage_in_usermode'],
        stats['cpu_stats']['system_cpu_usage'],
        stats['precpu_stats']['cpu_usage']['total_usage'],
        stats['precpu_stats']['cpu_usage']['usage_in_kernelmode'],
        stats['precpu_stats']['cpu_usage']['usage_in_usermode'],
        stats['precpu_stats']['system_cpu_usage'],
        stats['memory_stats']['usage'],
        stats['memory_stats']['stats']['active_anon'],
        stats['memory_stats']['stats']['active_file'],
        stats['memory_stats']['stats']['anon'],
        stats['memory_stats']['stats']['file'],
        stats['memory_stats']['stats']['file_dirty'],
        stats['memory_stats']['stats']['file_mapped'],
        stats['memory_stats']['stats']['inactive_anon'],
        stats['memory_stats']['stats']['inactive_file'],
        stats['memory_stats']['stats']['kernel_stack'],
        stats['memory_stats']['stats']['pgactivate'],
        stats['memory_stats']['stats']['pgfault'],
        stats['memory_stats']['stats']['pgmajfault'],
        stats['memory_stats']['stats']['pgrefill'],
        stats['memory_stats']['stats']['pgscan'],
        stats['memory_stats']['stats']['pgsteal'],
        stats['memory_stats']['stats']['shmem'],
        stats['memory_stats']['stats']['slab'],
        stats['memory_stats']['stats']['slab_reclaimable'],
        stats['memory_stats']['stats']['slab_unreclaimable'],
        stats['memory_stats']['stats']['sock'],
        stats['networks']['eth0']['rx_bytes'],
        stats['networks']['eth0']['rx_packets'],
    ]
    
def filtered_values_cloud_all_datas_v4(stats):
    return [
        stats['qoe'],
        stats['pids_stats']['current'],
        stats['cpu_stats']['cpu_usage']['total_usage'],
        stats['cpu_stats']['cpu_usage']['usage_in_kernelmode'],
        stats['cpu_stats']['cpu_usage']['usage_in_usermode'],
        stats['cpu_stats']['system_cpu_usage'],
        stats['precpu_stats']['cpu_usage']['total_usage'],
        stats['precpu_stats']['cpu_usage']['usage_in_kernelmode'],
        stats['precpu_stats']['cpu_usage']['usage_in_usermode'],
        stats['precpu_stats']['system_cpu_usage'],
        stats['memory_stats']['usage'],
        stats['memory_stats']['stats']['active_anon'],
        stats['memory_stats']['stats']['active_file'],
        stats['memory_stats']['stats']['anon'],
        stats['memory_stats']['stats']['file'],
        stats['memory_stats']['stats']['file_dirty'],
        stats['memory_stats']['stats']['file_mapped'],
        stats['memory_stats']['stats']['inactive_anon'],
        stats['memory_stats']['stats']['inactive_file'],
        stats['memory_stats']['stats']['kernel_stack'],
        stats['memory_stats']['stats']['pgactivate'],
        stats['memory_stats']['stats']['pgfault'],
        stats['memory_stats']['stats']['pgmajfault'],
        stats['memory_stats']['stats']['pgrefill'],
        stats['memory_stats']['stats']['pgscan'],
        stats['memory_stats']['stats']['pgsteal'],
        stats['memory_stats']['stats']['shmem'],
        stats['memory_stats']['stats']['slab'],
        stats['memory_stats']['stats']['slab_reclaimable'],
        stats['memory_stats']['stats']['slab_unreclaimable'],
        stats['memory_stats']['stats']['sock'],
        stats['networks']['eth0']['rx_bytes'],
        stats['networks']['eth0']['rx_packets'],
        stats['load']
    ]

def get_prediction_lists(df, test_start_idx, val_start_idx, split_1=0.25, split_2=0.05):
    # Calculate the sizes for the splits
    size_1 = int(len(df) * split_1)
    size_2 = int(len(df) * split_2)

    # Select contiguous rows for df_test and remove from df
    df_test = df.iloc[test_start_idx:test_start_idx + size_1]
    df = df.drop(df.index[test_start_idx:test_start_idx + size_1])

    # Select contiguous rows for df_validate and remove from df
    df_validate = df.iloc[val_start_idx:val_start_idx + size_2]
    df = df.drop(df.index[val_start_idx:val_start_idx + size_2])

    # The remaining data is df_train
    df_train = df

    X_tr = df_train.values
    y_tr = df_train["qoe"].values

    X_te = df_test.values
    y_te = df_test["qoe"].values

    X_va = df_validate.values
    y_va = df_validate["qoe"].values

    return X_tr, y_tr, X_te, y_te, X_va, y_va, (test_start_idx, val_start_idx)


def get_inference_lists(df, test_start_idx, val_start_idx, split_1=0.25, split_2=0.05):
    # Calculate the sizes for the splits
    size_1 = int(len(df) * split_1)
    size_2 = int(len(df) * split_2)

    # Select contiguous rows for df_test and remove from df
    df_test = df.iloc[test_start_idx:test_start_idx + size_1]
    df = df.drop(df.index[test_start_idx:test_start_idx + size_1])

    # Select contiguous rows for df_validate and remove from df
    df_validate = df.iloc[val_start_idx:val_start_idx + size_2]
    df = df.drop(df.index[val_start_idx:val_start_idx + size_2])

    # The remaining data is df_train
    df_train = df

    y_tr = df_train["qoe"].values
    df_train = df_train.drop(columns=["qoe"])
    X_tr = df_train.values

    y_te = df_test["qoe"].values
    df_test = df_test.drop(columns=["qoe"])
    X_te = df_test.values

    y_va = df_validate["qoe"].values
    df_validate = df_validate.drop(columns=["qoe"])
    X_va = df_validate.values

    return X_tr, y_tr, X_te, y_te, X_va, y_va, (test_start_idx, val_start_idx)
