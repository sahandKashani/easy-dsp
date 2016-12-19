import sys
sys.path.append('..')
sys.path.append('examples')
import browserinterface
import numpy as np

import _mypath
import realtimeaudio as rt
from math import ceil

f = 100

def when_config(buffer_frames, rate, channels, volume):
    global chart, fs, buffer_size, d, vad, f, nothing
    if channels != 2 or buffer_frames != 4096:
        browserinterface.change_config(channels=2, buffer_frames=4096)
        return
    chart = browserinterface.add_handler("Speech", 'base:graph:line', {'xName': 'Duration', 'min': -10000, 'max': 10000, 'xLimitNb': (rate/f*10), 'series': [{'name': 'Voice', 'color': 'green'}, {'name': 'Other', 'color': 'red'}]})
    fs = rate
    buffer_size = buffer_frames
    nothing = np.zeros(int(ceil(buffer_frames/float(f)))).tolist()
    d = rt.transforms.DFT(nfft=buffer_size)
    vad = rt.VAD(buffer_size, fs, 10, 40e-3, 3, 1.2)

browserinterface.register_when_new_config(when_config)

i = 0
# perform VAD
def new_buffer(buffer):
    global chart, fs, buffer_size, d, vad, i, f, nothing
    # grab slice and take DFT to feed to VAD
    sig = buffer[:,0]  # only one channel
    X = d.analysis(sig)

    # perform VAD
    decision = vad.decision(X)
    # decision = vad.decision_energy(sig, 4)
    t = np.linspace(i*buffer_size,(i+1)*buffer_size,buffer_size)/float(fs)
    # o1 = {'x': t[::f].tolist(), 'y': nothing}
    o1 = {'x': [], 'y': []}
    o2 = {'x': t[::f].tolist(), 'y': sig[::f].tolist()}
    if decision:
        chart.send_data({'add':[o2, o1]})
    else:
        chart.send_data({'add':[o1, o2]})

    i += 1

browserinterface.register_handle_data(new_buffer)
browserinterface.start()
browserinterface.loop_callbacks()
