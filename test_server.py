"""Regression: browser preconnections must not block the page or its buttons."""
import socket
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from server import Handler

class ServerTests(unittest.TestCase):
    def test_idle_connection_does_not_block_page(self):
        service = ThreadingHTTPServer(('127.0.0.1',0),Handler)
        thread = threading.Thread(target=service.serve_forever,daemon=True)
        thread.start()
        idle = socket.create_connection(service.server_address,timeout=2)
        try:
            request = urllib.request.Request('http://127.0.0.1:'+str(service.server_port)+'/',headers={'Host':'127.0.0.1:8765'})
            with urllib.request.urlopen(request,timeout=2) as response:
                self.assertEqual(response.status,200)
                self.assertIn(b'Run comparison',response.read())
        finally:
            idle.close()
            service.shutdown()
            service.server_close()
            thread.join(timeout=2)
