#include <inttypes.h>
#include <stdbool.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <stdio.h>
#include <stdlib.h>
#include <websock/websock.h>
#include <pthread.h>
#include <signal.h>
#include <time.h>
#include <unistd.h>
#include "browser-config.h"

void sig_handler(int signo) {
    if (signo == SIGPIPE) {
        fprintf(stdout, "received SIGPIPE\n");
    }
}

void *main_ws(void *nothing);
int *config;
void *send_config(libwebsock_client_state *state);

struct ws_client {
    libwebsock_client_state *c;
    struct ws_client *next;
};

struct ws_client* ws_clients;
pthread_mutex_t ws_client_lock;

int main(void) {
    ws_clients = NULL;

    if (signal(SIGPIPE, sig_handler) == SIG_ERR) {
        fprintf(stderr, "Can't catch SIGPIPE\n");
        exit(EXIT_FAILURE);
    }

    pthread_t main_ws_thread;

    if (pthread_create(&main_ws_thread, NULL, main_ws, NULL) < 0) {
        fprintf(stderr, "Could not create thread for main websocket loop\n");
        exit(EXIT_FAILURE);
    }

    int s = socket(AF_UNIX, SOCK_STREAM, 0);
    if (s  == -1) {
        fprintf(stderr, "Could not create socket\n");
        exit(EXIT_FAILURE);
    }

    printf("Trying to connect...\n");

    const char *SOCKNAME = EASY_DSP_AUDIO_SOCKET;
    struct sockaddr_un remote;
    remote.sun_family = AF_UNIX;
    strcpy(remote.sun_path, SOCKNAME);
    int len = strlen(remote.sun_path) + sizeof(remote.sun_family);
    if (connect(s, (struct sockaddr *)&remote, len) == -1) {
        fprintf(stderr, "Could not connect to socket\n");
        exit(EXIT_FAILURE);
    }

    printf("Connected.\n");

    struct ws_client* c;
    void *buffer = malloc(EASY_DSP_AUDIO_BUFFER_SIZE_BYTES);

    while (true) {
        // Wait until we receive EASY_DSP_AUDIO_BUFFER_SIZE_BYTES bytes in total.
        int32_t msg_len_bytes = 0;
        int32_t bytes_left_to_receive = EASY_DSP_AUDIO_BUFFER_SIZE_BYTES;
        do {
            void *dst = ((uint8_t *) buffer) + msg_len_bytes;

            ssize_t re = recv(s, dst, bytes_left_to_receive, 0);
            if (re >= 0) {
                msg_len_bytes += re;
                bytes_left_to_receive -= re;
            } else {
                fprintf(stderr, "Server closed connection\n");
                close(s);
                free(buffer);
                return EXIT_SUCCESS;
            }
        } while (bytes_left_to_receive > 0);

        // Send complete buffer to clients.
        struct ws_client* previous = NULL;
        pthread_mutex_lock(&ws_client_lock);

        for (c = ws_clients; c != NULL; c = c->next) {
            int re = libwebsock_send_binary(c->c, buffer, EASY_DSP_AUDIO_BUFFER_SIZE_BYTES);
            if (re == -1) {
                if (previous == NULL) {
                    ws_clients = c->next;
                } else {
                    previous->next = c->next;
                }
            } else {
                previous = c;
            }
        }

        pthread_mutex_unlock(&ws_client_lock);
    }

    return EXIT_SUCCESS;
}

int onmessage(libwebsock_client_state *state, libwebsock_message *msg) {
    fprintf(stdout, "Received message from client: %d\n", state->sockfd);
    fprintf(stdout, "Message opcode: %d\n", msg->opcode);
    fprintf(stdout, "Payload Length: %llu\n", msg->payload_len);
    fprintf(stdout, "Payload: %s\n", msg->payload);

    // Now let's send it back.
    libwebsock_send_text(state, msg->payload);

    return 0;
}

int onopen(libwebsock_client_state *state) {
    send_config(state);
    struct ws_client* new_client = malloc(sizeof(struct ws_client));
    new_client->next = ws_clients;
    new_client->c = state;
    ws_clients = new_client;
    return 0;
}

void *send_config(libwebsock_client_state *state) {
    char conf[100];

    sprintf(conf,
            "{\"buffer_frames\":%d,\"rate\":%d,\"channels\":%d,\"volume\":%d}",
            EASY_DSP_AUDIO_BUFFER_SIZE_BYTES / (EASY_DSP_NUM_CHANNELS * EASY_DSP_AUDIO_FORMAT_BYTES),
            EASY_DSP_AUDIO_FREQ_HZ,
            EASY_DSP_NUM_CHANNELS,
            EASY_DSP_VOLUME);

    libwebsock_send_text(state, conf);

    return NULL;
}

int onclose(libwebsock_client_state *state) {
    pthread_mutex_lock(&ws_client_lock);
    struct ws_client* c;
    struct ws_client* previous = NULL;

    for (c = ws_clients; c != NULL; c = c->next) {
        if (c->c == state) {
            break;
        }
        previous = c;
    }

    if (previous == NULL) {
        ws_clients = c->next;
    } else {
        previous->next = c->next;
    }

    pthread_mutex_unlock(&ws_client_lock);
    fprintf(stderr, "onclose: %d\n", state->sockfd);

    return 0;
}

void *main_ws(void* nothing) {
    libwebsock_context *ctx = NULL;
    ctx = libwebsock_init();

    if(ctx == NULL) {
        fprintf(stderr, "Error during libwebsock_init.\n");
        exit(EXIT_FAILURE);
    }

    libwebsock_bind(ctx, EASY_DSP_WSAUDIO_IP_ADDR, EASY_DSP_WSAUDIO_SERVER_PORT);
    fprintf(stdout, "libwebsock listening on port " EASY_DSP_WSAUDIO_SERVER_PORT "\n");
    ctx->onmessage = onmessage;
    ctx->onopen = onopen;
    ctx->onclose = onclose;
    libwebsock_wait(ctx);

    return NULL;
}
