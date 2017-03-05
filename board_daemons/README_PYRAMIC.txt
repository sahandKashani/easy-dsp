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
# Use minicom to login with user "root", password "1234"
/config_post_install.sh
# Restart the pyramic

################################################################################
# On host machine
################################################################################

cd Pyramic/fpga/MIC_ARRAY/sw/hps/application/pyramicio
scp libpyramicio.so root@pyramic:/usr/local/lib
scp pyramicio.h     root@pyramic:/usr/local/include

################################################################################
# On pyramic (AFTER first boot)
################################################################################

## SSH into pyramic
# ssh root@10.42.0.2

### ~/.bashrc
export LD_LIBRARY_PATH="${LD_LIBRARY_PATH}":/usr/local/lib
## locale
export LC_ALL="en_US.UTF-8"
## Unlimited bash history
export HISTCONTROL=ignoredups:erasedups
export HISTSIZE=
export HISTFILESIZE=
shopt -s histappend
export PROMPT_COMMAND="history -a; history -c; history -r; ${PROMPT_COMMAND}"

## Apache and PHP
apt install apache2 libapache2-mod-php5 php5 php5-common

## Install more stuff related to system:
apt install sshfs valgrind ethtool

## libevent
apt install libevent-dev libevent-openssl-2.0.5

## OpenSSL
apt install libssl-dev

## libwebsock
apt install git
git clone git://github.com/payden/libwebsock.git
pushd libwebsock
./autogen.sh # cloned from git, so need to execute autogen.sh before ./configure
./configure
make
make install
popd

## Jansson
wget http://www.digip.org/jansson/releases/jansson-2.9.tar.gz -O jansson-2.9.tar.gz
tar -xvzf jansson-2.9.tar.gz
./configure
make
make install
pushd jansson-2.9

################################################################################
# On pyramic (AFTER first boot, easy-dsp configuration)
################################################################################

cd /var
git clone git@github.com:sahandKashani/easy-dsp.git
cd easy-dsp
touch logs.txt
chown www-data:www-data logs.txt
cp microphones.virtualhost /etc/apache2/sites-available/microphones.conf # Attention: a2ensite is simply a perl script that only works with filenames ending ".conf" !
a2ensite microphones
echo "Listen 8081" | tee -a /etc/apache2/ports.conf > /dev/null
usermod -aG audio www-data
## not needed since no sound drivers are installed on pyramic
# apt install acl
# setfacl -m u:www-data:rw /dev/snd/*
# rm /tmp/micros-audio.socket /tmp/micros-control.socket # doesn't exist on first install, maybe if reinstalling later.
service apache2 restart
