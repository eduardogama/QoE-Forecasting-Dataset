import json
import sqlite3


class Sqlite3Service:
    def __init__(self, db_file):
        self.db_file = db_file
        self.conn = None

    def connect(self, timeout=5):
        self.conn = sqlite3.connect(self.db_file, timeout=timeout, check_same_thread=False)

    def disconnect(self):
        if self.conn:
            self.conn.close()

    def create_table(self, table_name, columns):
        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns})"
        self.conn.execute(query)
        self.conn.commit()

    def insert_data(self, table_name, data):
        if self.conn is None:
            self.connect()

        try:
            placeholders = ', '.join(['?' for _ in data])
            query = f"INSERT INTO {table_name} VALUES ({placeholders})"
            self.conn.execute(query, data)
            self.conn.commit()
        except sqlite3.OperationalError as e:
            self.conn.rollback()


    def update_data(self, table_name, data, condition):
        placeholders = ', '.join([f"{column} = ?" for column in data])
        query = f"UPDATE {table_name} SET {placeholders} WHERE {condition}"
        self.conn.execute(query, tuple(data.values()))
        self.conn.commit()

    def delete_data(self, table_name, condition):
        query = f"DELETE FROM {table_name} WHERE {condition}"
        self.conn.execute(query)
        self.conn.commit()

    def select_data(self, table_name, columns="*", condition=None):
        query = f"SELECT {columns} FROM {table_name}"
        if condition:
            query += f" WHERE {condition}"
        cursor = self.conn.execute(query)
        return cursor.fetchall()
    def list_tables(self):
        cursor = self.conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
        return cursor.fetchall()
    

class Sqlite3ContainerMonitor(Sqlite3Service):
    def __init__(self, database):
        super(Sqlite3ContainerMonitor, self).__init__(database)
        self.table = 'containerMonitor'

    def create_table(self):
        super(Sqlite3ContainerMonitor, self).create_table(self.table, 'container_name TEXT, metrics TEXT')

    def insert_container_metrics(self, container_name, metrics):
        data = (container_name, json.dumps(metrics))
        super(Sqlite3ContainerMonitor, self).insert_data(self.table, data)
    
    def list_container_metrics(self):
        return self.select_data(self.table)
        
    def get_container_metrics(self, container_name):
        return self.select_data(self.table, condition=f"container_name = '{container_name}'")
    
    def get_last_container_metrics(self, container_name):
        return self.select_data(self.table, condition=f"rowid = (SELECT MAX(rowid) FROM '{container_name}')")

    def get_last_n_rows(self, container_name, n):
        query = f"SELECT container_name, metrics FROM {self.table} WHERE container_name = '{container_name}' ORDER BY rowid DESC LIMIT {n}"
        cursor = self.conn.execute(query)
        return cursor.fetchall()

    def get_last_metrics_for_each_container(self):
        query = f"SELECT container_name, metrics FROM {self.table} WHERE rowid IN (SELECT MAX(rowid) FROM {self.table} GROUP BY container_name)"
        cursor = self.conn.execute(query)
        return cursor.fetchall()

    def get_last_row_for_each_container(self, container_name):
        query = f"SELECT container_name, MAX(rowid) FROM {self.table} GROUP BY container_name"
        cursor = self.conn.execute(query)
        return cursor.fetchall()

class Sqlite3PlayerMonitor(Sqlite3Service):
    def __init__(self, database):
        super(Sqlite3PlayerMonitor, self).__init__(database)
        self.table = 'playerMonitor'

    def create_table(self):
        super(Sqlite3PlayerMonitor, self).create_table(self.table, 'player_name TEXT, metrics TEXT')

    def insert_player_metrics(self, player_name, metrics):
        data = (player_name, json.dumps(metrics))
        super(Sqlite3PlayerMonitor, self).insert_data(self.table, data)
    
    def list_player_metrics(self):
        return self.select_data(self.table)
        
    def get_player_metrics(self, player_name):
        return self.select_data(self.table, condition=f"player_name = '{player_name}'")
    
    def get_last_player_metrics(self, player_name):
        return self.select_data(self.table, condition=f"rowid = (SELECT MAX(rowid) FROM '{player_name}')")

    def get_last_metrics_for_each_player(self):
        query = f"SELECT player_name, metrics FROM {self.table} WHERE rowid IN (SELECT MAX(rowid) FROM {self.table} GROUP BY player_name)"
        cursor = self.conn.execute(query)
        return cursor.fetchall()

    def get_last_row_for_each_player(self, player_name):
        query = f"SELECT player_name, MAX(rowid) FROM {self.table} GROUP BY player_name"
        cursor = self.conn.execute(query)
        return cursor.fetchall()
    
class Sqlite3NodeMonitor(Sqlite3Service):
    def __init__(self, database):
        super(Sqlite3NodeMonitor, self).__init__(database)
        self.table = 'nodeMonitor'

    def create_table(self):
        super(Sqlite3NodeMonitor, self).create_table(self.table, 'node_name TEXT, metrics TEXT')

    def insert_node_metrics(self, node_name, metrics):
        data = (node_name, json.dumps(metrics))
        super(Sqlite3NodeMonitor, self).insert_data(self.table, data)
    
    def list_node_metrics(self):
        return self.select_data(self.table)
    
    def list_nodes(self):
        tuples = self.select_data(self.table, columns="DISTINCT node_name")
        return [ node_name[0] for node_name in tuples ]
    
    def get_node_metrics(self, node_name):
        return self.select_data(self.table, condition=f"node_name = '{node_name}'")
    
    def get_last_node_metrics(self, node_name):
        return self.select_data(self.table, condition=f"rowid = (SELECT MAX(rowid) FROM '{node_name}')")

    def get_last_metrics_for_each_node(self):
        query = f"SELECT node_name, metrics FROM {self.table} WHERE rowid IN (SELECT MAX(rowid) FROM {self.table} GROUP BY node_name)"
        cursor = self.conn.execute(query)
        return cursor.fetchall()

    def get_last_row_for_each_node(self, node_name):
        query = f"SELECT node_name, MAX(rowid) FROM {self.table} GROUP BY node_name"
        cursor = self.conn.execute(query)
        return cursor.fetchall()
    
    def get_last_n_rows(self, container_name, n):
        query = f"SELECT node_name, metrics FROM {self.table} WHERE node_name = '{container_name}' ORDER BY rowid DESC LIMIT {n}"
        cursor = self.conn.execute(query)
        return cursor.fetchall()

class Sqlite3HandoverMonitor(Sqlite3Service):
    def __init__(self, database):
        super(Sqlite3HandoverMonitor, self).__init__(database)
        self.table = 'handoverMonitor'

    def create_table(self):
        super(Sqlite3HandoverMonitor, self).create_table(self.table, 'address TEXT, base_station TEXT')

    def insert_handover_metrics(self, node_name, metrics):
        data = (node_name, json.dumps(metrics))
        super(Sqlite3HandoverMonitor, self).insert_data(self.table, data)
    
    def list_handover_metrics(self):
        return self.select_data(self.table)
    
    def list_handovers(self):
        tuples = self.select_data(self.table, columns="DISTINCT address")
        return [ node_name[0] for node_name in tuples ]
    
    def get_handover_metrics(self, node_name):
        return self.select_data(self.table, condition=f"address = '{node_name}'")
    
    def get_last_handover_metrics(self, node_name):
        return self.select_data(self.table, condition=f"rowid = (SELECT MAX(rowid) FROM '{node_name}')")

    def get_last_metrics_for_each_address(self):
        query = f"SELECT address, base_station FROM {self.table} WHERE rowid IN (SELECT MAX(rowid) FROM {self.table} GROUP BY address)"
        cursor = self.conn.execute(query)
        return cursor.fetchall()

    def get_last_row_for_each_address(self, node_name):
        query = f"SELECT address, MAX(rowid) FROM {self.table} GROUP BY address"
        cursor = self.conn.execute(query)
        return cursor.fetchall()
    
    def get_last_n_rows(self, container_name, n):
        query = f"SELECT address, base_station FROM {self.table} WHERE address = '{container_name}' ORDER BY rowid DESC LIMIT {n}"
        cursor = self.conn.execute(query)
        return cursor.fetchall()
    
class Sqlite3NetworkMonitor(Sqlite3Service):
    def __init__(self, database):
        super(Sqlite3NetworkMonitor, self).__init__(database)
        self.table = 'networkMonitor'
        
    def create_table(self):
        super(Sqlite3NetworkMonitor, self).create_table(self.table, 'network_name TEXT, metrics TEXT')
        
    def insert_network_metrics(self, network_name, metrics):
        data = (network_name, json.dumps(metrics))
        super(Sqlite3NetworkMonitor, self).insert_data(self.table, data)
        
    def list_network_metrics(self):
        return self.select_data(self.table)
    
    def get_network_metrics(self, network_name):
        return self.select_data(self.table, condition=f"network_name = '{network_name}'")
    
    def get_last_network_metrics(self, network_name):
        return self.select_data(self.table, condition=f"rowid = (SELECT MAX(rowid) FROM '{network_name}')")
    
    def get_last_metrics_for_each_network(self):
        query = f"SELECT network_name, metrics FROM {self.table} WHERE rowid IN (SELECT MAX(rowid) FROM {self.table} GROUP BY network_name)"
        cursor = self.conn.execute(query)
        return cursor.fetchall()
    
    def get_last_row_for_each_network(self, network_name):
        query = f"SELECT network_name, MAX(rowid) FROM {self.table} GROUP BY network_name"
        cursor = self.conn.execute(query)
        return cursor.fetchall()
    
    def get_last_n_rows(self, container_name, n):
        query = f"SELECT network_name, metrics FROM {self.table} WHERE network_name = '{container_name}' ORDER BY rowid DESC LIMIT {n}"
        cursor = self.conn.execute(query)
        return cursor.fetchall()
    
        
# EOF