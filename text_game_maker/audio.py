import sys
import os
import time
import pygame
import text_game_maker
from text_game_maker.ptttl.ptttl_audio_encoder import ptttl_to_sample_data

AUDIO_DIR = os.path.abspath("audio")
SUCCESS_SOUND = os.path.join(AUDIO_DIR, "prompt_success.txt")
FAILURE_SOUND = os.path.join(AUDIO_DIR, "prompt_fail.txt")
DEATH_SOUND = os.path.join(AUDIO_DIR, "death.txt")
FANFARE_SOUND = os.path.join(AUDIO_DIR, "fanfare.txt")

pygame.mixer.pre_init(frequency=44100, size=-16, channels=1)
pygame.init()

class Control(object):
    def __init__(self):
        self.sounds = {}
        self.last_played = None

ctrl = Control()

def wait():
    if ctrl.last_played is None:
        return

    while ctrl.last_played.get_busy():
        time.sleep(0.01)

def add_ptttl_file(filename, sound_id=None):
    if sound_id is None:
        sound_id = filename

    with open(filename, 'r') as fh:
        ptttl_data = fh.read()

    rawdata = ptttl_to_sample_data(ptttl_data)
    ctrl.sounds[sound_id] = pygame.mixer.Sound(buffer=rawdata)

def play_sound(sound_id):
    if sound_id not in ctrl.sounds:
        raise ValueError("No sound with ID '%s'" % sound_id)

    ctrl.last_played = pygame.mixer.Sound.play(ctrl.sounds[sound_id])

add_ptttl_file(SUCCESS_SOUND)
add_ptttl_file(FAILURE_SOUND)
add_ptttl_file(DEATH_SOUND)
add_ptttl_file(FANFARE_SOUND)
