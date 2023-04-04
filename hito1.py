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
        switch = self.addSwitch('s1', protocols = 'OpenFlow13')
        h1 = self.addHost('h1', mac = '00:00:00:00:00:01',ip = '10.0.0.2', cls = MyHost, (ip_dest,mac_dest))
        h2 = self.addHost('h2', mac = '00:00:00:00:00:02', ip = '10.0.1.2')
        self.addLink(h1, switch)
        self.addLink(h2, switch)

class MyHost(Host):
    def config(self, (ip_dest,mac_dest), **params):
        host = super(MyHost, self).config(**params)
        host.setARP(ip = ip_dest, mac = mac_dest)
        return host


def simpleTestCLI():
    topo = SingleSwitchTopo(2)
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



