import time

class NetworkMonitor:
    def __init__(self):
        self.previous_rx_bytes = {}
        self.previous_tx_bytes = {}
        self.previous_time = {}

    def get_network_usage(self, interfaces):
        total_rx_bytes = 0
        total_tx_bytes = 0
        with open('/proc/net/dev', 'r') as f:
            for line in f:
                for intf in interfaces:
                    if intf in line:
                        data = line.split('%s:' % intf)[1].split()
                        rx_bytes, tx_bytes = (int(data[0]), int(data[8]))
                        total_rx_bytes += rx_bytes
                        total_tx_bytes += tx_bytes
        return total_rx_bytes, total_tx_bytes

    def get_network_speed(self, interfaces):
        current_time = time.time()
        rx_bytes, tx_bytes = self.get_network_usage(interfaces)
        interfaces_key = tuple(interfaces)  # Convert list to tuple for dictionary key

        if interfaces_key not in self.previous_rx_bytes:
            self.previous_rx_bytes[interfaces_key] = rx_bytes
            self.previous_tx_bytes[interfaces_key] = tx_bytes
            self.previous_time[interfaces_key] = current_time
            return 0, 0

        time_diff = current_time - self.previous_time[interfaces_key]
        rx_speed = (rx_bytes - self.previous_rx_bytes[interfaces_key]) / time_diff
        tx_speed = (tx_bytes - self.previous_tx_bytes[interfaces_key]) / time_diff

        self.previous_rx_bytes[interfaces_key] = rx_bytes
        self.previous_tx_bytes[interfaces_key] = tx_bytes
        self.previous_time[interfaces_key] = current_time

        return rx_speed, tx_speed

if '__main__' == __name__:
    
    edge1 = [f'e{i}-wlan1' for i in range(1, 4)]
    edge2 = [f'e{i}-wlan1' for i in range(4, 7)]
    edge3 = [f'e{i}-wlan1' for i in range(7, 10)]

    monitor = NetworkMonitor()
    while True:
        rx_speed, tx_speed = monitor.get_network_speed(edge1)
        print(f'Edge1 -> RX: {rx_speed:.2f} bytes/s, TX: {tx_speed:.2f} bytes/s')
        
        rx_speed, tx_speed = monitor.get_network_speed(edge2)
        print(f'Edge2 -> RX: {rx_speed:.2f} bytes/s, TX: {tx_speed:.2f} bytes/s')
        
        rx_speed, tx_speed = monitor.get_network_speed(edge3)
        print(f'Edge3 -> RX: {rx_speed:.2f} bytes/s, TX: {tx_speed:.2f} bytes/s')
        
        time.sleep(10)