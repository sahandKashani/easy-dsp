#include <stdio.h>
#include <stdlib.h>
#include <websock/websock.h>
#include <jansson.h>
#include "browser-config.h"

int onmessage(libwebsock_client_state *state, libwebsock_message *msg) {
    fprintf(stderr, "Received message from client: %d\n", state->sockfd);
    fprintf(stderr, "Message opcode: %d\n", msg->opcode);
    fprintf(stderr, "Payload Length: %llu\n", msg->payload_len);
    fprintf(stderr, "Payload: %s\n", msg->payload);
    return 0;
}

int onopen(libwebsock_client_state *state) {
    fprintf(stderr, "onopen: %d\n", state->sockfd);
    return 0;
}

int onclose(libwebsock_client_state *state) {
    fprintf(stderr, "onclose: %d\n", state->sockfd);
    return 0;
}

int main(void) {
    libwebsock_context *ctx = NULL;
    ctx = libwebsock_init();
    if(ctx == NULL) {
        fprintf(stderr, "Error during libwebsock_init.\n");
        exit(EXIT_FAILURE);
    }
    libwebsock_bind(ctx, EASY_DSP_WSCONFIG_IP_ADDR, EASY_DSP_WSCONFIG_SERVER_PORT);
    fprintf(stdout, "libwebsock listening on port " EASY_DSP_WSCONFIG_SERVER_PORT "\n");
    ctx->onmessage = onmessage;
    ctx->onopen = onopen;
    ctx->onclose = onclose;
    libwebsock_wait(ctx);
    return EXIT_SUCCESS;
}
