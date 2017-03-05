# ######################################################################################################################
# streaming.py
# ============
# Streaming module to get live samples from the Pyramic. This must be used in conjunction with the board_daemons/ programs.
# This file is based on the original variant from easy-dsp, but with much of the unneeded parts removed and optimized.
#
# Author        : Sepand KASHANI [sep@zurich.ibm.com]
# Revision      : 1.0
# Last modified : 2017.03.03
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
            # # Raw sign-and-magnitude data
            # sign_magnitude_data = np.frombuffer(message.data, dtype=np.int16).reshape(-1, channel_count)
            #
            # # Extract (sign,magnitude) pairs
            # sign_mask = np.array([1 << 15], dtype=np.int16)
            # magnitude_mask = np.bitwise_not(sign_mask)
            # (negative_sign, magnitude) = (np.bitwise_and(sign_mask, sign_magnitude_data) != 0,
            #                               np.bitwise_and(magnitude_mask, sign_magnitude_data))
            #
            # # Reconstruct raw data in two's complement format
            # twos_complement_data = np.zeros_like(sign_magnitude_data)
            # np.power(-1, negative_sign,
            #          out=twos_complement_data)  # use 'out=twos_complement_data' to guarantee the result stays on 16 bits.
            # twos_complement_data *= magnitude
            #
            # audio_buffer = twos_complement_data

            raw_data = np.frombuffer(message.data, dtype=np.uint8)
            (lsb, msb) = (raw_data[np.r_[0:len(raw_data):2]].astype(np.int16),
                          raw_data[np.r_[1:len(raw_data):2]].astype(np.int16))
            is_negative = (msb >= 128)
            zeta = (np.bitwise_and(msb, 0x7F) << 8) + lsb
            zeta[is_negative] -= 2 ** 15

            zeta = zeta.reshape(-1, channel_count)

            audio_buffer = zeta

            # data = bytearray()
            # data.extend(message.data)
            # i_frame = 0
            # i_channel = 0
            #
            # for i in range(len(data) // 2):  # we work with 16 bits = 2 bytes
            #     if data[2 * i + 1] <= 127:
            #         audio_buffer[i_frame][i_channel] = data[2 * i] + 256 * data[2 * i + 1]
            #     else:
            #         audio_buffer[i_frame][i_channel] = (data[2 * i + 1] - 128) * 256 + data[2 * i] - 32768
            #     i_channel += 1
            #     if (i % channel_count) == (channel_count - 1):
            #         i_channel = 0
            #         i_frame += 1
            #
            # print(np.all(zeta == audio_buffer))

            if process_samples:
                callback_queue.put((process_samples, (audio_buffer,)))
