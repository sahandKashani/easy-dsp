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

// Default audio configuration
#define EASY_DSP_DEFAULT_VOLUME                     (100)
#define EASY_DSP_DEFAULT_NUM_CHANNELS               (48)
#define EASY_DSP_DEFAULT_AUDIO_FREQ_HZ              (48000)
#define EASY_DSP_DEFAULT_AUDIO_FORMAT_BITS          (16)
#define EASY_DSP_DEFAULT_HALF_BUFFER_LENGTH_SECONDS (1)

#endif /* _BROWSER_CONFIG_H_ */
