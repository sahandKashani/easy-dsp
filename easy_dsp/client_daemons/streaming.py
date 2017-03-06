# ######################################################################################################################
# streaming.py
# ============
# Streaming module to get live samples from the Pyramic. This must be used in conjunction with the board_daemons/ programs.
# This file is based on the original variant from easy-dsp, but with much of the unneeded parts removed and optimized.
#
# Author        : Sepand KASHANI [sep@zurich.ibm.com]
# ######################################################################################################################

import json
from queue import Queue
from threading import Thread

import numpy as np
from ws4py.client.threadedclient import WebSocketClient

### Configuration ######################################################################################################
EASY_DSP_BOARD_IP_ADDRESS = None  # default Pyramic IP address (as a string)
(EASY_DSP_WSAUDIO_SERVER_PORT, EASY_DSP_WSCONFIG_SERVER_PORT) = (None, None)
(sample_rate, channel_count, frame_count, volume) = (None, None, None, None)

### Global Variables ###################################################################################################
audio_buffer = None  # buffer containing audio samples
callback_queue = Queue()
(process_samples, process_config) = (None, None)  # callback functions

### User-callable Functions ############################################################################################
def change_config(args=None):
    """
    Send the configuration variables to the microphone array.
    :param args: leave this argument empty. It is due to the way loop_callbacks() works.
    :return:
    """

    class WSConfigClient(WebSocketClient):
        def opened(self):
            self.send(
                json.dumps({'rate': sample_rate,
                            'channels': channel_count,
                            'buffer_frames': frame_count,
                            'volume': volume}))
            self.close()

    connection_line = 'ws://{ip}:{port}/'.format(ip=EASY_DSP_BOARD_IP_ADDRESS, port=EASY_DSP_WSCONFIG_SERVER_PORT)
    change_config_q = WSConfigClient(connection_line, protocols=['http-only', 'chat'])
    change_config_q.connect()


def start():
    def start_client():
        connection_line = 'ws://{ip}:{port}/'.format(ip=EASY_DSP_BOARD_IP_ADDRESS, port=EASY_DSP_WSAUDIO_SERVER_PORT)
        ws = StreamClient(connection_line, protocols=['http-only', 'chat'])
        ws.connect()
        ws.run_forever()

    client_thread = Thread(target=start_client)
    client_thread.daemon = True
    client_thread.start()


def loop_callbacks():
    global callback_queue
    while True:
        (func, args) = callback_queue.get()
        func(*args)
        callback_queue.task_done()

########################################################################################################################

class StreamClient(WebSocketClient):
    def received_message(self, message):
        global callback_queue, audio_buffer
        if not message.is_binary:  # new configuration
            global sample_rate, channel_count, frame_count, volume

            msg = json.loads(message.data)
            sample_rate = msg['rate']
            channel_count = msg['channels']
            frame_count = msg['buffer_frames']
            volume = msg['volume']

            audio_buffer = np.zeros((frame_count, channel_count), dtype=np.int16)
            if process_config:
                callback_queue.put((process_config, (None,)))

        else:  # new audio data
            # Raw sign-and-magnitude data
            raw_data = np.frombuffer(message.data, dtype=np.uint8)
            # Reconstruct raw data in two's complement format
            (lsb, msb) = (raw_data[np.r_[0:len(raw_data):2]].astype(np.int16),
                          raw_data[np.r_[1:len(raw_data):2]].astype(np.int16))
            is_negative = (msb >= 128)
            audio_buffer = (np.bitwise_and(msb, 0x7F) << 8) + lsb
            audio_buffer[is_negative] -= 32768  # 2**15
            audio_buffer = audio_buffer.reshape(-1, channel_count)

            if process_samples:
                callback_queue.put((process_samples, (audio_buffer,)))
