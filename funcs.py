import requests
import config
import json
import twitter
import pyaudio
import wave
from requests.auth import HTTPBasicAuth

AUDIO_FILENAME = 'rec.wav'

def tweet(message):
    api = twitter.Api(
        consumer_key=config.TWITTER_CK,
        consumer_secret=config.TWITTER_CS,
        access_token_key=config.TWITTER_TK,
        access_token_secret=config.TWITTER_TS)

    api.PostUpdate(message)

def speech_to_text():
    url = "https://stream.watsonplatform.net/speech-to-text/api/v1/recognize"
    files = {'file': open(AUDIO_FILENAME, 'rb')}
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
    jdata = resp.json()['results']
    if jdata:
        return jdata[0]['alternatives'][0]['transcript']
    else:
        return ''

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100

def create_audio_ctx():
    p = pyaudio.PyAudio()
    wf = wave.open(AUDIO_FILENAME, 'wb')
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    frames = []
    return [p, wf, stream, frames]

def process_audio_frame(ctx):
    p, wf, stream, frames = ctx

    data = stream.read(CHUNK)
    frames.append(data)

def close_audio_ctx(ctx):
    p, wf, stream, frames = ctx

    stream.stop_stream()
    stream.close()
    p.terminate()

    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
