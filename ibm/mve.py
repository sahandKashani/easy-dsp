from __future__ import print_function, division

import datetime
import sys

import browserinterface as bi


def printProgress(extraInfo=None):
    """
    Print to sys.stdout the name of the calling function along with a timestamp.
    If extraInfo is given, then replace the calling function name with extraInfo.

    :param extraInfo: string of user information
    """
    dt = datetime.datetime.now()
    if extraInfo:
        info = '{year:=04d}-{month:=02d}-{day:=02d}/{hour:02d}:{minute:=02d}:{second:=02d}  {info}'.format(
            year=dt.year, month=dt.month, day=dt.day,
            hour=dt.hour, minute=dt.minute, second=dt.second,
            info=extraInfo
        )
    else:
        info = '{year:=04d}-{month:=02d}-{day:=02d}/{hour:02d}:{minute:=02d}:{second:=02d}  {function}'.format(
            year=dt.year, month=dt.month, day=dt.day,
            hour=dt.hour, minute=dt.minute, second=dt.second,
            function=sys._getframe(1).f_code.co_name
        )
    print(info)


### Settings ###################################################################
# These must be kept in sync with browser-config.h
bi.inform_browser = False
bi.board_ip = '10.42.0.2'
bi.rate = 48000
bi.channels = 48
easy_dsp_audio_buffer_length_ms = 200
bi.buffer_frames = int(bi.rate * (easy_dsp_audio_buffer_length_ms / 1000.0))
bi.volume = 100


# bi.change_config(rate=bi.rate, channels=bi.channels, buffer_frames=bi.buffer_frames, volume=bi.volume)


### Define Callbacks ###########################################################
def handle_buffer(buffer):
    printProgress("handle_buffer: received {count} bytes".format(count=len(buffer)))


def handle_config(buffer_frames, rate, channels, volume):
    printProgress(
        "handle_config: new config ({frames},{sampleRate},{channelCount},{volume})".format(frames=buffer_frames,
                                                                                           sampleRate=rate,
                                                                                           channelCount=channels,
                                                                                           volume=volume))


def handle_recording(buffer):
    printProgress("handle_recording: {count} samples have been recorded".format(count=len(buffer)))


# ### Record Audio ###############################################################
# browserinterface.record_audio(5000, handle_recording)

### Register Handles ###########################################################
bi.register_handle_data(handle_buffer)
bi.register_when_new_config(handle_config)

### Start Communication ########################################################
bi.start()
bi.loop_callbacks()
