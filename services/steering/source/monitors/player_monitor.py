

class PlayerMonitor:
    def __init__(self, filename='container_stats.db', interval=1):        
        self.db = Sqlite3PlayerMonitor(filename)
        self.db.create_table()

        self.filename = filename

    def run(self):
        while True:
            containers = self.client.containers.list()
            for container in containers:
                container_stats = container.stats(stream=False)
                self.db.insert_data(container_stats)
                logging.info(f"Data inserted for container: {container.name}")
            time.sleep(self.interval)