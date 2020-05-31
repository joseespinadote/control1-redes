#!/usr/bin/env python3
'''
# Script para el control 1 de redes, primer semestre 2020
por José Espina (joseguillermoespina@gmail.com)

El script permite crear un id de cliente, descargar (arbitrariamente) el archivo "control1.pdf", y
continuar la descarga en caso de detener el cliente

# Modo de uso:
 1) Ejecutar el servidor

 $ ./control1

 Si todo marcha bien, el sistema operativo le asignará un puerto. Por stdout verá un mensaje similar al siguiente:
 "Servidor funcionando en 127.0.0.1:59286"

 2) Solicitar un id único de cliente a través de una petición GET. Ejemplo, usando cURL

 $ curl 127.0.0.1:59286

 Retornará por stout un identificador único. Por ejemplo: 98ff9a06-6707-4c17-b215-a6eb51639193

 3) Hacer nuevamente una solitud http GET con curl en la dirección que aparece por stdout en el primer paso,
 más el identificador del paso anterior, como en el ejemplo a continuación

 $ curl 127.0.0.1:59424/98ff9a06-6707-4c17-b215-a6eb51639193 --output archivo.parte1

 3.1) Antes de que termine la descarga, cancelar el curl con Control-C

 4) Continuar la descarga con curl, especificando otro nombre de archivo, para evitar sobre escribir el primero

 $ curl 127.0.0.1:59424/98ff9a06-6707-4c17-b215-a6eb51639193 --output archivo.parte2

 5) Concatenar los dos archivos en un tercero para comprobar que la descarga fue exitosa

 $ cat archivo.parte1 archivo.parte2 > archivo.pdf

'''
import os
import argparse
import socket
import sys
import socketserver
import threading
import uuid
import time
from datetime import datetime
from time import mktime

# Constantes globales
BUFFER_ENTRADA = 128
TAMANO_PEDAZOS = 512
TAMANO_UUID = 36
RUTA_ARCHIVO_SERVIDO = 'word.doc'
DICT_RESPUESTAS_HTTP = {200: "HTTP/1.1 200 OK\n",
                        400: "HTTP/1.1 400 Bad Request\n",
                        403: "HTTP/1.1 403 Forbidden\n",
                        404: "HTTP/1.1 404 Not Found\n"}

# Variables globales
dict_cliente_progeso = dict()


class Control_uno_handler(socketserver.BaseRequestHandler):

    def genera_cabeceras(self, codigo, tamanio_respuesta_bytes, binario=False):
        now = datetime.now()
        stamp = mktime(now.timetuple())
        str_headers = DICT_RESPUESTAS_HTTP[codigo]
        str_headers += "Date: " + str(format_date_time(stamp)) + "\n"
        str_headers += "Server: ~el joServer 'the espinator'~ v0.1\n"
        str_headers += "Last-Modified: " + str(format_date_time(stamp)) + "\n"
        str_headers += "Accept-Ranges: bytes\n"
        str_headers += "Content-Length: "+str(tamanio_respuesta_bytes)+"\n"
        str_headers += "Cache-Control: max-age=0\n"
        str_headers += "Expires: " + str(format_date_time(stamp)) + "\n"
        if binario:
            str_headers += "Content-Type: application/octet-stream\n"
        else:
            str_headers += "Content-Type: text/plain\n"
        str_headers += "\n"
        return str_headers

    def handle(self):
        data = self.request.recv(BUFFER_ENTRADA)
        str_data = data.decode('utf-8')
        # Si la solicitud no es GET: error 403 (prohibido)
        if not str_data.startswith('GET /'):
            headers = self.genera_cabeceras(403, 0)
            self.request.send(str.encode(headers))
            return
        # Si no viene id unico de cliente, se asume que un cliente está pidiendo uno
        if str_data[5] == ' ':
            cliente_id = str.encode(str(uuid.uuid4()))
            # Si el id unico de cliente no existe: error 404 (no encontrado)
            if cliente_id not in dict_cliente_progeso.keys():
                headers = self.genera_cabeceras(404, 0)
                self.request.send(str.encode(headers))
                return
            headers = self.genera_cabeceras(200, TAMANO_UUID, False)
            self.request.send(str.encode(headers))
            self.request.send(cliente_id)
            return
        # Si viene id de cliente, y está en el diccionario, entonces es porque
        # se quiere retomar una descarga
        else:
            cliente_id = str_data[5:5+TAMANO_UUID]
            progreso = dict_cliente_progeso[cliente_id] if cliente_id in dict_cliente_progeso.keys(
            ) else 0
            filename = RUTA_ARCHIVO_SERVIDO
            total = os.path.getsize(RUTA_ARCHIVO_SERVIDO)
            total_sent = progreso
            with open(filename, 'rb') as output:
                output.seek(progreso)
                str_headers = "HTTP/1.1 200 OK\n"
                str_headers += "Date: Sat, 30 May 2020 04:55:14 GMT\n"
                str_headers += "Server: Apache/2.4.10\n"
                str_headers += "Last-Modified: Wed, 02 Aug 2017 12:44:32 GMT\n"
                str_headers += "Accept-Ranges: bytes\n"
                str_headers += "Content-Length: "+str(100352-progreso)+"\n"
                str_headers += "Cache-Control: max-age=0\n"
                str_headers += "Expires: Sat, 30 May 2020 04:55:14 GMT\n"
                str_headers += "Content-Type: application/octet-stream\n\n"
                self.request.send(str.encode(str_headers))
                while True:
                    data = output.read(TAMANO_PEDAZOS)
                    #data = output.read()
                    if not data:
                        del dict_cliente_progeso[cliente_id]
                        break
                    try:
                        self.request.send(data)
                    except ConnectionResetError:
                        print('El cliente {} alcanzó a descargar {} bytes'.format(
                            cliente_id, dict_cliente_progeso[cliente_id]))
                        return
                    total_sent += len(data)
                    dict_cliente_progeso[cliente_id] = total_sent
                    print('{} de {} bytes enviados'.format(total_sent, total),
                          sep=' ', end='\r', flush=True)
                    time.sleep(0.05)
                print('')
        return


def server():
    address = ('localhost', 0)
    servidor = socketserver.TCPServer(address, Control_uno_handler)
    ip, port = servidor.server_address  # what port was assigned?
    print('Servidor funcionando en {ip}:{puerto}'.format(ip=ip, puerto=port))
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        servidor.shutdown()
        servidor.socket.close()


if __name__ == '__main__':
    server()
