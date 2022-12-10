# flacfluke

A command-line tool to detect "fake" FLAC files

The logic taken from mvdschee's code https://github.com/mevdschee/fakeflac. Read the writeup here: https://github.com/mevdschee/fakeflac/blob/master/doc/index.md

The code was refactored to suit my needs. Temp .wav files are no longer created (which should make the script work on python) and I added threading when analyzing multiple files.

### Requirements

```
$ pip install -r requirements.txt
```

### Usage

```
$ python flacfluke.py [paths]
```
`[paths]` Can be a path to a flac file, a directory, or multiple space-separated directories/files