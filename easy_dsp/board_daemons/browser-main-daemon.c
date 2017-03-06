#include <assert.h>
#include <inttypes.h>
#include <pthread.h>
#include <pyramicio.h>
#include <signal.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <sys/un.h>
#include "browser-config.h"

#define SLEEP_DURATION_US           ((uint32_t) (0.1 * EASY_DSP_AUDIO_BUFFER_LENGTH_MS * 1000))
#define SLEEP_DURATION_IDLE_SECONDS (10) // Any constant would work here.

void sig_handler(int signo) {
    if (signo == SIGPIPE) {
        fprintf(stdout, "received SIGPIPE\n");
    }
}

struct client {
    int addr;
    struct client* next;
};

void *handle_connections_audio(void *nothing);
void *handle_connections_control(void *nothing);
void *handle_audio(void *nothing);

struct client *clients;

int main (int argc, char *argv[]) {
    clients = NULL;

    // "catch" SIGPIPE we get when we try to send data to a disconnected client
    if (signal(SIGPIPE, sig_handler) == SIG_ERR) {
        fprintf(stderr, "Can't catch SIGPIPE\n");
    }

    pthread_t connections_audio_thread;
    pthread_t connections_control_thread;
    pthread_t audio_thread;

    if (pthread_create(&connections_audio_thread, NULL, handle_connections_audio, NULL) < 0) {
        fprintf(stderr, "Could not create thread to handle connections audio\n");
        return EXIT_FAILURE;
    }

    if (pthread_create(&audio_thread, NULL, handle_audio, NULL) < 0) {
        fprintf(stderr, "Could not create thread to handle audio\n");
        return EXIT_FAILURE;
    }

    if (pthread_create(&connections_control_thread, NULL, handle_connections_control, NULL) < 0) {
        fprintf(stderr, "Could not create thread to handle connections control\n");
        return EXIT_FAILURE;
    }

    while (true) {
        // Sleep for a long time to not take CPU cycles. ANY constant could work
        // here.
        sleep(SLEEP_DURATION_IDLE_SECONDS);
    }

  exit(EXIT_SUCCESS);
}

void *handle_audio(void *nothing) {
    void *buffer = malloc(EASY_DSP_AUDIO_BUFFER_SIZE_BYTES);

    if (buffer == NULL) {
        fprintf(stderr, "Cannot allocate buffer %p (size: %d)\n", buffer, EASY_DSP_AUDIO_BUFFER_SIZE_BYTES);
        exit(EXIT_FAILURE);
    }

    struct pyramic *p = pyramicInitializePyramic();
    if (p == NULL) {
        fprintf(stderr, "pyramicInitializePyramic() failed\n");
        exit(EXIT_FAILURE);
    }

    // Multiply by 2 because the pyramic uses a double buffering technique. If
    // we want to receive EASY_DSP_AUDIO_BUFFER_LENGTH_MS milliseconds of audio
    // RELIABLY, then we need to allocate double the buffer size.
    if (pyramicStartCapture(p, 2 * EASY_DSP_AUDIO_BUFFER_LENGTH_MS) != 0) {
        fprintf(stderr, "pyramicStartCapture() failed\n");
        pyramicDeinitPyramic(p);
        exit(EXIT_FAILURE);
    }

    // double-buffered sound acquisition
    uint8_t buffer_id_write = pyramicGetCurrentBufferHalf(p) - 1; // returns 0 or 1 (after the subtraction).
    uint8_t buffer_id_read = !buffer_id_write;

    while (true) {
        // Wait until write buffer is completely filled.
        while(pyramicGetCurrentBufferHalf(p) - 1 == buffer_id_write) {
            usleep(SLEEP_DURATION_US);
        }

        // Swap write and read buffers
        buffer_id_write = !buffer_id_write;
        buffer_id_read = !buffer_id_read;

        // Get samples from read buffer
        struct inputBuffer ib = pyramicGetInputBuffer(p, buffer_id_read);

        // Send samples to clients
        struct client *c = clients;
        struct client *previous = NULL;

        while (c != NULL) {
            ssize_t re = write(c->addr, ib.samples, EASY_DSP_AUDIO_BUFFER_SIZE_BYTES);
            if (re == -1) {
                // This client is gone, so we remove it.
                if (previous == NULL) { // First client
                    clients = c->next;
                } else {
                    previous->next = c->next;
                }
            }
            previous = c;
            c = c->next;
        }
    }

    pyramicDeinitPyramic(p);
    free(buffer);
}

void *handle_connections_control(void *nothing) {
    // Pyramic is non-configurable at runtime. Only at compile-time through
    // browser-config.h
    while (true) {
        // Sleep for a long time to not take CPU cycles. ANY constant could work
        // here.
        sleep(SLEEP_DURATION_IDLE_SECONDS);
    }
}

void *handle_connections_audio(void *nothing) {
    const char *SOCKNAME = EASY_DSP_AUDIO_SOCKET;
    unlink(SOCKNAME);
    int sfd, s2;
    struct sockaddr_un addr, remote;

    sfd = socket(AF_UNIX, SOCK_STREAM, 0); // Create socket
    if (sfd == -1) {
        fprintf(stderr, "Cannot create the audio socket\n");
        return NULL;
    }

    memset(&addr, 0, sizeof(struct sockaddr_un)); // Clear structure
    addr.sun_family = AF_UNIX; // UNIX domain address
    strncpy(addr.sun_path, SOCKNAME, sizeof(addr.sun_path) - 1);

    if (bind(sfd, (struct sockaddr *) &addr, sizeof(struct sockaddr_un)) == -1) {
        fprintf(stderr, "Cannot bind the socket\n");
        return NULL;
    }

    listen(sfd, 3);
    fprintf(stdout, "Bind successful audio\n");
    while (true) {
        fprintf(stdout, "Waiting for a connection...\n");
        socklen_t t = sizeof(remote);
        if ((s2 = accept(sfd, (struct sockaddr *)&remote, &t)) == -1) {
            fprintf(stderr, "Cannot accept the connection audio\n");
            continue;
        }

        fprintf(stdout, "Added new client to list of audio clients\n");
        struct client* new_client = malloc(sizeof(struct client));
        new_client->addr = s2;
        new_client->next = clients;
        clients = new_client;
    }
}
