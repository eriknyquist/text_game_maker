import sys
import os
import time
from pygame import mixer
import text_game_maker
from text_game_maker.ptttl.ptttl_audio_encoder import ptttl_to_sample_data

dir_path = os.path.dirname(text_game_maker.__file__)
AUDIO_DIR = os.path.join(dir_path, 'ptttl-data')
SUCCESS_SOUND = os.path.join(AUDIO_DIR, "prompt_success.txt")
FAILURE_SOUND = os.path.join(AUDIO_DIR, "prompt_fail.txt")
NEW_ITEM_SOUND = os.path.join(AUDIO_DIR, "new_item.txt")
ERROR_SOUND = os.path.join(AUDIO_DIR, "prompt_error.txt")
DEATH_SOUND = os.path.join(AUDIO_DIR, "death.txt")
FANFARE_SOUND = os.path.join(AUDIO_DIR, "fanfare.txt")
ALLSTAR_SOUND = os.path.join(AUDIO_DIR, "allstar_bach_chorale.txt")

FREQ = 44100
SAMPLESIZE = -16
CHANNELS = 1
BUFSIZE = 1024

class _Control(object):
    def __init__(self):
        self.sounds = {}
        self.last_played = None
        self.files_loaded = False

ctrl = _Control()

def load_file(filename, sound_id=None):
    """
    Read a PTTTL file, convert to PCM samples and save for playback

    :param str filename: filename for PTTTL file to read
    :param sound_id: key used to retrieve sound for playback (if None, filename\
        is used)
    """
    if sound_id is None:
        sound_id = filename

    with open(filename, 'r') as fh:
        ptttl_data = fh.read()

    rawdata = ptttl_to_sample_data(ptttl_data)
    ctrl.sounds[sound_id] = mixer.Sound(buffer=rawdata)

def init(frequency=FREQ, samplewidth=SAMPLESIZE, numchannels=CHANNELS,
        buffersize=BUFSIZE):
    """
    Initialize game audio and load PTTTL files for default sounds (called
    automatically by text_game_maker.builder.map_builder.MapBuilder.run_game)

    :param int frequency: frequency in HZ
    :param int samplewidth: sample size in bits
    :param int numchannels: number of audio channels
    :param int buffersize: size in bytes of the buffer to be used for playing\
        audio samples
    """
    if mixer.get_init() is not None:
        return

    mixer.pre_init(frequency, samplewidth, numchannels, buffersize)
    mixer.init()

    if not ctrl.files_loaded:
        load_file(SUCCESS_SOUND)
        load_file(FAILURE_SOUND)
        load_file(NEW_ITEM_SOUND)
        load_file(ERROR_SOUND)
        load_file(DEATH_SOUND)
        load_file(FANFARE_SOUND)
        load_file(ALLSTAR_SOUND)
        ctrl.files_loaded = True

def wait():
    """
    Wait until currently playing sound is finished playing (if any)
    """
    if ctrl.last_played is None:
        return

    while ctrl.last_played.get_busy():
        time.sleep(0.01)

def quit():
    """
    Disable audio after it has been initialized
    """
    wait()

    if mixer.get_init() is None:
        return

    ctrl.last_played = None
    mixer.quit()

def play_sound(sound_id):
    """
    Play a loaded sound

    :param sound_id: key for sound to play
    """
    if mixer.get_init() is None:
        return

    if (not ctrl.last_played is None) and ctrl.last_played.get_busy():
        return

    if sound_id not in ctrl.sounds:
        raise ValueError("No sound with ID '%s'" % sound_id)

    ctrl.last_played = mixer.Sound.play(ctrl.sounds[sound_id])
