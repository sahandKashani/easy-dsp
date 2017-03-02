#ifndef _BROWSER_CONFIG_H_
#define _BROWSER_CONFIG_H_

// Local sockets
#define EASY_DSP_CONTROL_SOCKET      "/tmp/micros-control.socket"
#define EASY_DSP_AUDIO_SOCKET        "/tmp/micros-audio.socket"

// Server configurations
#define EASY_DSP_WSAUDIO_IP_ADDR      "0.0.0.0" // 0.0.0.0 = all IPv4 addresses on the local machine
#define EASY_DSP_WSAUDIO_SERVER_PORT  "7321"
#define EASY_DSP_WSCONFIG_IP_ADDR     "0.0.0.0" // 0.0.0.0 = all IPv4 addresses on the local machine
#define EASY_DSP_WSCONFIG_SERVER_PORT "7322"

// Audio configuration
#define EASY_DSP_VOLUME                              (100)
#define EASY_DSP_NUM_CHANNELS                        (48)
#define EASY_DSP_AUDIO_FREQ_HZ                       (48000)
#define EASY_DSP_AUDIO_DOWNSAMPLE_FACTOR             (3)
#define EASY_DSP_AUDIO_FORMAT_BITS                   (16)
#define EASY_DSP_AUDIO_FORMAT_BYTES                  (EASY_DSP_AUDIO_FORMAT_BITS / 8)
#define EASY_DSP_AUDIO_BUFFER_LENGTH_MS              (200)
#define EASY_DSP_AUDIO_BUFFER_SIZE_BYTES             ((uint32_t) (EASY_DSP_NUM_CHANNELS * EASY_DSP_AUDIO_FREQ_HZ * EASY_DSP_AUDIO_FORMAT_BYTES * (EASY_DSP_AUDIO_BUFFER_LENGTH_MS / 1000.0)))
#define EASY_DSP_AUDIO_BUFFER_DOWNSAMPLED_SIZE_BYTES ((uint32_t) EASY_DSP_AUDIO_BUFFER_SIZE_BYTES / EASY_DSP_AUDIO_DOWNSAMPLE_FACTOR)

// In order to guarantee a continuous stream of audio samples, it is important
// to limit the maximum number of clients such that the total time to send the
// samples to all the clients is less than the acquisition time.
// In the case of the pyramic array on the DE1-SoC board, we measured that the
// system takes 0.15 ms to send 1 ms of audio to 1 client. Therefore, the
// theoretical maximum number of clients is floor(1 / 0.15) = 6.
// However, due to the randomness of the OS scheduler, it is safer to restrict
// the number of clients to 66% of this theoretical bound. As such, we limit the
// number of clients to (2/3) * 6 = 4.
#define MAX_CONNECTIONS 4

#endif /* _BROWSER_CONFIG_H_ */
