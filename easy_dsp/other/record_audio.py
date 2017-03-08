# ######################################################################################################################
# record_audio.py
# ===============
# Get live audio from the Pyramic and save as a WAV file
#
# Author        : Sepand KASHANI [sep@zurich.ibm.com]
# ######################################################################################################################

import argparse
import os
import sys
from queue import Queue
from threading import Thread

import numpy as np
from scipy.io import wavfile

from easy_dsp.client_daemons import streaming as stream
from pypeline.radioAstronomy.utils.progressMonitor import printProgress

### Pyramic Configuration: these must be kept in sync with browser-config.h ############################################
EASY_DSP_VOLUME = 100
EASY_DSP_NUM_CHANNELS = 48
EASY_DSP_AUDIO_FREQ_HZ = 48000
EASY_DSP_AUDIO_FORMAT_BITS = 16
EASY_DSP_AUDIO_FORMAT_BYTES = EASY_DSP_AUDIO_FORMAT_BITS // 8
EASY_DSP_AUDIO_BUFFER_LENGTH_MS = 200
EASY_DSP_AUDIO_BUFFER_SIZE_BYTES = int((EASY_DSP_NUM_CHANNELS * EASY_DSP_AUDIO_FREQ_HZ * EASY_DSP_AUDIO_FORMAT_BYTES * \
                                        (EASY_DSP_AUDIO_BUFFER_LENGTH_MS / 1000.0)))
########################################################################################################################


def parseArgs():
    """
    Parse command-line arguments.

    :return: dictionary of valid arguments
    """
    printProgress()

    parser = argparse.ArgumentParser(
        description="""
Record a live audio stream from the Pyramic and save it to a WAV file.
            """,
        epilog="""
Example usage: python3 record_audio.py --duration 10
                                       --outputFile /home/sep/Desktop/out.wav
            """,
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('--duration', type=int, required=True, help='Duration of the recording. [seconds]')
    parser.add_argument('--outputFile', type=str, required=True, help='File in which the audio stream is saved.')

    args = vars(parser.parse_args())
    args['outputFile'] = os.path.abspath(args['outputFile'])
    return args


def configure_live_stream(sample_queue):
    def run(sample_queue):
        # streaming.py Settings
        stream.EASY_DSP_BOARD_IP_ADDRESS = '10.42.0.2'
        stream.EASY_DSP_WSAUDIO_SERVER_PORT = 7321
        stream.EASY_DSP_WSCONFIG_SERVER_PORT = 7322
        stream.sample_rate = EASY_DSP_AUDIO_FREQ_HZ
        stream.channel_count = EASY_DSP_NUM_CHANNELS
        stream.frame_count = EASY_DSP_AUDIO_BUFFER_SIZE_BYTES // (EASY_DSP_NUM_CHANNELS * EASY_DSP_AUDIO_FORMAT_BYTES)
        stream.volume = EASY_DSP_VOLUME

        def handle_samples(buffer):
            # printProgress(
            #     "handle_buffer: received {count} bytes | shape {shape} | type {dtype}".format(count=buffer.nbytes,
            #                                                                                   shape=buffer.shape,
            #                                                                                   dtype=buffer.dtype))
            sample_queue.put(buffer)

        def handle_config(args=None):
            printProgress("handle_config: new config ({frames},{sampleRate},{channelCount},{volume})".format(
                frames=stream.frame_count,
                sampleRate=stream.sample_rate,
                channelCount=stream.channel_count,
                volume=stream.volume))

        stream.change_config()
        stream.process_samples = handle_samples
        stream.process_config = handle_config
        stream.start()
        stream.loop_callbacks()

    streaming_thread = Thread(target=run, name='sample-stream', args=(sample_queue,), daemon=True)
    return streaming_thread


if __name__ == '__main__':
    args = parseArgs()

    sample_queue = Queue()
    streaming_thread = configure_live_stream(sample_queue)
    streaming_thread.start()

    buffers_to_accumulate = np.ceil(args['duration'] / (EASY_DSP_AUDIO_BUFFER_LENGTH_MS / 1000))
    past_buffers = []
    while len(past_buffers) != buffers_to_accumulate:
        samples = sample_queue.get()
        past_buffers += [samples]

    recording = np.concatenate(past_buffers, axis=0)
    wavfile.write(args['outputFile'], EASY_DSP_AUDIO_FREQ_HZ, recording)

    # Needed because Thread('sample-stream') is on an infinite loop. (This is by construction of streaming.py.)
    sys.exit()
