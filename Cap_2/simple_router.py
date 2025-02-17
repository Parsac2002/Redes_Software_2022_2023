# Copyright (C) 2011 Nippon Telegraph and Telephone Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
#from ryu.lib.packet import ipv6
from ryu.lib.packet import icmp
from ryu.lib.packet import ipv4
from ryu.lib.packet import in_proto #como ether_types pero para protocolos de la capa superior en IP.



class SimpleRouter(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleRouter, self).__init__(*args, **kwargs)
        self.mac_to_port = {}

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)#responde a las peticiones de configuracion que manda el switch.
    def switch_features_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        #fLUJOS PARA LLDP E IPV6:
        # LLDP -> 
        match_LLDP = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_LLDP)
        actions_LLDP = self.dropActions(parser = parser, ofproto = ofproto)
        self.add_flow(datapath= datapath, priority = 10000, match = match_LLDP, actions = actions_LLDP)
        # IPV6 -> 
        match_IPV6 = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IPV6)
        actions_IPV6 = self.dropActions(parser = parser, ofproto = ofproto)
        self.add_flow(datapath= datapath, priority = 10000, match = match_IPV6, actions = actions_IPV6)
        
        #TODO: Paquetes ICMP: solamente procesamos los mensajes ICMP que le llegan al switch.
        # pkt = packet.Packet(msg.data)
        # eth = pkt.get_protocol(ethernet.ethernet)
        # if eth.ethertype == ether_types.ETH_TYPE_IP:
        #     ip = pkt.get_protocol(ipv4.ipv4)
        #     protocol = ip.proto
        #     if protocol == in_proto.IPPROTO_ICMP:
        #         match_ICMP = parser.OFPMatch(eth_type= ether_types.ETH_TYPE_IP)
        #         actions_ICMP = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
        #                                         ofproto.OFPCML_NO_BUFFER)]
        #         self.add_flow(datapath, 5000, match_ICMP, actions_ICMP)
        #         #Luego ya le decimos en el Main_dispatcher al switch que hacer con el paquete que nosotros le mandemos.

        #Paquetes ICMP
        match_ICMP = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP, ipv4_dst=('0.0.0.1', '0.0.0.255'))
        actions_ICMP = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                        ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 5000, match_ICMP, actions_ICMP)

        #Paquetes desde h1 a h2:
        match_1 = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP, ipv4_dst=('10.0.1.0', '255.255.255.0'))
        actions_1 = self.forwardActions(parser = parser, ofproto = ofproto, port = 2, src = "70:88:99:00:00:02", dst = "00:00:00:00:00:02" )
        self.add_flow(datapath= datapath, priority = 1000, match = match_1, actions = actions_1)
        
        #Paquetes desde h2 a h1:
        match_2 = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP, ipv4_dst=('10.0.0.0', '255.255.255.0'))
        actions_2 = self.forwardActions(parser = parser, ofproto = ofproto, port = 1 , src = "70:88:99:00:00:01", dst = "00:00:00:00:00:01" )
        self.add_flow(datapath= datapath, priority = 1000, match = match_2, actions = actions_2)
        
        #Resto de paquetes:
        match_0 = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                        ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match_0, actions)

    def forwardActions(self, parser, ofproto, port, src, dst):
        return [
        #parser.OFPActionDecNwTtl(len = 1),
        parser.OFPActionSetField(eth_src=src),
        parser.OFPActionSetField(eth_dst=dst),
        parser.OFPActionDecNwTtl(),
        parser.OFPActionOutput(port),
        ]
    def dropActions(self, parser, ofproto):
        return [ ]
    

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                            actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)#
    def _packet_in_handler(self, ev):
        # If you hit this you might want to increase
        # the "miss_send_length" of your switch
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                            ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg
        datapath = msg.datapath #datapath indentifica el swith o router que envia el mensaje recibido por el controlador.
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)#devuelve una lista de protocolos de nivel de enlace (guarda 1a opcion)
        #pkt_ipv6 = pkt.get_protocol(ipv6.ipv6)#devuelve el primer miembro de la lista de protocolos que corresponden a ipv6.

        # if eth.ethertype == ether_types.ETH_TYPE_LLDP:
        #     #ethertype es un atributo de la clase ethernet que siempre es el mismo (0x0800)
        #     # ignore lldp packet
        #     return
        # if pkt_ipv6.ipv6 == ether_types.ETH_TYPE_IPV6 :
        #     # ignore ipv6 packet (0x86DD)
        #     return 

        dst = eth.dst
        src = eth.src

        dpid = format(datapath.id, "d").zfill(16)
        self.mac_to_port.setdefault(dpid, {})
        

        self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

        if eth.ethertype == ether_types.ETH_TYPE_IP:
            ip = pkt.get_protocol(ipv4.ipv4)
            protocol = ip.proto
            if protocol == in_proto.IPPROTO_ICMP:
                #No sabemos si la idea es que la primera vez se mande trafico ICMP con destino al propio switch
                # nos entre como "resto de trafico" y luego al procesarlo si es ICMP, añadamos una regla para que deahi en adelante
                #el switch sepa que hacer.
                # match_ICMP = parser.OFPMatch(eth_type= ether_types.ETH_TYPE_IP)
                # actions_ICMP = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                #                                 ofproto.OFPCML_NO_BUFFER)]
                # self.add_flow(datapath, 5000, match_ICMP, actions_ICMP)
                self._handle_icmp(datapath=datapath, port= in_port, pkt_original= pkt)


    def _handle_icmp(self, datapath, port, pkt_original):
        pkt_ethernet = pkt_original.get_protocol(ethernet.ethernet)
        pkt_ipv4 = pkt_original.get_protocol(ipv4.ipv4) #Nos devuelve el tipo de protocolo y ademas campos de la cabecera.
        pkt_icmp = pkt_original.get_protocol(icmp.icmp)

        if pkt_icmp.type != icmp.ICMP_ECHO_REQUEST:
            return
        #Creamos el paquete ICMP_REPLY para responder al request.
        
        pkt = packet.Packet() #Creamos el paquete vacio.
        pkt.add_protocol(ethernet.ethernet(ethertype=pkt_ethernet.ethertype,
        dst=pkt_ethernet.src,src=pkt_ethernet.dst)) #Metemos cabecera ethernet en el paquete.

        pkt.add_protocol(ipv4.ipv4(dst=pkt_ipv4.src,src=pkt_ipv4.dst, # tambien pordria ser: pkt_ipv4.dst
        proto=pkt_ipv4.proto))

        pkt.add_protocol(icmp.icmp(type_=icmp.ICMP_ECHO_REPLY,code=icmp.ICMP_ECHO_REPLY_CODE,
        csum=0,data=pkt_icmp.data))

        self._send_packet(datapath, port, pkt)

    def _send_packet(self, datapath, port, pkt):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        pkt.serialize()# codificamos todo el paquete entero (sin prev porque codificamos a trozos).
        self.logger.info("packet-out %s" % (pkt,))
        data = pkt.data
        actions = [parser.OFPActionOutput(port=port)] # que tendra que hacer el switch cuando le llegue el paquete.
        out = parser.OFPPacketOut(datapath=datapath, # Es para ordenar al switch que mande el paquete que nosotros le mandemos.
        buffer_id=ofproto.OFP_NO_BUFFER,in_port=ofproto.OFPP_CONTROLLER,
        actions=actions,data=data)
        datapath.send_msg(out) #mandamos al switch del que nos ha llegado el REQUEST el paquete que queremos que el switch reenvie.   
