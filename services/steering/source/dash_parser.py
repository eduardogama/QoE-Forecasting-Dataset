class DashParser:
    def __init__(self):
        self.count = 0
        self.ttl = 10
        self.pathway_clones = [
            {
                "BASE-ID": f"mn.cloud-1",
                "ID": f"mn.edge1",
                "URI-REPLACEMENT": {
                    "HOST": f"mn.edge1",
                    "PARAMS": {}
                }
            },
            {
                "BASE-ID": f"mn.cloud-1",
                "ID": f"mn.edge2",
                "URI-REPLACEMENT": {
                    "HOST": f"mn.edge2",
                    "PARAMS": {}
                }
            },
            {
                "BASE-ID": f"mn.cloud-1",
                "ID": f"mn.edge3",
                "URI-REPLACEMENT": {
                    "HOST": f"mn.edge3",
                    "PARAMS": {}
                }
            },
            {
                "BASE-ID": f"mn.cloud-1",
                "ID": f"mn.edge4",
                "URI-REPLACEMENT": {
                    "HOST": f"mn.edge4",
                    "PARAMS": {}
                }
            },
            {
                "BASE-ID": f"mn.cloud-1",
                "ID": f"mn.edge5",
                "URI-REPLACEMENT": {
                    "HOST": f"mn.edge5",
                    "PARAMS": {}
                }
            },
            {
                "BASE-ID": f"mn.cloud-1",
                "ID": f"mn.edge6",
                "URI-REPLACEMENT": {
                    "HOST": f"mn.edge6",
                    "PARAMS": {}
                }
            }
        ]

    def build(self, target, nodes, uri, request):
        message = {
            "VERSION": 1,
            "TTL": self.ttl,
            "RELOAD-URI": f"{uri}{request.path}",
            "PATHWAY-PRIORITY": [f"{node}" for node in nodes],
            "PATHWAY-CLONES": self.pathway_clones
        }

        return message