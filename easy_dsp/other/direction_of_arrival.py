# ######################################################################################################################
# direction_of_arrival.py
# =======================
# Visualize the DoA on a real-time plot.
# ######################################################################################################################

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

### streaming.py Settings ##############################################################################################
stream.EASY_DSP_BOARD_IP_ADDRESS = '10.42.0.2'
stream.EASY_DSP_WSAUDIO_SERVER_PORT = 7321
stream.EASY_DSP_WSCONFIG_SERVER_PORT = 7322
stream.sample_rate = EASY_DSP_AUDIO_FREQ_HZ
stream.channel_count = EASY_DSP_NUM_CHANNELS
stream.frame_count = EASY_DSP_AUDIO_BUFFER_SIZE_BYTES // (EASY_DSP_NUM_CHANNELS * EASY_DSP_AUDIO_FORMAT_BYTES)
stream.volume = EASY_DSP_VOLUME


########################################################################################################################

### Define Callbacks ###################################################################################################
def handle_samples(buffer):
    printProgress("handle_buffer: received {count} bytes | shape {shape} | type {dtype}".format(count=buffer.nbytes,
                                                                                                shape=buffer.shape,
                                                                                                dtype=buffer.dtype, ))
    doa_info = compute_doa(buffer)


def handle_config(args=None):
    printProgress(
        "handle_config: new config ({frames},{sampleRate},{channelCount},{volume})".format(frames=stream.frame_count,
                                                                                           sampleRate=stream.sample_rate,
                                                                                           channelCount=stream.channel_count,
                                                                                           volume=stream.volume))
########################################################################################################################

### Actual DoA #########################################################################################################
def compute_doa(buffer):
    pass


########################################################################################################################

### Plot setup, animation, and DoA #####################################################################################



########################################################################################################################


if __name__ == '__main__':
    stream.change_config()
    stream.process_samples = handle_samples
    stream.process_config = handle_config
    stream.start()
    stream.loop_callbacks()
