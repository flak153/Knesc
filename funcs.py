import requests
import config
import json
import twittera
import pyaudio
import wave
from requests.auth import HTTPBasicAuth

def tweet(message):
    api = twitter.Api(
        consumer_key=config.TWITTER_CK,
        consumer_secret=config.TWITTER_CS,
        access_token_key=config.TWITTER_TK,
        access_token_secret=config.TWITTER_TS)

    api.PostUpdate(message)

def speech_to_text(audio_):
    url = "https://stream.watsonplatform.net/speech-to-text/api/v1/recognize"
    files = {'file': open(audio_filename, 'rb')}
    auth = HTTPBasicAuth(config.BLUEMIX_STT_USER, config.BLUEMIX_STT_PASS)
    data = {
        'jsonDescription':json.dumps({
            "part_content_type": "audio/wav",
            "word_confidence": False,
            "continuous": False,
            "timestamps": False,
            "inactivity_timeout": 30,
            "max_alternatives": 1
        })
    }
    resp = requests.post(url, data=data, files=files, auth=auth)
    return resp.json().results.transcript

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
RECORD_SECONDS = 5

def create_audio(audio_filename):
    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    frames = []

    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(audio_data, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
