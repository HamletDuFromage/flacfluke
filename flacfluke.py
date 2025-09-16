#!/usr/bin/python

import io
import sys
from pydub import AudioSegment
from pathlib import Path
import argparse
import numpy
import threading
from scipy.fftpack import rfft
from scipy.io.wavfile import read
from scipy.signal.windows import hann


class FlacFluke:
    def __init__(self, paths):
        self.data = {}
        self.flacs = set()
        for path in list(map(Path, paths)):
            if path.exists():
                if path.is_dir():
                    self.flacs = self.flacs.union(set(path.glob("*.flac")))
                elif path.suffix.lower() == ".flac":
                    self.flacs.add(path)
            else:
                raise FileNotFoundError(path)
        self.threads_nb = min(len(self.flacs), 20)

    def threaded_processing(self):
        while True:
            try:
                flac = self.flacs.pop()
                self._scores[flac.name] = self._get_score(flac)
            except KeyError:
                break

    def get_scores(self):
        self._scores = {}
        threads = []
        for _ in range(self.threads_nb):
            x = threading.Thread(target=self.threaded_processing)
            threads.append(x)
            x.start()
        for thread in threads:
            thread.join()
        return self._scores

    def _moving_average(self, a, w):
        # calculate moving average
        window = numpy.ones(int(w)) / float(w)
        r = numpy.convolve(a, window, 'valid')
        # len(a) = len(r) + w
        a = numpy.empty((int(w / 2)))
        a.fill(numpy.nan)
        b = numpy.empty((int(w - len(a))))
        b.fill(numpy.nan)
        # add nan arrays to equal input and output length
        return numpy.concatenate((a, r, b))

    def _find_cutoff(self, a, dx, diff, limit):
        for i in range(1, int(a.shape[0] - dx)):
            if a[-i] / a[-1] > limit:
                break
            if a[int(-i - dx)] - a[-i] > diff:
                return a.shape[0] - i - dx
        return a.shape[0]

    def _get_score(self, flac_path):
        flac_data = AudioSegment.from_file(flac_path, format="flac")
        wav_stream = io.BytesIO()
        flac_data.export(wav_stream, format="wav")
        freq, audio = read(wav_stream)

        # process data
        channel = 0
        samples = len(audio[:, 0])
        seconds = int(samples / freq)
        seconds = min(seconds, 30)
        spectrum = [0] * freq

        # run over the seconds (max 30)
        for t in range(0, seconds - 1):
            # apply hanning window
            window = hann(freq)
            audio_second = audio[t * freq:(t + 1) * freq, channel] * window
            # do fft to add second to frequency spectrum
            spectrum += abs(rfft(audio_second))

        # calculate average of the spectrum
        spectrum /= seconds
        # normalize frequency spectrum
        spectrum = numpy.lib.scimath.log10(spectrum)
        # smoothen frequency spectrum with window w
        spectrum = self._moving_average(spectrum, freq / 100)
        # find cutoff in frequency spectrum
        cutoff = self._find_cutoff(spectrum, freq / 50, 1.25, 1.1)
        # print percentage of frequency spectrum before cutoff
        return int((cutoff * 100) / freq)


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print("usage: python3 flacfluke file")
    else:
        flacs = FlacFluke(sys.argv[1:])
        scores = flacs.get_scores()
        for key in sorted(scores):
            print(f"{key}: {scores[key]}")
