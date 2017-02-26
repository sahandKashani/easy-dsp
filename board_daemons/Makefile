CC = gcc
CFLAGS = -g -Wall -Wextra -O0 -std=gnu99

default: all

all: browser-main-daemon browser-wsaudio browser-wsconfig

browser-main-daemon:
	$(CC) $(CFLAGS) browser-main-daemon.c -o browser-main-daemon -lpyramicio -lpthread

browser-wsaudio:
	$(CC) $(CFLAGS) browser-wsaudio.c     -o browser-wsaudio     -lwebsock   -lpthread

browser-wsconfig:
	$(CC) $(CFLAGS) browser-wsconfig.c    -o browser-wsconfig    -lwebsock   -ljansson

clean:
	-rm -f browser-main-daemon
	-rm -f browser-wsaudio
	-rm -f browser-wsconfig
