=================================
Sound viewer
------------
[May 2020] - Mina PECHEUX

Based on the work by Yu-Jie Lin
(Public Domain)
Github: https://gist.github.com/manugarri/1c0fcfe9619b775bb82de0790ccb88da
=================================

LICENSE: CC0 (Public Domain) - see the file in the archive for more info
--------

DISCLAIMERS:
------------
  - all bash scripts use ffmpeg, so you need to install it first if
    you don't have it yet (https://ffmpeg.org/)
  - for now, the project only works with .wav and .mp4 files
  - all scripts and commands except file names WITHOUT their extension
  - the Python script doesn't automatically merge the audio and video
    (see step 4)


TL;DR:
------
A test audio file of some fingers snapping is provided with the scripts to
easily try out the project. Here is the entire process to get a fully finished
generated video:

  0. (optional) Start a virtual environment
  1. Install the Python packages:

      ~$ pip install -r requirements.txt

  2. Convert the test audio file, which is mono, to stereo:

      ~$ bash convert_to_stereo.sh test

  3. Create the video from the sound file:

      ~$ python main.py -m bars -c "#ddddff" --output test_stereo

  4. Merge the video and the audio:

      ~$ bash add_audio_to_video.sh -a test_stereo -v test_stereo

  5. Your final video is now available: it's the "test_stereo_processed.mp4" file :)
