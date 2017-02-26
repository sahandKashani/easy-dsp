################################################################################
# On host machine (inside embedded command shell)
################################################################################

git clone git@github.com:sahandKashani/Pyramic.git
cd Pyramic/fpga/MIC_ARRAY/
./create_linux_system.sh /dev/sdX # replace /dev/sdX with you sdcard
./create_hw_headers.sh
cd sw/hps/application
make -C pyramicio clean
make -C pyramicio
make -C pyramic_mic2wav clean
make -C pyramic_mic2wav
# make -C wav_tools clean
# make -C wav_tools
# make -C libpyramicio_test clean
# make -C libpyramicio

################################################################################
# On pyramic (FIRST boot, pyramic never switched on before)
################################################################################

## Very first boot (pyramic never switched on before)
# Use minicom to login with user "ibm", password "1234"
sudo /config_post_install.sh
# Restart the pyramic

################################################################################
# On host machine
################################################################################

cd Pyramic/fpga/MIC_ARRAY/sw/hps/application/pyramicio
scp libpyramicio.so root@pyramic:/usr/local/lib
scp pyramic.h       root@pyramic:/usr/local/include

################################################################################
# On pyramic (AFTER first boot)
################################################################################

## SSH into pyramic
# ssh ibm@10.42.0.2

## ~/.bashrc
export LD_LIBRARY_PATH="${LD_LIBRARY_PATH}":/usr/local/lib

## Apache and PHP
sudo apt install apache2 libapache2-mod-php5 php5 php5-common

## libevent
wget https://github.com/libevent/libevent/releases/download/release-2.1.8-stable/libevent-2.1.8-stable.tar.gz -O libevent-2.1.8-stable.tar.gz
tar -xvzf libevent-2.1.8-stable.tar.gz
pushd libevent-2.1.8-stable
sudo apt install make libtool automake
./configure # obtained from archive, not git, so no need to execute autogen.sh before ./configure
make
make verify # FAILS (missing time server it seems)
sudo make install
popd

## OpenSSL
sudo apt install libssl-dev

## libwebsock
sudo apt install git
git clone git://github.com/payden/libwebsock.git
pushd libwebsock
./autogen.sh # cloned from git, so need to execute autogen.sh before ./configure
./configure
make
sudo make install
popd

## Jansson
wget http://www.digip.org/jansson/releases/jansson-2.9.tar.gz -O jansson-2.9.tar.gz
tar -xvzf jansson-2.9.tar.gz
./configure
make
sudo make install
pushd jansson-2.9

################################################################################
# On pyramic (AFTER first boot, easy-dsp configuration)
################################################################################

cd /var
sudo git clone https://github.com/sahandKashani/easy-dsp.git
cd easy-dsp
sudo touch logs.txt
sudo chown www-data:www-data logs.txt
sudo cp microphones.virtualhost /etc/apache2/sites-available/microphones.conf # Attention: a2ensite is simply a perl script that only works with filenames ending ".conf" !
sudo a2ensite microphones
sudo echo "Listen 8081" | sudo tee -a /etc/apache2/ports.conf > /dev/null
sudo usermod -aG audio www-data
## not needed since no sound drivers are installed on pyramic
# sudo apt install acl
# sudo setfacl -m u:www-data:rw /dev/snd/*
# sudo rm /tmp/micros-audio.socket /tmp/micros-control.socket # doesn't exist on first install, maybe if reinstalling later.
sudo service apache2 restart
