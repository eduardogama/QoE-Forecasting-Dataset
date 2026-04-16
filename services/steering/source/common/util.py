import json
import pandas as pd

from common.sql_service import Sqlite3ContainerMonitor


def flatten_json_and_store(datas, csv_file_path):
    final = pd.DataFrame()

    # Iterate over the list of JSON data
    for data in datas:

        # Convert the JSON string to a Python dictionary
        data_dict = json.loads(data[1])

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
    final = final.drop(columns=['blkio_stats.io_service_bytes_recursive'])
    
    # If the file does not exist, write the header
    final.to_csv(csv_file_path, mode='w', index=False)



def create_csv_from_remote_server(users=5, path='/home/eduardo/workspace/drl-css/logs'):

    path_monitor = f'{path}/monitor/{users}'
    path_users = f'{path}/users/{users}'

    # Create a connection to the database
    db = Sqlite3ContainerMonitor(f'{path_monitor}/container_stats.db')
    db.connect()

    datas = db.list_container_metrics()
    flatten_json_and_store(datas, f'{path_monitor}/monitor.csv')


    monitor_data = pd.read_csv(f'{path_monitor}/monitor.csv')
    monitor_data['read'] = pd.to_datetime(monitor_data['read'])
    monitor_data['read'] = pd.to_datetime(monitor_data['read']).dt.tz_localize(None)


    monitor_data['qoe'] = 0.0
    monitor_data['thr'] = 0.0
    monitor_data['quality'] = 0.0
    monitor_data['expected throughput'] = 0.0
    monitor_data['nusers'] = 0


    sta_datas = []
    for i in range(1, users+1):
        data = pd.read_csv(f'{path_users}/sta{i}-iw.csv').rename(columns={'timestamp': 'read'})
        data['read'] = pd.to_datetime(data['read']).dt.tz_localize(None)

        sta_datas.append(data)


    monitor_datas = []
    for u in range(users):
        
        monitor_data_copy = monitor_data.copy()

        for i in range(len(monitor_data_copy)):
            
            current_read = monitor_data_copy['read'][i]
            next_read = monitor_data_copy['read'][i+1] if i+1 < len(monitor_data_copy) else None

            if next_read is not None:
                filtered_data = sta_datas[u][(sta_datas[u]['read'] >= current_read) & (sta_datas[u]['read'] < next_read)]
            else:
                filtered_data = sta_datas[u][sta_datas[u]['read'] >= current_read]
            
            if not filtered_data.empty:
                filtered_data.loc[:, 'expected throughput ()'] = filtered_data['expected throughput ()'].str.replace('Mbps', '').astype(float)
    
                avg_quality = filtered_data['quality'].mean()
                avg_qoe = filtered_data['qoe'].mean()
                avg_thr = filtered_data['thr'].mean()
                avg_exp_thr = filtered_data['expected throughput ()'].mean()
                
                monitor_data_copy.loc[i, 'qoe'] = avg_qoe
                monitor_data_copy.loc[i, 'thr'] = avg_thr
                monitor_data_copy.loc[i, 'quality'] = avg_quality
                monitor_data_copy.loc[i, 'expected throughput'] = avg_exp_thr

            # print(filtered_data)


        for i in range(1, len(monitor_data_copy)-1):
            if monitor_data_copy.loc[i, 'qoe'] == 0.0 and monitor_data_copy.loc[i+1, 'thr'] != 0.0:
                monitor_data_copy.loc[i, 'qoe'] = monitor_data_copy.loc[i-1, 'qoe']
            if monitor_data_copy.loc[i, 'thr'] == 0.0 and monitor_data_copy.loc[i+1, 'thr'] != 0.0:
                monitor_data_copy.loc[i, 'thr'] = monitor_data_copy.loc[i-1, 'thr']
            if monitor_data_copy.loc[i, 'quality'] == 0.0 and monitor_data_copy.loc[i+1, 'quality'] != 0.0:
                monitor_data_copy.loc[i, 'quality'] = monitor_data_copy.loc[i-1, 'quality']
            if monitor_data_copy.loc[i, 'expected throughput'] == 0.0 and monitor_data_copy.loc[i+1, 'expected throughput'] != 0.0:
                monitor_data_copy.loc[i, 'expected throughput'] = monitor_data_copy.loc[i-1, 'expected throughput']

        monitor_data_copy.to_csv(f'{path_users}/merged-{u}.csv',  index=False)
        monitor_datas.append(monitor_data_copy)


    for i in range(len(monitor_data)):

        nusers = 0
        for data in monitor_datas:
            nusers += 1 if data['qoe'][i] != 0.0 else 0

        if nusers != 0:
            mean_qoe = sum([data['qoe'][i] for data in monitor_datas]) / nusers
            mean_thr = sum([data['thr'][i] for data in monitor_datas]) / nusers
            mean_quality = sum([data['quality'][i] for data in monitor_datas]) / nusers
            mean_exp_thr = sum([data['expected throughput'][i] for data in monitor_datas]) / nusers
        else:
            mean_qoe = mean_thr = mean_quality = mean_exp_thr = 0
        
        monitor_data.loc[i, 'qoe'] = mean_qoe
        monitor_data.loc[i, 'thr'] = mean_thr
        monitor_data.loc[i, 'quality'] = mean_quality
        monitor_data.loc[i, 'expected throughput'] = mean_exp_thr
        monitor_data.loc[i, 'nusers'] = nusers

    monitor_data.to_csv(f'{path}/merged-result-{users}.csv', index=False)


def create_csv():
    users = 5
    path = f'logs-db/{users}'

    # Create a connection to the database
    db = Sqlite3ContainerMonitor(f'{path}/container_stats.db')
    db.connect()

    datas = db.list_container_metrics()
    flatten_json_and_store(datas, f'{path}/monitor.csv')


    monitor_data = pd.read_csv(f'{path}/monitor.csv')
    monitor_data['read'] = pd.to_datetime(monitor_data['read'])
    monitor_data['read'] = pd.to_datetime(monitor_data['read']).dt.tz_localize(None)


    monitor_data['qoe'] = 0.0
    monitor_data['thr'] = 0.0
    monitor_data['quality'] = 0.0
    monitor_data['expected throughput'] = 0.0
    monitor_data['nusers'] = 0


    sta_datas = []
    for i in range(1, users+1):
        data = pd.read_csv(f'{path}/sta{i}-iw.csv').rename(columns={'timestamp': 'read'})
        data['read'] = pd.to_datetime(data['read'])
        data['read'] = pd.to_datetime(data['read']).dt.tz_localize(None)

        sta_datas.append(data)


    monitor_datas = []
    for u in range(users):
        
        monitor_data_copy = monitor_data.copy()

        for i in range(len(monitor_data_copy)):
            
            current_read = monitor_data_copy['read'][i]
            next_read = monitor_data_copy['read'][i+1] if i+1 < len(monitor_data_copy) else None

            if next_read is not None:
                filtered_data = sta_datas[u][(sta_datas[u]['read'] >= current_read) & (sta_datas[u]['read'] < next_read)]
            else:
                filtered_data = sta_datas[u][sta_datas[u]['read'] >= current_read]
            
            if not filtered_data.empty:
                filtered_data['expected throughput ()'] = filtered_data['expected throughput ()'].str.replace('Mbps', '').astype(float)
                avg_quality = filtered_data['quality'].mean()
                avg_qoe = filtered_data['qoe'].mean()
                avg_thr = filtered_data['thr'].mean()
                avg_exp_thr = filtered_data['expected throughput ()'].mean()
                
                monitor_data_copy.loc[i, 'qoe'] = avg_qoe
                monitor_data_copy.loc[i, 'thr'] = avg_thr
                monitor_data_copy.loc[i, 'quality'] = avg_quality
                monitor_data_copy.loc[i, 'expected throughput'] = avg_exp_thr

            print(filtered_data)


        for i in range(1, len(monitor_data_copy)-1):
            if monitor_data_copy.loc[i, 'qoe'] == 0.0 and monitor_data_copy.loc[i+1, 'thr'] != 0.0:
                monitor_data_copy.loc[i, 'qoe'] = monitor_data_copy.loc[i-1, 'qoe']
            if monitor_data_copy.loc[i, 'thr'] == 0.0 and monitor_data_copy.loc[i+1, 'thr'] != 0.0:
                monitor_data_copy.loc[i, 'thr'] = monitor_data_copy.loc[i-1, 'thr']
            if monitor_data_copy.loc[i, 'quality'] == 0.0 and monitor_data_copy.loc[i+1, 'quality'] != 0.0:
                monitor_data_copy.loc[i, 'quality'] = monitor_data_copy.loc[i-1, 'quality']
            if monitor_data_copy.loc[i, 'expected throughput'] == 0.0 and monitor_data_copy.loc[i+1, 'expected throughput'] != 0.0:
                monitor_data_copy.loc[i, 'expected throughput'] = monitor_data_copy.loc[i-1, 'expected throughput']

        monitor_data_copy.to_csv(f'{path}/merged-{u}.csv',  index=False)
        monitor_datas.append(monitor_data_copy)


    for i in range(len(monitor_data)):

        nusers = 0
        for data in monitor_datas:
            nusers += 1 if data['qoe'][i] != 0.0 else 0

        mean_qoe = sum([data['qoe'][i] for data in monitor_datas]) / nusers
        mean_thr = sum([data['thr'][i] for data in monitor_datas]) / nusers
        mean_quality = sum([data['quality'][i] for data in monitor_datas]) / nusers
        mean_exp_thr = sum([data['expected throughput'][i] for data in monitor_datas]) / nusers

        monitor_data['qoe'][i] = mean_qoe
        monitor_data['thr'][i] = mean_thr
        monitor_data['quality'][i] = mean_quality
        monitor_data['expected throughput'][i] = mean_exp_thr
        monitor_data['nusers'][i] = nusers

    monitor_data.to_csv(f'{path}/merged-result.csv', index=False)
    
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

def filtered_values_1(stats):
    return [
        stats["cpu_stats"]["cpu_usage"]["total_usage"],
        stats["cpu_stats"]["cpu_usage"]["usage_in_kernelmode"],
        stats["cpu_stats"]["cpu_usage"]["usage_in_usermode"],
        stats["cpu_stats"]["system_cpu_usage"],
        stats["precpu_stats"]["cpu_usage"]["total_usage"],
        stats["precpu_stats"]["cpu_usage"]["usage_in_kernelmode"],
        stats["precpu_stats"]["cpu_usage"]["usage_in_usermode"],
        stats["precpu_stats"]["system_cpu_usage"],
        stats["memory_stats"]["usage"],
        stats["memory_stats"]["stats"]["active_anon"],
        stats["memory_stats"]["stats"]["active_file"],
        stats["memory_stats"]["stats"]["anon"],
        stats["memory_stats"]["stats"]["file"],
        stats["memory_stats"]["stats"]["file_dirty"],
        stats["memory_stats"]["stats"]["file_mapped"],
        stats["memory_stats"]["stats"]["inactive_anon"],
        stats["memory_stats"]["stats"]["inactive_file"],
        stats["memory_stats"]["stats"]["kernel_stack"],
        stats["memory_stats"]["stats"]["pgfault"],
        stats["memory_stats"]["stats"]["pgmajfault"],
        stats["memory_stats"]["stats"]["pgrefill"],
        stats["memory_stats"]["stats"]["pgscan"],
        stats["memory_stats"]["stats"]["pgsteal"],
        stats["memory_stats"]["stats"]["slab"],
        stats["memory_stats"]["stats"]["slab_reclaimable"],
        stats["memory_stats"]["stats"]["slab_unreclaimable"],
        stats["memory_stats"]["stats"]["sock"],
        stats["memory_stats"]["limit"],
        stats["networks"]["eth0"]["rx_bytes"],
        stats["networks"]["eth0"]["rx_packets"],
        stats["blkio_stats"]["io_service_bytes_recursive"][0]["value"],
        stats["qoe"]
    ]

def filtered_values_2(stats):
    return [
        stats["qoe"],
        stats["cpu_stats"]["cpu_usage"]["total_usage"],
        stats["cpu_stats"]["cpu_usage"]["usage_in_kernelmode"],
        stats["cpu_stats"]["cpu_usage"]["usage_in_usermode"],
        stats["cpu_stats"]["system_cpu_usage"],
        stats["precpu_stats"]["cpu_usage"]["total_usage"],
        stats["precpu_stats"]["cpu_usage"]["usage_in_kernelmode"],
        stats["precpu_stats"]["cpu_usage"]["usage_in_usermode"],
        stats["precpu_stats"]["system_cpu_usage"],
        stats["memory_stats"]["usage"],
        stats["memory_stats"]["stats"]["active_anon"],
        stats["memory_stats"]["stats"]["active_file"],
        stats["memory_stats"]["stats"]["anon"],
        stats["memory_stats"]["stats"]["inactive_anon"],
        stats["memory_stats"]["stats"]["pgfault"],
        stats["memory_stats"]["stats"]["slab"],
        stats["memory_stats"]["stats"]["slab_reclaimable"],
        stats["memory_stats"]["stats"]["slab_unreclaimable"],
        stats["memory_stats"]["stats"]["sock"],
        stats["networks"]["eth0"]["rx_bytes"],
        stats["networks"]["eth0"]["rx_packets"],
        stats["networks"]["eth0"]["tx_bytes"],
        stats["networks"]["eth0"]["tx_packets"]
    ]

def filtered_values_3(stats):
    return [
        stats["qoe"],
        stats["cpu_stats"]["cpu_usage"]["total_usage"],
        stats["cpu_stats"]["cpu_usage"]["usage_in_kernelmode"],
        stats["cpu_stats"]["cpu_usage"]["usage_in_usermode"],
        stats["cpu_stats"]["system_cpu_usage"],
        stats["precpu_stats"]["cpu_usage"]["total_usage"],
        stats["precpu_stats"]["cpu_usage"]["usage_in_kernelmode"],
        stats["precpu_stats"]["cpu_usage"]["usage_in_usermode"],
        stats["precpu_stats"]["system_cpu_usage"],
        stats["memory_stats"]["usage"],
        stats["memory_stats"]["stats"]["active_anon"],
        stats["memory_stats"]["stats"]["anon"],
        stats["memory_stats"]["stats"]["file_dirty"],
        stats["memory_stats"]["stats"]["inactive_anon"],
        stats["memory_stats"]["stats"]["pgactivate"],
        stats["memory_stats"]["stats"]["pgfault"],
        stats["memory_stats"]["stats"]["slab"],
        stats["memory_stats"]["stats"]["slab_reclaimable"],
        stats["memory_stats"]["stats"]["slab_unreclaimable"],
        stats["memory_stats"]["stats"]["sock"],
        stats["networks"]["eth0"]["rx_bytes"],
        stats["networks"]["eth0"]["rx_packets"],
        stats["networks"]["eth0"]["tx_bytes"],
        stats["networks"]["eth0"]["tx_packets"],
        stats["blkio_stats"]["io_service_bytes_recursive"][0]["major"],
        stats["blkio_stats"]["io_service_bytes_recursive"][0]["minor"],
        stats["blkio_stats"]["io_service_bytes_recursive"][1]["major"],
        stats["blkio_stats"]["io_service_bytes_recursive"][1]["minor"],
        stats["blkio_stats"]["io_service_bytes_recursive"][1]["value"]
    ]

def filtered_values(stats):
    return [
        stats["qoe"],
        stats["cpu_stats"]["cpu_usage"]["total_usage"],
        stats["cpu_stats"]["cpu_usage"]["usage_in_kernelmode"],
        stats["cpu_stats"]["cpu_usage"]["usage_in_usermode"],
        stats["cpu_stats"]["system_cpu_usage"],
        stats["precpu_stats"]["cpu_usage"]["total_usage"],
        stats["precpu_stats"]["cpu_usage"]["usage_in_kernelmode"],
        stats["precpu_stats"]["cpu_usage"]["usage_in_usermode"],
        stats["precpu_stats"]["system_cpu_usage"],
        stats["memory_stats"]["usage"],
        stats["memory_stats"]["stats"]["active_anon"],
        stats["memory_stats"]["stats"]["anon"],
        stats["memory_stats"]["stats"]["file_dirty"],
        stats["memory_stats"]["stats"]["inactive_anon"],
        stats["memory_stats"]["stats"]["pgactivate"],
        stats["memory_stats"]["stats"]["pgfault"],
        stats["memory_stats"]["stats"]["slab"],
        stats["memory_stats"]["stats"]["slab_reclaimable"],
        stats["memory_stats"]["stats"]["slab_unreclaimable"],
        stats["memory_stats"]["stats"]["sock"],
        stats["networks"]["eth0"]["rx_bytes"],
        stats["networks"]["eth0"]["rx_packets"],
        stats["networks"]["eth0"]["tx_bytes"],
        stats["networks"]["eth0"]["tx_packets"],
        stats["blkio_stats"]["io_service_bytes_recursive"][0]["major"],
        stats["blkio_stats"]["io_service_bytes_recursive"][0]["minor"],
        stats["blkio_stats"]["io_service_bytes_recursive"][1]["major"],
        stats["blkio_stats"]["io_service_bytes_recursive"][1]["minor"],
        stats["blkio_stats"]["io_service_bytes_recursive"][1]["value"],
        stats["blkio_stats"]["io_service_bytes_recursive"][2]["major"],
        stats["blkio_stats"]["io_service_bytes_recursive"][3]["major"],
        stats["blkio_stats"]["io_service_bytes_recursive"][3]["value"]
    ]

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
        stats['blkio_stats']['io_service_bytes_recursive'][0]['value'],
        stats['blkio_stats']['io_service_bytes_recursive'][1]['value']
    ]