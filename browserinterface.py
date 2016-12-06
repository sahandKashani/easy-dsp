#!/usr/local/bin/python

from ws4py.client.threadedclient import WebSocketClient
from wsgiref.simple_server import make_server
from ws4py.websocket import WebSocket
from ws4py.server.wsgirefserver import WSGIServer, WebSocketWSGIRequestHandler
from ws4py.server.wsgiutils import WebSocketWSGIApplication
from threading import Thread
from Queue import Queue
import os
import json
import sys
import socket
import json
import datetime
import numpy as np

r_messages = Queue()
r_id = 0
handle_data = 0
when_new_config = 0

def register_handle_data(fn):
    global handle_data
    handle_data = fn

def register_when_new_config(fn):
    global when_new_config
    when_new_config = fn

class DataHandler():
    def __init__(self, id):
        self.id = id

    def send_data(self, data):
        r_messages.put(json.dumps({'dataHandler': self.id, 'data': data}))

# name: name of the graph
# type: type of the graphs: 'base:graph:area', 'base:graph:line', 'base:graph:bar', 'base:graph:scatterplot'
# parameters: parameters of the graph. Typically: {xName: "name of the x axis", seriesNames: ["serie 1", "serie 2", "serie 3"] }
# returns: a Graph object
def add_handler(name, type, parameters):
    global r_id
    r_id = r_id + 1
    r_messages.put(json.dumps({'addHandler': name, 'id': r_id, 'type': type, 'parameters': parameters}))
    return DataHandler(r_id)

rate = -1
channels = 0
buffer_frames = -1
volume = -1

# The following variables are used to measure the latency
## Date we began to receive audio stream
bi_audio_start = None
## Number of audio messages we received so far
bi_audio_number = 0

bi_buffer = 0

bi_recordings = []
# duration in ms
def record_audio(duration, callback):
    global bi_recordings
    bi_recordings.append({'duration': duration, 'callback': callback, 'buffer': np.empty([0, channels], dtype=np.int16), 'ended': False})

def handle_recordings():
    global bi_recordings
    for i in reversed(range(len(bi_recordings))):
        recording = bi_recordings[i]
        audio_duration = len(recording['buffer'])*1000/rate
        if audio_duration >= recording['duration']:
            recording['ended'] = True
            recording['callback'](recording['buffer'])
            del bi_recordings[i]

class StreamClient(WebSocketClient):
    def received_message(self, m):
        global bi_audio_start
        global bi_audio_number
        global bi_recordings
        global bi_buffer
        if not m.is_binary:
            print m
            global rate
            global channels
            global buffer_frames
            global volume
            bi_audio_start = None
            bi_audio_number = 0
            m = json.loads(m.data)
            rate = m['rate']
            channels = m['channels']
            buffer_frames = m['buffer_frames']
            volume = m['volume']
            bi_buffer = np.zeros((buffer_frames, channels), dtype=np.int16)
            for recording in bi_recordings:
                recording['buffer'] = np.empty([0, channels], dtype=np.int16)
            if when_new_config != 0:
                when_new_config(buffer_frames, rate, channels, volume)
        else:
            # For measuring the latency
            if bi_audio_start == None:
                bi_audio_start = datetime.datetime.now()

            time_diff = datetime.datetime.now() - bi_audio_start
            time_elapsed = time_diff.total_seconds()*1000 # in milliseconds
            audio_received = bi_audio_number*buffer_frames*1000/rate
            audio_delay = time_elapsed - audio_received
            r_messages.put(json.dumps({'latency': audio_delay}))
            bi_audio_number += 1

            data = bytearray()
            data.extend(m.data)
            i = 0
            i_frame = 0
            i_channel = 0
            for i in range(len(data) / 2): # we work with 16 bits = 2 bytes
                if data[2*i+1] <= 127:
                    bi_buffer[i_frame][i_channel] = data[2*i] + 256*data[2*i+1]
                else:
                    bi_buffer[i_frame][i_channel] = (data[2*i+1]-128)*256 + data[2*i] - 32768
                i_channel += 1
                if (i % channels) == (channels-1):
                    i_channel = 0
                    i_frame += 1
            for recording in bi_recordings:
                if not recording['ended']:
                    recording['buffer'] = np.concatenate((recording['buffer'], bi_buffer))
            handle_recordings()
            if handle_data != 0:
                handle_data(bi_buffer)

def send_audio(buffer):
    if client != -1:
        try:
            nbuffer = []
            for i in range(len(buffer)):
                if buffer[i] >= 0:
                    nbuffer.append(min(buffer[i]%256, 255))
                    nbuffer.append(min(buffer[i]/256, 255))
                else:
                    t = max(0, 32768 + buffer[i])
                    nbuffer.append(min(t%256, 255))
                    nbuffer.append(min(t/256 + 128, 255))
            client.send(bytearray(nbuffer), True)
        except socket.error, e:
            print "autre erreur11"
        except IOError, e:
            print "exception11"

client = -1
standalone = False

class WSServer(WebSocket):
    def opened(self):
        global client
        client = self
        while True:
            self.send(r_messages.get(), False)
            r_messages.task_done()

    def close(self, code, reason):
        global client
        global server
        global ws
        sys.stderr.write("1.1\n")
        client = -1
        os._exit(1)

def start_server(port):
    global server
    server = make_server('', port, server_class=WSGIServer,
                         handler_class=WebSocketWSGIRequestHandler,
                         app=WebSocketWSGIApplication(handler_cls=WSServer))
    server.initialize_websockets_manager()
    server.serve_forever()

class PythonDaemonClient(WebSocketClient):
    def opened(self):
        self.send(json.dumps({'script': 9001}))
        self.close()

def inform_browser():
    python_daemon = PythonDaemonClient('ws://127.0.0.1:7320/', protocols=['http-only', 'chat'])
    python_daemon.connect()


def start_client():
    ws = StreamClient('ws://192.168.1.151:7321/', protocols=['http-only', 'chat'])
    ws.connect()

    ws.run_forever()

def start():
    serverThread = Thread(target = start_server, args = (9001, ))
    serverThread.start()

    if standalone:
        inform_browser()

    clientThread = Thread(target = start_client)
    clientThread.start()
