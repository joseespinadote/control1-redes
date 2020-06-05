#!/usr/bin/env python3
'''

Script Python 3 para el Control 1 de Redes,
Primer semestre 2020,
Creado por José Espina (joseguillermoespina@gmail.com)

**Ver el informe (control1.pdf) para hacerlo funcionar**

Consideraciones:

 - Se añadieron comentarios para mejorar la comprensión del script
 - La explicación de qué hace cada parte del código, variables y 
   constantes globales, se encuentran en el informe
'''
# "os" se usó para obtener metadata del archivo a enviar al cliente
import os
# "socketserver" librería del framework nativo de python para levantar
# un servidor socket (single thread) y hacer "override" de sus los
# métodos de las clases pre-fabricadas para levantar servicios sobre
# UDP y TCP muy rapidamente
import socketserver
# "threading" no se usa en esta versión. Pero se deja comentario para
# el caso que se quiera implementar un servidor multi-thread, que permi-
# tirá atender a varios clientes de manera simultánea
import threading
# "uuid" se usó para generar el id único de cliente
import uuid
# "time" se usó para ralentizar la transferencia del envío de "chunks"
# de datos con "sleep". Da tiempo de alcanzar a "botar" al cliente con
# control-c con fines de experimentación
import time
# "mimetypes" permite extraer el texto descriptivo para se usado en
# la cabecera "Content-type" y cumplir con HTTP 1.1
import mimetypes
# "format_date_time" y "mktime" permiten representar la fecha en formato
# del RFC 1123
from wsgiref.handlers import format_date_time
from time import mktime
# "datetime" se usa para obtener la fecha de ahora
from datetime import datetime

# Definción de constantes globales
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
    address = ('localhost', 0)
    # Comentar la línea anterior y descomentar la siguiente
    # para dejar el puerto fijo en 9999 (si es que sistema
    # operativo lo permite)
    #address = ('localhost', 9999)

    # Se configura el seridor y se pasa clase handler que
    # hereda de socketserver.BaseRequestHandler
    servidor = socketserver.TCPServer(address, Control_uno_handler)
    ip, port = servidor.server_address
    print('Servidor funcionando en {ip}:{puerto}'.format(ip=ip, puerto=port))

    # Experimental: para probar atender múltiples clientes
    # descimentar las líneas a continuación, y comentar
    # el resto del script

    # t = threading.Thread(target=servidor.serve_forever)
    # t.setDaemon(True)
    # t.start()

    # El servidor "servirá" para siempre, hasta que se le detenga
    # con un ctrl + c
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        servidor.shutdown()
        servidor.socket.close()
