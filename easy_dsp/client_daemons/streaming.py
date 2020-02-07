# ##############################################################################
# streaming.py
# ============
# Streaming module to get live samples from the Pyramic. This must be used in
# conjunction with the board_daemons/ programs.
# This file is based on the original variant from easy-dsp, but with much of the
# unneeded parts removed and optimized.
#
# Author: Sepand KASHANI [kashani.sepand@gmail.com]
# ##############################################################################

import json
import queue
import threading

import numpy as np

import ws4py.client.threadedclient as threadedclient


## Configuration ###############################################################
EASY_DSP_BOARD_IP_ADDRESS = None  # default Pyramic IP address (as a string)
(EASY_DSP_WSAUDIO_SERVER_PORT, EASY_DSP_WSCONFIG_SERVER_PORT) = (None, None)
(sample_rate, channel_count, frame_count, volume) = (None, None, None, None)

## Global Variables ############################################################
audio_buffer = None  # buffer containing audio samples
q_callback = queue.Queue()
(process_samples, process_config) = (None, None)  # callback functions

## User-callable Functions #####################################################
def change_config(args=None):
    """
    Send the configuration variables to the microphone array.

    Parameters
    ----------
    args
        Leave unspecified an `None`.
        It is due to the way loop_callbacks() works.
    """

    class WSConfigClient(threadedclient.WebSocketClient):
        def opened(self):
            config = json.dumps({'rate': sample_rate,
                                 'channels': channel_count,
                                 'buffer_frames': frame_count,
                                 'volume': volume})
            self.send(config)
            self.close()

    connect_line = 'ws://{EASY_DSP_BOARD_IP_ADDRESS}:{EASY_DSP_WSCONFIG_SERVER_PORT}/'
    ws_config = WSConfigClient(connect_line, protocols=['http-only', 'chat'])
    ws_config.connect()


def start():
    def start_client():
        connect_line = f'ws://{EASY_DSP_BOARD_IP_ADDRESS}:{EASY_DSP_WSAUDIO_SERVER_PORT}/'
        ws_client = StreamClient(connect_line, protocols=['http-only', 'chat'])
        ws_client.connect()
        ws_client.run_forever()

    th_client = threading.Thread(target=start_client)
    th_client.daemon = True
    th_client.start()


def loop_callbacks():
    global q_callback
    while True:
        (func, args) = q_callback.get()
        func(*args)
        q_callback.task_done()


class StreamClient(threadedclient.WebSocketClient):
    def received_message(self, message):
        global q_callback, audio_buffer
        if not message.is_binary:  # new configuration
            global sample_rate, channel_count, frame_count, volume

            msg = json.loads(message.data)
            sample_rate = msg['rate']
            channel_count = msg['channels']
            frame_count = msg['buffer_frames']
            volume = msg['volume']

            audio_buffer = np.zeros((frame_count, channel_count), dtype=np.int16)
            if process_config:
                q_callback.put((process_config, (None,)))

        else:  # new audio data
            raw_data = np.frombuffer(message.data, dtype=np.int16)
            audio_buffer = raw_data.reshape(-1, channel_count)

            if process_samples:
                q_callback.put((process_samples, (audio_buffer,)))
