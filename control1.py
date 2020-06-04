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
import mimetypes
# para representar la fecha RFC 1123
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime

# Constantes globales
BUFFER_ENTRADA = 256
TAMANO_PEDAZOS = 512
TAMANO_UUID = 36
DICT_RESPUESTAS_HTTP = {200: "HTTP/1.1 200 OK\n",
                        400: "HTTP/1.1 400 Bad Request\n",
                        403: "HTTP/1.1 403 Forbidden\n",
                        404: "HTTP/1.1 404 Not Found\n"}

# Variables globales
dict_cliente_progeso = dict()


class Control_uno_handler(socketserver.BaseRequestHandler):

    def genera_cabeceras(self, codigo, tamanio_respuesta_bytes, content_type="text/plain"):
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
        str_headers += "Content-Type: " + content_type + "\n"
        str_headers += "\n"
        return str_headers

    def handle(self):
        data = self.request.recv(BUFFER_ENTRADA)
        str_data = data.decode('utf-8')

        # Se comprueba si la llamada es de tipo GET
        if not str_data.startswith('GET /'):
            headers = self.genera_cabeceras(403, 0)
            self.request.send(str.encode(headers))
            return

        # Cuando no viene el id de cliente
        if str_data[5] == ' ':
            str_cliente_id = str(uuid.uuid4())
            cliente_id = str.encode(str_cliente_id)
            dict_cliente_progeso[str_cliente_id] = 0
            headers = self.genera_cabeceras(200, TAMANO_UUID)
            self.request.send(str.encode(headers))
            self.request.send(cliente_id)
            return

        # Si viene el id de cliente
        else:
            parametros_GET = str_data.split(" ")[1].split("/")
            cliente_id = parametros_GET[1]
            archivo = parametros_GET[2]
            tipo_contenido = mimetypes.guess_type(archivo)[0]
            total = os.path.getsize(archivo)

            if cliente_id not in dict_cliente_progeso.keys():
                headers = self.genera_cabeceras(404, 0)
                self.request.send(str.encode(headers))
                return

            progreso = dict_cliente_progeso[cliente_id]
            total_enviado = progreso
            with open(archivo, 'rb') as output:
                output.seek(progreso)
                str_headers = self.genera_cabeceras(
                    200, total-progreso, tipo_contenido)
                self.request.send(str.encode(str_headers))
                while True:
                    data = output.read(TAMANO_PEDAZOS)
                    if not data:
                        del dict_cliente_progeso[cliente_id]
                        break
                    try:
                        self.request.send(data)
                    except ConnectionResetError:
                        print('El cliente {} alcanzó a descargar {} bytes'.format(
                            cliente_id, dict_cliente_progeso[cliente_id]))
                        return
                    total_enviado += len(data)
                    dict_cliente_progeso[cliente_id] = total_enviado
                    print('{} de {} bytes enviados'.format(total_enviado, total),
                          sep=' ', end='\r', flush=True)
                    time.sleep(0.05)
                print('')
        return


if __name__ == '__main__':
    #address = ('localhost', 0)
    address = ('localhost', 9999)
    servidor = socketserver.TCPServer(address, Control_uno_handler)
    ip, port = servidor.server_address
    print('Servidor funcionando en {ip}:{puerto}'.format(ip=ip, puerto=port))
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        servidor.shutdown()
        servidor.socket.close()
