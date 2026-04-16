from entities import EdgeCluster, EdgeServer
import json


class Selector:
    def __init__(self, monitor=None):
        self.clouds = []
        self.clusters = []
        self.sessions = {}

        self.monitor = monitor
        self.request_problem = None
        self.select_cache_problem = None

    def addCloudCluster(self, name, weight=1):
        cloud = EdgeCluster(name, weight)
        self.clouds.append(cloud)

    def addCluster(self, cluster):
        if not isinstance(cluster, EdgeCluster):
            raise ValueError("Cluster must be an instance of EdgeCluster")
        self.clusters.append(cluster)

    def addClusters(self, clusters):
        for cluster in clusters:
            self.addCluster(cluster)

    def addServer(self, cluster, server):
        if not isinstance(server, EdgeServer):
            raise ValueError("Server must be an instance of EdgeServer")
        cluster.add_server(server)

    def addServersToCluster(self, cluster, servers):
        for server in servers:
            self.addServer(cluster, server)

    def getClusters(self):
        return self.clusters
    
    def getCluster(self, name):
        for cluster in self.clusters:
            if cluster.name == name:
                return cluster
        return None
    
    def getServer(self, cluster_name, server_name):
        cluster = self.getCluster(cluster_name)
        if cluster is not None:
            for server in cluster.servers:
                if server.name == server_name:
                    return server
        return None
    


    def set_request_problem(self, problem):
        self.request_problem = problem

    def set_select_cache_problem(self, problem):
        self.select_cache_problem = problem
        

    def solve(self, uid, **kwargs) -> object:
        # Implement your solution logic here
        if self.request_problem is None or self.select_cache_problem is None:
            raise ValueError("Both request problem and select cache problem must be set")

        # Your solution code goes here

        # Return the result
        return "Solution"



class RoundRobinBalancer(Selector):
    def __ini__(self, monitor=None):
        self.current_server_index = 0
        
        super().__init__(monitor=monitor)


    def solve(self, **kwargs) -> object:
        for cluster in self.clusters:

            num_servers = len(cluster.servers)
            idx = cluster.current_server_index
            
            for _ in range(num_servers):
                server = cluster.servers[idx]        
                idx = (idx + 1) % num_servers

                if server.is_available():
                    self.current_server_index = idx
                    return server
        
        return None

class RegionAware(Selector):
    def __ini__(self, monitor=None):
        self.usersMap = {}
        self.mapRegion = {}
        self.current_server_index = 0
        
        super().__init__(monitor=monitor)

    def solve(self, **kwargs) -> object:
        adr = kwargs['adr']
        region_edge_server = self.monitor.locate_region_server(adr)
        
        if region_edge_server != 'mn.cloud-1' and region_edge_server in self.monitor.get_available_nodes():
            return [region_edge_server] + ['mn.cloud-1']

        return ['mn.cloud-1']

class ContentAwareRoundRobinBalancer(Selector):
    def __ini__(self, monitor=None):
        self.videosMap = {}
        self.current_server_index = 0

        super().__init__(monitor=monitor)

    def solve(self, **kwargs) -> object:
        v = kwargs['vid']
        
        if v in self.videosMap:
            return self.videosMap[v]

        for cluster in self.clusters:
            num_servers = len(cluster.servers)
            idx = self.current_server_index
            
            for _ in range(num_servers):
                server = cluster.servers[idx]
                idx = (idx + 1) % num_servers

                if server.is_available():
                    self.current_server_index = idx
                    self.videosMap[v] = server

                    return server
        return None

    def RequestRoutingProblem(self, uid, **kwargs):
        if uid in self.sessions:
            return self.sessions[uid]
                
        server = self.solve(**kwargs)

        server.serve_request()
        self.sessions[uid] = [server] + self.clouds

        return self.sessions[uid] 


if __name__ == "__main__":
    selector = Selector()
    selector.set_request_problem("Request problem")
    selector.set_select_cache_problem("Select cache problem")
    solution = selector.solve()
    print(solution)