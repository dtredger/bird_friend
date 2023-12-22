# Enable headphone audio out via raspi-config

# An alternate way of determining the correct mouth movements could
# be a volume sensor; ie if it's not possible to determine loudness
# _before_ a sound is made.

import random
from logger import logger
from pygame import mixer


# volume range from 0 to 1
mixer.init()
mixer.music.set_volume(1)


# play sound
def play(filename):
    logger.info(f"play {filename}")
    full_path = SOUND_FILE_ROOT + filename
    mixer.music.load(full_path)
    mixer.music.play()


SOUND_FILE_ROOT = '/home/pi/crow_friend/sounds/'

# surprise motherfucker!
SURPRISE = 'surprise_louder.mp3'

CAW_1 = 'crow_1.mp3'  # 1 Caw, 700ms
CAW_4 = 'crow_4.wav'  # 4 caws, 3s
#
# # clicking sounds, 2s
# RATTLE_1 = 'crow_click_1.mp3'
# RATTLE_2 = 'crow_click_2.mp3'
# RATTLE_3 = 'crow_click_3.mp3'
# RATTLE_4 = 'crow_click_4.mp3'


CAW_MULTI_3 = 'crow_multi_3.mp3'
CAW_MULTI_9 = 'crow_multi_9.mp3'
CAW_MULTI_10 = 'crow_multi_10.mp3'

SOUNDS = {
    'surprise': {
        'filename': 'surprise_louder.mp3',
        'duration': 3.0
    },
    # every caw_1 is a single caw
    'caw_1': {
        'filename': 'crow_1.mp3',
        'duration': 0.7
    },
    'caw_1-2': {
        'filename': 'crow_1-2.wav',
        'duration': 0.7
    },
    'caw_1-3': {
        'filename': 'crow_1-3.mp3',
        'duration': 0.7
    },
    # 4 caws
    'caw_4': {
        'filename': 'crow_4.wav',
        'duration': 3.0
    },
    'crow_multi_3': {
        'filename': 'crow_multi-3ld.mp3',
        'duration': 4.5
    },
    'crow_multi_9': {
        'filename': 'crow_multi-9ld.mp3',
        'duration': 5.0
    },
    # (1 long, 9 short caws)
    'crow_multi_10': {
        'filename': 'crow_multi-10ld.mp3',
        'duration': 6.0
    },
    # rattle/click sounds
    'rattle_1': {
        'filename': 'crow_click_1ld.mp3',
        'duration': 2.0
    },
    'rattle_2': {
        'filename': 'crow_click_2ld.mp3',
        'duration': 2.0
    },
    'rattle_3': {
        'filename': 'crow_click_3ld.mp3',
        'duration': 2.0
    },
    'rattle_4': {
        'filename': 'crow_click_4ld.mp3',
        'duration': 2.0
    },
}

RATTLES = [SOUNDS['rattle_1'],
           SOUNDS['rattle_2'],
           SOUNDS['rattle_3'],
           SOUNDS['rattle_4']]

CAW_1S = [SOUNDS['caw_1'],
          SOUNDS['caw_1-2'],
          SOUNDS['caw_1-3']]

MULTICAWS = [SOUNDS['crow_multi_3'],
             SOUNDS['crow_multi_9'],
             SOUNDS['crow_multi_10']]


def rand_rattle():
    return random.choice(RATTLES)


def rand_caw1():
    return random.choice(CAW_1S)


def rand_multicaw():
    return random.choice(MULTICAWS)
