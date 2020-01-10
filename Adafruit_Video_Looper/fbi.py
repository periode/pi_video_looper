# Copyright 2015 Adafruit Industries.
# Author: Tony DiCola, Pierre Depaz
# License: GNU GPLv2, see LICENSE.txt
import os
import shutil
import subprocess
import tempfile
import time


class Fbi:

    def __init__(self, config):
        """Create an instance of a video player that runs omxplayer in the
        background.
        """
        self._process = None
        self._temp_directory = None
        self._load_config(config)

    def __del__(self):
        if self._temp_directory:
            shutil.rmtree(self._temp_directory)

    def _get_temp_directory(self):
        if not self._temp_directory:
            self._temp_directory = tempfile.mkdtemp()
        return self._temp_directory

    def _load_config(self, config):
        self._extensions = map(str.strip, config.get('fbi', 'extensions').split(','))
        #self._extensions = config.get('fbi', 'extensions') \
                                #.translate(None, '\t\r\n.') \
                                #.split(',')
        self._extra_args = config.get('fbi', 'extra_args').split()
        self._display_duration = config.get('fbi', 'display_duration')

    def supported_extensions(self):
        """Return list of supported file extensions."""
        return self._extensions

    def play(self, images, loop=None, vol=0):
        """Play the provided movie file, optionally looping it repeatedly."""
        self.stop(3)  # Up to 3 second delay to let the old player stop.
        # Assemble list of arguments.
        args = ['fbi']
        #args.extend(['-o', self._sound])  # Add sound arguments.
        args.extend(self._extra_args)     # Add extra arguments from config.
        args.extend(['-t', self._display_duration]) # display time for each image
        args.extend(images)       # Add movie file path.

        print("final args: %s" % ' '.join(args))
        # Run fbi process and direct standard output to /dev/null.
        self._process = subprocess.Popen(args,
                                         stdout=open(os.devnull, 'wb'),
                                         close_fds=True)

    def is_playing(self):
        """Return true if the video player is running, false otherwise."""
        if self._process is None:
            return False
        else:
            return True

    def stop(self, block_timeout_sec=0):
        """Stop the video player.  block_timeout_sec is how many seconds to
        block waiting for the player to stop before moving on.
        """
        # Stop the player if it's running.
        if self._process is not None and self._process.returncode is None:
            # There are a couple processes used by omxplayer, so kill both
            # with a pkill command.
            subprocess.call(['pkill', '-9', 'fbi'])
        # If a blocking timeout was specified, wait up to that amount of time
        # for the process to stop.
        start = time.time()
        while self._process is not None and self._process.returncode is None:
            if (time.time() - start) >= block_timeout_sec:
                break
            time.sleep(0)
        # Let the process be garbage collected.
        self._process = None

    @staticmethod
    def can_loop_count():
        return False


def create_player(config):
    """Create new video player based on fbi."""
    return Fbi(config)
