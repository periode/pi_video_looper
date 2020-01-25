#!/bin/sh

# Error out if anything fails.
set -e

# Make sure script is run as root.
if [ "$(id -u)" != "0" ]; then
  echo "Must be run as root with sudo! Try: sudo ./install.sh"
  exit 1
fi


echo "Installing dependencies..."
echo "=========================="
apt update && apt -y install python3 python3-pip python3-pygame supervisor omxplayer ntfs-3g exfat-fuse ffmpeg fbi python-pil

if [ "$*" != "no_hello_video" ]
then
	echo "Installing hello_video..."
	echo "========================="
	apt -y install git build-essential python3-dev
	git clone https://github.com/adafruit/pi_hello_video
	cd pi_hello_video
	./rebuild.sh
	cd hello_video
	make install
	cd ../..
	rm -rf pi_hello_video
else
    echo "hello_video was not installed"
    echo "=========================="
fi

echo "Installing video_looper program..."
echo "=================================="

# change the directoy to the script location
cd "$(dirname "$0")"

mkdir -p /mnt/usbdrive0 # This is very important if you put your system in readonly after
mkdir -p /home/pi/video # create default video directory

pip3 install setuptools
python3 setup.py install --force

cp ./assets/video_looper.ini /boot/video_looper.ini

echo "Configuring video_looper to run on start..."
echo "==========================================="

cp ./assets/video_looper.conf /etc/supervisor/conf.d/

service supervisor restart

echo "Setting up daily autoshutdown"
echo "============================="

(crontab -l ; echo "55 1 * * * sudo shutdown -h") | crontab -

if grep gpu_mem /boot/config.txt; then
  echo "Not changing GPU memory since it's already set"
else
  echo "Increasing GPU memory..."
  echo "========================"
  echo "" >> /boot/config.txt
  echo "# Increase GPU memory to avoid video playback problems" >> /boot/config.txt
  echo "gpu_mem=128" >> /boot/config.txt
fi

echo "Finished!"
