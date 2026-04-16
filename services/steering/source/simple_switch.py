from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ipv4

class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        # Get the packet
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Extract the packet data
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        # Ignore packets that are not IP packets
        if eth.ethertype != 0x0800:
            return

        # Extract the IP packet
        ip_pkt = pkt.get_protocol(ipv4.ipv4)

        # Extract source and destination IP addresses
        src_ip = ip_pkt.src
        dst_ip = ip_pkt.dst

        # Print the IP addresses
        self.logger.info("Packet in: %s -> %s", src_ip, dst_ip)

        # Here, you can add logic to handle the packet or forward it based on IP addresses
        # Example: forwarding packet out to a specific port
        # actions = [parser.OFPActionOutput(ofproto.OFPP_FLOOD)]
        # out = parser.OFPPacketOut(
        #     datapath=datapath, buffer_id=msg.buffer_id, in_port=msg.match['in_port'],
        #     actions=actions, data=msg.data)
        # datapath.send_msg(out)
