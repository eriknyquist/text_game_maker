from __future__ import unicode_literals, print_function

import sys
import time
import inspect
import textwrap
import threading
import Queue

from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory

import parser
import map_builder

# Might use this later...
#
#import nltk
#
#def get_nouns(text):
#    tokens = nltk.word_tokenize(text)
#    tagged = nltk.pos_tag(tokens)
#    nouns = ['%s (%s)' % (word, pos) for word,pos in tagged
#        if (pos == 'NNP' or pos == 'NNS' )]
#    downcased = [x.lower() for x in nouns]
#    return "\n".join(downcased)

history = InMemoryHistory()
session = PromptSession(history=history, enable_history_search=True)

sequence = []

info = {
    'slow_printing': False,
    'chardelay': 0.02,
    'last_command': 'look',
    'sound': None
}

wrapper = textwrap.TextWrapper()
wrapper.width = 60

basic_controls = """
Movement
--------

Use phrases like 'east' or 'go south' to move around


Items
-----

Items are referred to by name. Use an item's name along with various verbs
to manipulate it:

 * Use 'i', 'inventory' or anything in between to show current inventory
   contents

 * Use phrases like 'get key' or 'pick up key' to add an item to your inventory
   by name (the item is named 'key' in this example and the following examples)

 * Use phrases like 'use key' or 'equip key' to equip an item by name from your
   inventory

 * Use phrases like 'put away key' or 'unequip key' to unequip an item

 * Equip inventory items to use them. For example, to use a key to unlock
   a door, walk to the door with the key equipped


People
------

People you encounter are referred to by name. Most interaction with people is
done through speaking.

* Use phrases like 'speak to alan', 'talk to alan', 'speak alan' to interact
  with a person by name (sample person is named 'Alan' in this example and the
  following examples)

* If you speak to someone with an inventory item equipped, they will see
  it and may offer to buy it.

* Use phrases like 'loot alan' or 'search alan' to try and steal a person's
  items and add them to your inventory. Attempts to loot a living person
  are usually unsuccessful.


Misc
----

* Use words like 'look' or 'show' to be reminded of your current surroundings

* Use 'help' or '?' to show this printout

* Use 'help' with a game command, e.g. 'help speak', to show information about
  that particular command

* Use 'controls' or 'commands' or 'words' or 'show words'... etc. to show a
  comprehensive listing of game commands"""

def _verify_callback(obj):
    if not inspect.isfunction(obj):
        raise TypeError('callbacks must be top-level functions')

def _remove_leading_whitespace(string):
    trimmed = [s.strip() for s in string.splitlines()]
    return '\n'.join(trimmed)

def _wrap_text(text):
    return wrapper.fill(text.replace('\n', ' ').replace('\r', ''))

def _wrap_print(text):
    print('\n' + _wrap_text(text))

def queue_command_sequence(seq):
    sequence.extend(seq)

def pop_command():
    try:
        ret = sequence.pop(0)
    except IndexError:
        ret = None

    return ret

def save_sound(sound):
    info['sound'] = sound

def last_saved_sound():
    return info['sound']

def list_to_english(strlist, conj='and'):
    """
    Convert a list of strings to description of the list in english.
    For example, ['4 coins', 'an apple', 'a sausage'] would be converted to
    '4 coins, an apple and a sausage'

    :param strlist: list of strings to convert to english
    :type strlist: str

    :return: english description of the passed list
    :rtype: str
    """

    if len(strlist) == 1:
        return strlist[0]

    msg = ""
    for i in range(len(strlist[:-1])):
        if i == (len(strlist) - 2):
            delim = ' ' + conj
        else:
            delim = ','

        msg += '%s%s ' % (strlist[i], delim)

    return msg + strlist[-1]

def _quit_hint():
    _wrap_print("Use %s to stop playing"
        % (list_to_english(['"%s"' % i for i in parser.KILL_WORDS], conj='or')))

def del_from_lists(item, *lists):
    for l in lists:
        if item in l:
            del l[l.index(item)]

def read_line_raw(msg, cancel_word=None, default=None):
    """
    Read a line of input from stdin

    :param str msg: message to print before reading input
    :return: a line ending with either a newline or carriage return character
    :rtype: str
    """

    user_input = ""
    buf = ""
    default_desc = ""
    cancel_desc = ""

    if default:
        default_desc = " [default: %s] " % default

    if cancel_word:
        cancel_desc = "(or '%s')" % cancel_word

    prompt = "%s %s%s: " % (msg, cancel_desc, default_desc)
    print('')

    if sequence:
        user_input = pop_command()
        print(prompt + user_input)
    else:
        user_input = session.prompt(prompt)

    if default and user_input == '':
        return default

    if cancel_word and cancel_word.startswith(user_input):
        return None

    return user_input

def read_line(msg, cancel_word=None, default=None):
    ret = ""
    while ret == "":
        ret = read_line_raw(msg, cancel_word, default)

    return ret

def ask_yes_no(msg, cancel_word="cancel"):
    """
    Ask player a yes/no question, and repeat the prompt until player
    gives a valid answer

    :param str msg: message to print inside prompt to player
    :param str cancel_word: player response that will cause this function\
        to return -1

    :return: 1 if player responded 'yes', 0 if they responded 'no', and -1\
        if they cancelled
    :rtype: int
    """

    prompt = "%s (yes/no/%s)" % (msg, cancel_word)

    while True:
        ret = read_line(prompt)
        if cancel_word.startswith(ret):
            return -1
        elif 'yes'.startswith(ret):
            return 1
        elif 'no'.startswith(ret):
            return 0

    return 0

def ask_multiple_choice(choices, msg=None, cancel_word="cancel"):
    """
    Ask the user a multiple-choice question, and return their selection

    :param [str] choices: choices to present to the player
    :return: list index of player's selection (-1 if user cancelled)
    :rtype: int
    """

    prompt = "Enter a number"
    lines = ['    %d. %s' % (i + 1, choices[i]) for i in range(len(choices))]

    if msg:
        print('\n' + msg + '\n')

    print('\n' + '\n'.join(lines))

    while True:
        ret = read_line(prompt, cancel_word)
        if ret is None:
            return -1

        try:
            number = int(ret)
        except ValueError:
            _wrap_print("'%s' is not a number." % ret)
            continue

        if (number < 1) or (number > len(choices)):
            _wrap_print("'%d' is not a valid choice. Pick something bewtween "
                "1-%d" % (number, len(choices)))
            continue

        return number - 1

def game_print(msg):
    """
    Print one character at a time if player has set 'print slow', otherwise
    print normally

    :param msg: message to print
    :type msg: str
    """

    msg = '\n' + _wrap_text(msg)
    if not info['slow_printing']:
        print(msg)
        return

    for i in range(len(msg)):
        sys.stdout.write(msg[i])
        sys.stdout.flush()
        time.sleep(info['chardelay'])

    print('')

def get_basic_controls():
    """
    Returns a basic overview of game command words
    """

    return basic_controls

def _do_listing(word_list, arg, desc):
    ret = '\n' + desc + '\n\n'
    for w in word_list:
        ret +='    "%s %s' % (w, arg)
        ret = ret.rstrip() + '"\n'

    return ret

def get_print_controls():
    return (
    '\n\nWords/phrases to control how the game prints stuff\n\n'
    '    "print slow" : print game output one character at\n'
    '    a time\n\n'
    '    "print fast" : print normally, with no delays\n\n'
    '    "print delay <secs>" : Set number of seconds (e.g.\n'
    '    0.02) to delay between characters when printing\n'
    '    slow\n\n'
    '    "print width <chars>": Set maximum line width for\n'
    '    game output'
    )

def get_full_controls(fsm):
    """
    Returns a comprehensive listing of of all game command words
    """

    descs = []

    ret = ""
    for cmd in fsm.iterate():
        text = cmd.help_text()
        if text not in descs:
            ret += '\n' + text
            descs.append(text)

    return ret
