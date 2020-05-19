#!usr/bin/env python3
'''
# Script para el control 1 de redes,
por José Espina (joseguillermoespina@gmail.com)
 
## Modo de uso:
 * Primero, ejecutar el servidor. Fijarse que el archivo a descargar exista
./control1 servidor
 * Ejecutar netem para simular pérdida de paquetes
 <codigo netem aquii>
 * Ejecutar el cliente
./control1 cliente
'''
import argparse
import logging
import socket
import sys

# El servidor envía un archivo "hardcoded"
def servidor(puerto) :
    filename='control1.pdf'
    print("Sending:", filename)
    with open(filename, 'rb') as f:
        raw = f.read()
    # Send actual length ahead of data, with fixed byteorder and size
    self.sock.sendall(len(raw).to_bytes(8, 'big'))
    # You have the whole thing in memory anyway; don't bother chunking
    self.sock.sendall(raw)

# El ciente recibe el archivo en fragmentos
def cliente(puerto) :
    # Get the expected length (eight bytes long, always)
    expected_size = b""
    while len(expected_size) < 8:
        more_size = conn.recv(8 - len(expected_size))
        if not more_size:
            raise Exception("Short file length received")
        expected_size += more_size

    # Convert to int, the expected file length
    expected_size = int.from_bytes(expected_size, 'big')

    # Until we've received the expected amount of data, keep receiving
    packet = b""  # Use bytes, not str, to accumulate
    while len(packet) < expected_size:
        buffer = conn.recv(expected_size - len(packet))
        if not buffer:
            raise Exception("Incomplete file received")
        packet += buffer
    with open(filename, 'wb') as f:
        f.write(packet)
    
if __name__ == '__main__' :
    if sys.version_info.major !=3 :
        print("Este script funciona con python 3 o superior")
        sys.exit(-1)
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.DEBUG)
    choices = {'cliente': cliente, 'servidor':servidor}
    parser = argparse.ArgumentParser(description='Script para el control 1, por José Espina (joseguillermoespina@gmail.com)')
    parser.add_argument('role', choices=choices,help='Rol del script')
    parser.add_argument('-p',metavar='PORT', type=int, default=1060,help='Puerto (default 1060)')
    args=parser.parse_args()
    function=choices[args.role]
    function(args.p)
