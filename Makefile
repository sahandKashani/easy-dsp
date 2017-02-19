CC = gcc
CFLAGS = -g -Wall -Wextra -O0 -std=c99

default: program

program:
	$(CC) $(CFLAGS) browser-main-daemon.c -o browser-main-daemon -lpyramicio -lpthread
	$(CC) $(CFLAGS) browser-wsconfig.c    -o browser-wsconfig    -lwebsock   -ljansson
	$(CC) $(CFLAGS) browser-wsaudio.c     -o browser-wsaudio     -lwebsock   -lpthread

clean:
	-rm -f *.o
	-rm -f $(TARGET)
