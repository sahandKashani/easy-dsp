#include <pthread.h>
#include <pyramicio.h>
#include <signal.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/un.h>

#define VOLUME                     (100)
#define NUM_CHANNELS               (48)
#define AUDIO_FREQ_HZ              (48000)
#define AUDIO_FORMAT_BITS          (16)
#define HALF_BUFFER_LENGTH_SECONDS (1)
#define HALF_BUFFER_SIZE_BYTES     (NUM_CHANNELS * AUDIO_FREQ_HZ * (AUDIO_FORMAT_BITS / 8) * HALF_BUFFER_LENGTH_SECONDS)

void sig_handler(int signo)
{
  if (signo == SIGPIPE) {
    fprintf(stdout, "received SIGPIPE\n");
  }
}

struct client {
  int addr;
  struct client* next;
};

void* handle_connections_audio(void* nothing);
void* handle_connections_control(void* nothing);
void* handle_audio(void* nothing);

struct client* clients;
pthread_t* audio_thread;

// alsa parameters
int* buffer_frames;
unsigned int* rate;
int* volume;
int* channels;


int main (int argc, char *argv[])
{
  buffer_frames = malloc(sizeof(*buffer_frames));
  rate = malloc(sizeof(*rate));
  channels = malloc(sizeof(*channels));
  volume = malloc(sizeof(*volume));
  audio_thread = malloc(sizeof(*audio_thread));
  *buffer_frames = HALF_BUFFER_SIZE_BYTES;
  *rate = AUDIO_FREQ_HZ;
  *channels = NUM_CHANNELS;
  *volume = VOLUME;
  clients = NULL;

  // "catch" SIGPIPE we get when we try to send data to a disconnected client
  if (signal(SIGPIPE, sig_handler) == SIG_ERR) {
    printf("\ncan't catch SIGPIPE\n");
  }

  pthread_t connections_audio_thread;
  pthread_t connections_control_thread;


  if( pthread_create(&connections_audio_thread, NULL, handle_connections_audio, NULL) < 0) {
      perror("could not create thread to handle connections audio");
      return 1;
  }
  if( pthread_create(audio_thread, NULL, handle_audio, NULL) < 0) {
      perror("could not create thread to handle audio ALSA");
      return 1;
  }
  if( pthread_create(&connections_control_thread, NULL, handle_connections_control, NULL) < 0) {
      perror("could not create thread to handle connections control");
      return 1;
  }

  while (1) {
  }

  exit (0);
}

void* handle_audio(void* nothing) {

  // 16-bit signed audio data
  int16_t *buffer = (int16_t *) malloc(HALF_BUFFER_SIZE_BYTES);
  if (buffer == NULL) {
    fprintf(stdout, "Cannot allocate buffer %p (size: %d)\n", buffer, HALF_BUFFER_SIZE_BYTES);
    exit(EXIT_FAILURE);
  }

  fprintf(stdout, "buffer allocated %d\n", HALF_BUFFER_SIZE_BYTES);

  struct pyramic *p = pyramicInitializePyramic();
  if (p == NULL) {
    fprintf(stderr, "pyramicInitializePyramic() failed\n");
    exit(EXIT_FAILURE);
  }

  if (pyramicStartCapture(p, HALF_BUFFER_LENGTH_SECONDS) != 0) {
    fprintf(stderr, "pyramicStartCapture() failed\n");
    pyramicDeinitPyramic(p);
    exit(EXIT_FAILURE);
  }

  // Note that the very first sample (when the daemon is switched on) will
  // contain garbage. It is assumed that the time to start the daemon and launch
  // a client is more than the size of an audio buffer in seconds.
  while (true) {
    // Get samples
    uint8_t buffer_id_currently_writing = pyramicGetCurrentBufferHalf(p) - 1; // returns 0 or 1 (after the subtraction).
    uint8_t buffer_id_currently_readable = buffer_id_currently_writing == 0 ? 1 : 0;

    struct inputBuffer ib = pyramicGetInputBuffer(p, buffer_id_currently_readable);
    memcpy(buffer, ib.samples, HALF_BUFFER_SIZE_BYTES);

    // Send audio buffer to clients
    struct client *c = clients;
    struct client *previous = NULL;
    while (c != NULL) {
      int re = write((*c).addr, buffer, HALF_BUFFER_SIZE_BYTES);
      if (re == -1) {
        // This client is gone
        // We remove it
        if (previous == NULL) { // First client
          clients = (*c).next;
        } else {
          (*previous).next = (*c).next;
        }
      }
      previous = c;
      c = (*c).next;
    }
  }

  pyramicDeinitPyramic(p);
  free(buffer);
}

void *handle_connections_control(void* nothing) {
  const char *SOCKNAMEC = "/tmp/micros-control.socket";
  unlink(SOCKNAMEC);
  int sfd, t, s2;
  struct sockaddr_un addr, remote;
  int config[4];
  int* c = config;

  sfd = socket(AF_UNIX, SOCK_STREAM, 0);            /* Create socket */
  if (sfd == -1) {
    fprintf (stderr, "cannot create the socket control\n");
    return NULL;
  }

  memset(&addr, 0, sizeof(struct sockaddr_un));     /* Clear structure */
  addr.sun_family = AF_UNIX;                            /* UNIX domain address */
  strncpy(addr.sun_path, SOCKNAMEC, sizeof(addr.sun_path) - 1);

  if (bind(sfd, (struct sockaddr *) &addr, sizeof(struct sockaddr_un)) == -1) {
    fprintf (stderr, "cannot bind the socket control\n");
    return NULL;
  }

  listen(sfd, 3);
  fprintf (stdout, "Bind successful control\n");
  while (1) {
    fprintf(stdout, "Waiting for a connection...\n");
    t = sizeof(remote);
    if ((s2 = accept(sfd, (struct sockaddr *)&remote, &t)) == -1) {
      fprintf (stderr, "cannot accept the connection control\n");
      continue;
    }

    fprintf(stdout, "New client control\n");

    recv(s2, c, sizeof(config), 0);
    fprintf(stdout, "111\n");
    pthread_cancel(*audio_thread);
    fprintf(stdout, "222\n");
    sleep(2); // FIXME : this is NOT deterministic. Need to find a better way.
    fprintf(stdout, "333\n");
    sleep(1); // FIXME : this is NOT deterministic. Need to find a better way.

    *buffer_frames = config[0];
    *rate = config[1];
    *channels = config[2];
    *volume = config[3];

    struct client* client;
    for (client = clients; client != NULL; client = (*client).next) {
      write((*client).addr, c, sizeof(config));
    }

    fprintf(stdout, "New configuration: %d %d %d %d", *buffer_frames, *rate, *channels, *volume);

    if( pthread_create(audio_thread, NULL, handle_audio, NULL) < 0) {
        perror("could not create thread to handle audio ALSA");
        return NULL;
    }

  }
}

void *handle_connections_audio(void* nothing) {
  const char *SOCKNAME = "/tmp/micros-audio.socket";
  unlink(SOCKNAME);
  int sfd, t, s2;
  struct sockaddr_un addr, remote;
  int config[4];
  int* c = config;

  sfd = socket(AF_UNIX, SOCK_STREAM, 0);            /* Create socket */
  if (sfd == -1) {
    fprintf (stderr, "cannot create the socket audio\n");
    return NULL;
  }

  memset(&addr, 0, sizeof(struct sockaddr_un));     /* Clear structure */
  addr.sun_family = AF_UNIX;                            /* UNIX domain address */
  strncpy(addr.sun_path, SOCKNAME, sizeof(addr.sun_path) - 1);

  if (bind(sfd, (struct sockaddr *) &addr, sizeof(struct sockaddr_un)) == -1) {
    fprintf (stderr, "cannot bind the socket\n");
    return NULL;
  }

  listen(sfd, 3);
  fprintf (stdout, "Bind successful audio\n");
  while (1) {
    fprintf(stdout, "Waiting for a connection...\n");
    t = sizeof(remote);
    if ((s2 = accept(sfd, (struct sockaddr *)&remote, &t)) == -1) {
      fprintf (stderr, "cannot accept the connection audio\n");
      continue;
    }

    fprintf(stdout, "New client audio\n");

    config[0] = *buffer_frames;
    config[1] = *rate;
    config[2] = *channels;
    config[3] = *volume;
    write(s2, c, sizeof(config));

    struct client* new_client = malloc(sizeof(struct client));
    (*new_client).addr = s2;
    (*new_client).next = clients;
    clients = new_client;
  }
}
