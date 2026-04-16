class EdgeCluster:
    
    def __init__(self, name, weight=1):
        self.name = name
        self.weight = weight
        self.current_server_index = 0
        self.servers = []

    def addServer(self, capacity, uri, weight=1):
        server = EdgeServer("", capacity, uri)
        server.weight = weight
        
        self.servers.append(server)


class EdgeServer:
    def __init__(self, name, capacity, uri, weight=1):
        self.name = name
        self.uri = uri
        self.weight = weight
        self.capacity = capacity
        self.current_load = 0
        
    def isAvailable(self):
        return self.current_load < self.capacity

    def serveRequest(self):
        if self.is_available():
            self.current_load += 1
            return True
        else:
            return False