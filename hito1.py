#!/usr/bin/env python3
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import Host
from mininet.log import setLogLevel
from mininet.cli import CLI

from mininet.node import RemoteController
from mininet.node import OVSSwitch
from functools import partial

class SingleSwitchTopo (Topo):
    def build(self, N=2):
        tupla_ip_mac_dest_1 = ("10.0.0.1", "70:88:99:00:00:01")
        tupla_ip_mac_dest_2 = ("10.0.1.1", "70:88:99:00:00:02")
        switch = self.addSwitch('s1', protocols = 'OpenFlow13')
        h1 = self.addHost('h1', mac = '00:00:00:00:00:01',ip = '10.0.0.2', cls = MyHost, arp = tupla_ip_mac_dest_1 )
        h2 = self.addHost('h2', mac = '00:00:00:00:00:02', ip = '10.0.1.2', cls = MyHost, arp = tupla_ip_mac_dest_2  )
        self.addLink(h1, switch)
        self.addLink(h2, switch)
# tupla_ip_mac_dest
# ip = tupla_ip_mac[0]
class MyHost(Host):
    def config(self, **params):#
        arp = params.pop("arp")
        host = super(MyHost, self).config(**params)
        host.setARP(ip = arp[0], mac = arp[1])
        return host


def simpleTestCLI():
    ##args = [tupla_ip_mac_dest_1, tupla_ip_mac_dest_2]
    #topo = SingleSwitchTopo(2, tupla_ip_mac_dest_1, tupla_ip_mac_dest_2)
    topo = SingleSwitchTopo()
    net = Mininet(topo, controller = partial(RemoteController, ip="127.0.0.1"))
    #partial en este caso devolvera el constructor de la clase RemoteController con los parametros que le especificamos
    #Entonces controller sera una llamada al constructor RemoteController que devolvera un objeto de la clase RemoteController
    net.start()
    CLI(net)
    net.stop()

if __name__ == '__main__':
    # Tell mininet to print useful information
    setLogLevel('info')
    simpleTestCLI()



