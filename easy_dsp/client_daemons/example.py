# ##############################################################################
# example.py
# ==========
# Minimum building block to get the audio stream from a Pyramic
#
# Author: Sepand KASHANI [kashani.sepand@gmail.com]
# ##############################################################################

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
################################################################################

### streaming.py Settings ######################################################
streaming.EASY_DSP_BOARD_IP_ADDRESS = '10.42.0.2'
streaming.EASY_DSP_WSAUDIO_SERVER_PORT = 7321
streaming.EASY_DSP_WSCONFIG_SERVER_PORT = 7322
streaming.sample_rate = EASY_DSP_AUDIO_FREQ_HZ
streaming.channel_count = EASY_DSP_NUM_CHANNELS
streaming.frame_count = EASY_DSP_AUDIO_BUFFER_SIZE_BYTES // (EASY_DSP_NUM_CHANNELS * EASY_DSP_AUDIO_FORMAT_BYTES)
streaming.volume = EASY_DSP_VOLUME
################################################################################

### Define Callbacks ###########################################################
def handle_samples(buffer):
    """
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

def handle_config(args=None):
    msg = ('handle_config: new_config=('
           f'{streaming.frame_count}, '
           f'{streaming.sample_rate}, '
           f'{streaming.channel_count}, '
           f'{streaming.volume})')
    print(msg)
################################################################################


if __name__ == '__main__':
    streaming.change_config()
    streaming.process_samples = handle_samples
    streaming.process_config = handle_config
    streaming.start()
    streaming.loop_callbacks()
