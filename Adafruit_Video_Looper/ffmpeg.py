# Copyright 2015 Adafruit Industries.
# Author: Tony DiCola, Pierre Depaz
# License: GNU GPLv2, see LICENSE.txt
import os
import shutil
import subprocess
import tempfile
import time

from PIL import Image

class Ffmpeg:

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
        self._extensions = map(str.strip, config.get('ffmpeg', 'extensions').split(','))
        self._sound = config.get('ffmpeg', 'sound').lower()
        #self._extensions = config.get('fbi', 'extensions') \
                                #.translate(None, '\t\r\n.') \
                                #.split(',')
        self._extra_args = config.get('ffmpeg', 'extra_args').split()
        self._extra_render_args = config.get('ffmpeg', 'extra_render_args').split()
        self._display_duration = config.get('ffmpeg', 'display_duration')

    def _render_slideshow(self, images):
        if not os.path.exists('/home/pi/tmp') or not os.path.exists('/home/pi/slideshow'):
            os.makedirs('/home/pi/tmp')
            os.makedirs('/home/pi/slideshow')

        #clean directories
        os.system('rm /home/pi/tmp/*')
        os.system('rm /home/slideshow/*')
        os.system('rm /home/pi/slideshow.mp4')


        print("Moving and converting images...")
        for img in images:
            base = os.path.basename(img)
            fname, fext = os.path.splitext(base)
            if fext != ".png":
                print("converting -> /home/pi/{0}{1}".format(fname, fext))
                shutil.copy(img, '/home/pi/'+fname+fext)
                #cmd = 'mogrify -path /home/pi/tmp -format png -flatten -quality 100 /home/pi/{0}{1}'.format(fname, fext)
                #cmd = 'convert -quality 100 /home/pi/{0}{1} /home/pi/tmp/{0}.png'.format(fname, fext)
                #print(cmd)
                #p = subprocess.Popen(cmd)
                #time.sleep(5)
                #p.wait()
                im1 = Image.open('/home/pi/{0}{1}'.format(fname, fext))
                im1.save('/home/pi/tmp/{0}.png'.format(fname, fext))
            else:
                print("moving -> /home/pi/tmp/{0}{1}".format(fname, fext))
                shutil.copy(img, '/home/pi/tmp/'+fname+fext)

        print("...converted to png!")
        print("Renaming images for slideshow...")

        for i, filename in enumerate(os.listdir('/home/pi/tmp')):
            print(filename)
            os.rename('/home/pi/tmp/'+filename, '/home/pi/slideshow/'+str(i).zfill(5)+'.png')

        print("Renamed in the /home/pi/slideshow!")
        print("Rendering...")

        render_args = ['ffmpeg']
        render_args.extend(['-r', '1/'+self._display_duration]) # display time for each image
        render_args.extend(self._extra_render_args)
        command = "ffmpeg -r 1/"+self._display_duration+" -i '/home/pi/slideshow/%5d.png' -vf 'scale=1920:1080:force_original_aspect_ratio=decrease, pad=1920:1080:(ow-iw)/2:(oh-ih)/2, setsar=1' -c:v libx264 -crf 14 -r 25 -pix_fmt yuv420p -shortest /home/pi/slideshow.mp4"
        print(command)
        os.system(command)
        #render_process = subprocess.Popen(command,
        #                    stdout=subprocess.STDOUT,
        #                    close_fds=True)

        #render_process.wait()
        print("Rendered video!")

    def supported_extensions(self):
        """Return list of supported file extensions."""
        return self._extensions

    def play(self, playlist, loop=None, vol=0):
        """Play the provided movie file, optionally looping it repeatedly."""
        self.stop(3)  # Up to 3 second delay to let the old player stop.
        self._render_slideshow(playlist)
        # Assemble list of arguments.
        args = ['omxplayer', '/home/pi/slideshow.mp4']
        args.extend(['-o', self._sound])  # Add sound arguments.
        args.extend(self._extra_args)     # Add extra arguments from config.

        # Run omxplayer process and direct standard output to /dev/null.
        #os.system(' '.join(args))
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
            subprocess.call(['pkill', '-9', 'omxplayer'])
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
    """Create new video player based on ffmpeg."""
    return Ffmpeg(config)
