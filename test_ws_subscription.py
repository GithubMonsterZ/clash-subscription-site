"""Offline transport validation; run with python -m unittest test_ws_subscription."""
import copy
import unittest
from build import vless_node

class WebSocketContract(unittest.TestCase):
    def setUp(self):
        self.node = {'type':'vless','server':'example.com','port':8443,
                     'uuid':'6f8bcb7c-47fb-47cb-bdda-fb5ba0a03de1','network':'ws','tls':True,
                     'skip-cert-verify':False,'servername':'example.com','alpn':['http/1.1'],
                     'ws-opts':{'path':'/demo/stream','headers':{'Host':'example.com'}}}
    def test_transport_and_certificate_validation_survive_export(self):
        self.assertEqual(vless_node(self.node,'target'),dict(self.node,name='target'))
    def test_reject_invalid_or_insecure_websocket_settings(self):
        for change in [{'skip-cert-verify':True},{'flow':'xtls-rprx-vision'},
                       {'reality-opts':{}},{'port':True},{'port':204444},
                       {'servername':'other.example.com'},{'alpn':['h2']},
                       {'ws-opts':{'path':'/demo','headers':{'Host':'other.example.com'}}},
                       {'ws-opts':{'path':'demo','headers':{'Host':'example.com'}}}]:
            with self.subTest(change=change):
                node=copy.deepcopy(self.node);node.update(change)
                with self.assertRaises(ValueError):vless_node(node,'target')
if __name__=='__main__':unittest.main()
