#!/usr/bin/env python
# =================================
# Sound viewer
# ------------
# [May 2020] - Mina PECHEUX
#
# Based on the work by Yu-Jie Lin
# (Public Domain)
# Github: https://gist.github.com/manugarri/1c0fcfe9619b775bb82de0790ccb88da

import wave

import click
import numpy as np
import psutil
import pyaudio
import vispy
from pygame import mixer

from compute import compute_spectrum, FPS, MAX_Z_SIZE

DEFAULT_CHANNELS = 2
DEFAULT_RATE = 44100

RECORD_SECONDS = 30
FORMAT = pyaudio.paInt16


@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.argument('filename', type=str, default='microphone')
@click.argument('log_input', type=bool, default=False)
def main(filename: str, log_input: bool):
    print(vispy.sys_info())
    if filename == 'microphone':
        p = pyaudio.PyAudio()

        stream = p.open(format=FORMAT,
                        channels=DEFAULT_CHANNELS,
                        rate=DEFAULT_RATE,
                        input=True,
                        frames_per_buffer=1024)

        frames = []
        print('Recording...')
        for _ in range(0, int(DEFAULT_RATE / 1024 * RECORD_SECONDS)):
            data = stream.read(1024)
            frames.append(data)
        print('Done recording')

        stream.stop_stream()
        stream.close()
        p.terminate()

        wf = wave.open('microphone.wav', 'wb')
        wf.setnchannels(DEFAULT_CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(DEFAULT_RATE)
        wf.writeframes(b''.join(frames))
        wf.close()

    # TODO: In case of 1 channel, reflect it into second

    frames_array = None
    with wave.open(filename + '.wav', 'rb') as wf:
        if wf.getnchannels() > 2:
            raise Exception("More than 2 channels in audio file")
        rate = wf.getframerate()
        sample_size = wf.getsampwidth()
        # Frames here mean number of frames we're going to take from the input
        num_frames = int(wf.getnframes() / rate * FPS)

        percent_free = (100 - psutil.virtual_memory().percent) / 100
        nfft = int(pow(2, np.floor(np.log((MAX_Z_SIZE * percent_free) / num_frames) / np.log(2)) - 1))
        print(f'Splitting frequency (X) axis into {nfft} parts')

        rate_fps_ratio = int(rate / FPS)
        N = (rate_fps_ratio // nfft) * nfft if rate_fps_ratio >= nfft else rate_fps_ratio
        frames_array = [wf.readframes(N) for _ in range(num_frames)]

    mixer.init()
    mixer_sound = mixer.Sound(filename + '.wav')
    compute_spectrum(frames_array, sample_size, rate, num_frames, nfft, mixer_sound, log_input)


if __name__ == '__main__':
    main()
