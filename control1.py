#!/usr/bin/env python3
'''
# Script para el control 1 de redes,
por José Espina (joseguillermoespina@gmail.com)
 
## Modo de uso:
 * Ejecutar netem como superusuario para simular pérdida de paquetes y retraso en la red
 tc qdisc add dev lo root netem loss 20.0% delay 0.5s
 * Ejecutar el servidor. Fijarse que el archivo a descargar exista
 ./control1 servidor ""
 * Hacer una solitud http GET con curl en la dirección que aparece por stdout en el paso anterior
 ejemplo: curl 127.0.0.1:9999
'''
import argparse
import socket
import logging
import sys
import socketserver
import threading

logging.basicConfig(level=logging.DEBUG)

class EchoRequestHandler(socketserver.BaseRequestHandler):

    def __init__(self, request, client_address, server):
        self.logger = logging.getLogger('EchoRequestHandler')
        self.logger.debug('__init__')
        socketserver.BaseRequestHandler.__init__(self, request,client_address,server)
        return

    def setup(self):
        self.logger.debug('setup')
        return socketserver.BaseRequestHandler.setup(self)

    def handle(self):
        self.logger.debug('handle')
        print(self.request.getpeername())
        # Echo the back to the client
        data = self.request.recv(128)
        str_data = data.decode('utf-8')
        print(str_data)
        print(str_data.startswith('GET /'))
        self.logger.debug('recv()->"%s"', data)
        self.request.send(data)
        return

    def finish(self):
        self.logger.debug('finish')
        return socketserver.BaseRequestHandler.finish(self)
    
class EchoServer(socketserver.TCPServer):

    def __init__(self, server_address, handler_class=EchoRequestHandler,):
        self.logger = logging.getLogger('EchoServer')
        self.logger.debug('__init__')
        socketserver.TCPServer.__init__(self, server_address, handler_class)
        return

    def server_activate(self):
        self.logger.debug('server_activate')
        socketserver.TCPServer.server_activate(self)
        return

    def serve_forever(self, poll_interval=0.5):
        self.logger.debug('waiting for request')
        self.logger.info(
            'Handling requests, press <Ctrl-C> to quit'
        )
        socketserver.TCPServer.serve_forever(self, poll_interval)
        return

    def handle_request(self):
        self.logger.debug('handle_request')
        return socketserver.TCPServer.handle_request(self)

    def verify_request(self, request, client_address):
        self.logger.debug('verify_request(%s, %s)',
                          request, client_address)
        return socketserver.TCPServer.verify_request(
            self, request, client_address,
        )

    def process_request(self, request, client_address):
        self.logger.debug('process_request(%s, %s)',
                          request, client_address)
        return socketserver.TCPServer.process_request(
            self, request, client_address,
        )

    def server_close(self):
        self.logger.debug('server_close')
        return socketserver.TCPServer.server_close(self)

    def finish_request(self, request, client_address):
        self.logger.debug('finish_request(%s, %s)',
                          request, client_address)
        return socketserver.TCPServer.finish_request(
            self, request, client_address,
        )

    def close_request(self, request_address):
        self.logger.debug('close_request(%s)', request_address)
        return socketserver.TCPServer.close_request(
            self, request_address,
        )

    def shutdown(self):
        self.logger.debug('shutdown()')
        return socketserver.TCPServer.shutdown(self)

def server(interface, port):
    address = ('localhost', 9999)  # let the kernel assign a port
    server = EchoServer(address, EchoRequestHandler)
    ip, port = server.server_address  # what port was assigned?
    print('servidor {ip}:{puerto}'.format(ip=ip, puerto=port))
    try :
        server.serve_forever()
    except KeyboardInterrupt :
        pass
    finally :
        server.shutdown()
        server.socket.close()
        print("Gracias!\n")

def client(host, port):
    pass

if __name__ == '__main__':
    choices = {'client': client, 'server': server}
    parser = argparse.ArgumentParser(description='Send and receive over TCP')
    parser.add_argument('role', choices=choices, help='which role to play')
    parser.add_argument('host', help='interface the server listens at;'
                        ' host the client sends to')
    parser.add_argument('-p', metavar='PORT', type=int, default=1060,
                        help='TCP port (default 1060)')
    args = parser.parse_args()
    function = choices[args.role]
    function(args.host, args.p)
