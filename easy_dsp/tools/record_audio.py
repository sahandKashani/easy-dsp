# ##############################################################################
# record_audio.py
# ===============
# Get live audio from the Pyramic and save as a WAV file
#
# Author: Sepand KASHANI [kashani.sepand@gmail.com]
# ##############################################################################

import argparse
import pathlib
import queue
import sys
import threading

import numpy as np
import scipy.io.wavfile as wavfile

import easy_dsp.client_daemons.streaming as streaming


## Pyramic Configuration: these must be kept in sync with browser-config.h #####
EASY_DSP_VOLUME = 100
EASY_DSP_NUM_CHANNELS = 48
EASY_DSP_AUDIO_FREQ_HZ = 48000
EASY_DSP_AUDIO_FORMAT_BITS = 16
EASY_DSP_AUDIO_FORMAT_BYTES = EASY_DSP_AUDIO_FORMAT_BITS // 8
EASY_DSP_AUDIO_BUFFER_LENGTH_MS = 200
EASY_DSP_AUDIO_BUFFER_SIZE_BYTES = int((EASY_DSP_NUM_CHANNELS * EASY_DSP_AUDIO_FREQ_HZ * EASY_DSP_AUDIO_FORMAT_BYTES * \
                                        (EASY_DSP_AUDIO_BUFFER_LENGTH_MS / 1000.0)))


def parseArgs():
    """
    Parse command-line arguments.

    Returns
    -------
    args : dict
        duration : int
            Recording time [s]
        output : pathlib.Path
            Absolute file path
    """
    parser = argparse.ArgumentParser(description="Record a live audio stream from the Pyramic and save it to a WAV file.",
                                     epilog="Example: python3 record_audio.py --duration 10 ./out.wav",
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--duration',
                        type=int,
                        required=True,
                        help='Duration of the recording. [seconds]')
    parser.add_argument('output',
                        type=str,
                        required=True,
                        help='File in which the audio stream is saved.')

    args = parser.parse_args()
    args.output = pathlib.Path(args.output).expanduser().absolute()
    return vars(args)


def configure_stream_capture(q_samples):
    def run(q_samples):
        streaming.EASY_DSP_BOARD_IP_ADDRESS = '10.42.0.2'
        streaming.EASY_DSP_WSAUDIO_SERVER_PORT = 7321
        streaming.EASY_DSP_WSCONFIG_SERVER_PORT = 7322
        streaming.sample_rate = EASY_DSP_AUDIO_FREQ_HZ
        streaming.channel_count = EASY_DSP_NUM_CHANNELS
        streaming.frame_count = EASY_DSP_AUDIO_BUFFER_SIZE_BYTES // (EASY_DSP_NUM_CHANNELS * EASY_DSP_AUDIO_FORMAT_BYTES)
        streaming.volume = EASY_DSP_VOLUME

        def handle_samples(buffer):
            """
            Add incoming audio buffer to sample queue.

            Parameters
            ----------
            buffer : :py:class:`~numpy.ndarray`
                (N_sample, N_channel) audio packet
            """
            msg = ('handle_samples: '
                   f'received={buffer.nbytes} bytes, '
                   f'shape={buffer.shape}, '
                   f'type={buffer.dtype}')
            print(msg)
            q_samples.put(buffer)

        def handle_config(args=None):
            msg = ('handle_config: new_config=('
                   f'{streaming.frame_count}, '
                   f'{streaming.sample_rate}, '
                   f'{streaming.channel_count}, '
                   f'{streaming.volume})')
            print(msg)

        streaming.change_config()
        streaming.process_samples = handle_samples
        streaming.process_config = handle_config
        streaming.start()
        streaming.loop_callbacks()

    th_stream = threading.Thread(target=run,
                                 name='sample-stream',
                                 args=(q_samples,),
                                 daemon=True)
    return th_stream


if __name__ == '__main__':
    args = parseArgs()

    q_samples = queue.Queue()
    th_stream = configure_stream_capture(q_samples)
    th_stream.start()

    N_buffer = np.ceil(args['duration'] / (EASY_DSP_AUDIO_BUFFER_LENGTH_MS / 1000))
    buffers = []
    while len(buffers) != N_buffer:
        buffers.append(q_samples.get())
        q_samples.task_done()

    recording = np.concatenate(buffers, axis=0)
    wavfile.write(args['output'], EASY_DSP_AUDIO_FREQ_HZ, recording)

    sys.exit()  # Needed because `th_stream` is on an infinite loop
                # (by construction of streaming.py).
