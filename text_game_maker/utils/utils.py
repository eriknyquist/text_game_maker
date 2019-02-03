from __future__ import unicode_literals, print_function
import sys
import os
import time
import random
import fnmatch
import inspect
import textwrap
import importlib

from prompt_toolkit.completion import PathCompleter
from prompt_toolkit import prompt as prompt_toolkit_prompt
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory

ITEM_LIST_FMT = "      {0:33}{1:1}({2})"

history = InMemoryHistory()
session = PromptSession(history=history, enable_history_search=True)

sequence = []

serializable_classes = {
}

info = {
    'slow_printing': False,
    'chardelay': 0.02,
    'last_command': 'look',
    'sequence_count': None,
    'sound': None,
    'instance': None,
}

wrapper = textwrap.TextWrapper()
wrapper.width = 60

_format_tokens = {}

_location = os.path.dirname(__file__)
_first_names = os.path.join(_location, "first-names.txt")
_middle_names = os.path.join(_location, "middle-names.txt")

def _fpeek(fh):
    ret = fh.read(1)
    fh.seek(-1, 1)
    return ret

def _rand_line(filename):
    with open(filename, 'r') as fh:
        # Get file size in bytes
        fh.seek(0, 2)
        size = fh.tell()
        fh.seek(0)

        # Seek to random byte offset in file
        pos = random.randrange(0, size)
        fh.seek(pos)

        # Seek backwards to a newline
        while (fh.tell() > 0) and (_fpeek(fh) != '\n'):
            fh.seek(-1, 1)

        if _fpeek(fh) == '\n':
            fh.seek(1, 1)

        name = fh.readline().strip().lower()
        return name[:1].upper() + name[1:]

def get_random_name():
    return '%s %s' % (_rand_line(_first_names), _rand_line(_middle_names))

def get_builder_instance():
    return info['instance']

def set_builder_instance(ins):
    info['instance'] = ins

def get_full_import_name(classobj):
    module = classobj.__module__
    if module is None or module == str.__class__.__module__:
        return classobj.__name__  # Avoid reporting __builtin__
    else:
        return module + '.' + classobj.__name__

def register_serializable_class(classobj, name):
    serializable_classes[name] = classobj

class SubclassTrackerMetaClass(type):
    def __init__(cls, name, bases, clsdict):
        if get_serializable_class(name):
            raise RuntimeError("There is already a game object class called "
                "'%s', please choose a different class name" % name)

        cls.full_class_name = get_full_import_name(cls)
        register_serializable_class(cls, cls.full_class_name)
        super(SubclassTrackerMetaClass, cls).__init__(name, bases, clsdict)

def get_serializable_class(name):
    if name not in serializable_classes:
        return None

    return serializable_classes[name]

def import_module_attribute(fullname):
    fields = fullname.split(".")
    modname = ".".join(fields[:-1])
    classname = fields[-1]
    return getattr(importlib.import_module(modname), classname)

def set_sequence_count(count):
    info['sequence_count'] = count

def get_sequence_count(count):
    return info['sequence_count']

def set_chardelay(delay):
    info['chardelay'] = delay

def get_chardelay():
    return info['chardelay']

def set_slow_printing(val):
    info['slow_printing'] = val

def get_slow_printing():
    return info['slow_printing']

def set_last_command(cmd):
    info['last_command'] = cmd

def get_last_command():
    return info['last_command']

def find_item(player, name, locations=None, ignore_dark=False):
    """
    Find an item by name in the provided locations

    :param text_game_maker.player.player.Player player: player object
    :param str name: name of item to find
    :param [[text_game_maker.game_objects.items.Item]] locations: location\
        lists to search. If None, the item list of the current tile is used
    :return: found item (None if no matching item is found)
    :rtype: text_game_maker.items.Item
    """
    if (not ignore_dark) and (not player.can_see()):
        return None

    if locations is None:
        locations = player.current.items.values()

    for itemlist in locations:
        for item in itemlist:
            if item.matches_name(name):
                return item

    return None


def is_location(player, name):
    """
    Checks if text matches the name of an adjacent tile that is connected to
    the current tile

    :param text_game_maker.player.player.Player player: player object
    :param str name: text to check
    :return: True if text matches adjacent tile name
    :rtype: bool
    """
    for direction in player.current.iterate_directions():
        if direction and direction.is_door() and (name in direction.name):
            return True

    for loc in player.current.items:
        if name in loc:
            return True

    return False

def get_all_items(player, locations=None, except_item=None):
    """
    Retrieves all items from specified locations

    :param text_game_maker.player.player.Player player: player object
    :param [[text_game_maker.game_objects.items.Item]] locations: location lists to search.\
        If None, the item list of the current room/tile is used
    :param object except_item: do not retrive item from location if it is the\
        same memory object as except_item. If None, no items are ignored.
    :return: list of retreived items
    :rtype: [text_game_maker.game_objects.items.Item]
    """

    if not player.can_see():
        return []

    if not locations:
        locations = player.current.items.values()

    ret = []
    for loc in locations:
        for item in loc:
            if (not except_item is None) and (except_item is item):
                continue

            if item.scenery:
                continue

            ret.append(item)

    return ret

def find_item_wildcard(player, name, locations=None):
    """
    Find the first item whose name matches a wildcard pattern ('*') in specific
    locations.

    :param text_game_maker.player.player.Player player: player object
    :param str name: wildcard pattern
    :param [[text_game_maker.game_objects.items.Item]] locations: location\
        lists to search. If None, the item list of the current tile is used
    :return: found item. If no matching item is found, None is returned.
    :rtype: text_game_maker.game_objects.items.Item
    """
    if name.startswith('the '):
        name = name[4:]

    if locations is None:
        locations = player.current.items.values()

    ret = []
    for loc in locations:
        for item in loc:
            if (not item.scenery) and fnmatch.fnmatch(item.name, name):
                return item

    return None

def find_person(player, name):
    """
    Find a person by name in the current tile

    :param text_game_maker.player.player.Player player: player object
    :param str name: name of person to search for
    :return: found person. If no matching person is found, None is returned.
    :rtype: text_game_maker.game_objects.person.Person
    """
    for loc in player.current.people:
        itemlist = player.current.people[loc]
        for item in itemlist:
            if (item.name.lower().startswith(name.lower())
                    or name.lower() in item.name.lower()):
                return item

    return None

def _inventory_search(player, cmpfunc):
    items = []
    items.extend(player.pockets.items)

    if player.inventory:
        items.extend(player.inventory.items)

    if player.equipped:
        items.append(player.equipped)

    for item in items:
        if cmpfunc(item):
            return item

    return None

def find_inventory_item(player, name):
    """
    Find an item by name in player's inventory

    :param text_game_maker.player.player.Player player: player object
    :param str name: name of item to search for
    :return: found item. If no matching item is found, None is returned.
    :rtype: text_game_maker.game_objects.items.Item
    """
    return _inventory_search(player,
        lambda x: x.matches_name(name))

def find_any_item(player, name):
    """
    Find an item by name in either the player's inventory or in the current tile

    :param text_game_maker.player.player.Player player: player object
    :param str name: name of item to search for
    :return: found item. If no matching item is found, None is returned.
    :rtype: text_game_maker.game_objects.items.Item
    """
    ret = find_inventory_item(player, name)
    if not ret:
        return find_item(player, name)

    return ret

def find_inventory_item_class(player, classobj):
    """
    Find first item in player's inventory which is an instance of a specific
    class

    :param text_game_maker.player.player.Player player: player object
    :param classobj: class to check for instances of
    :return: found item. If no matching item is found, None is returned.
    :rtype: text_game_maker.game_objects.items.Item
    """
    return _inventory_search(player, lambda x: isinstance(x, classobj))

def find_inventory_wildcard(player, name):
    """
    Find the first item in player's inventory whose name matches a wildcard
    pattern ('*').

    :param text_game_maker.player.player.Player player: player object
    :param str name: wildcard pattern
    :return: found item. If no matching item is found, None is returned.
    :rtype: text_game_maker.game_objects.items.Item
    """
    for item in player.inventory.items:
        if fnmatch.fnmatch(item.name, name):
            return item

    return None

def find_tile(player, name):
    """
    Find an adjacent tile that is connected to the current tile by name

    :param text_game_maker.player.player.Player player: player object
    :param str name: name of adjacent tile to search for
    :return: adjacent matching tile. If no matching tiles are found, None is\
        returned
    :rtype: text_game_maker.tile.tile.Tile
    """
    for tile in player.current.iterate_directions():
        if tile and (name in tile.name):
            return tile

    return None

def add_format_token(token, func):
    """
    Add a format token

    :param str token: token string to look for
    :param func: function to call to obtain replacement text for format token
    """
    _format_tokens[token] = func

def replace_format_tokens(text):
    """
    Replace format tokens in string (if any)

    :param str text: text that may contain format tokens
    :return: formatted text
    :rtype: str
    """
    for tok in _format_tokens:
        if tok in text:
            text = text.replace(tok, _format_tokens[tok]())

    return text

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

def get_all_contained_items(item, stoptest=None):
    """
    Recursively retrieve all items contained in another item

    :param text_game_maker.game_objects.items.Item item: item to retrieve items\
        from
    :param stoptest: callback to call on each sub-item to test whether\
        recursion should continue. If stoptest() == True, recursion will\
        continue
    :return: list of retrieved items
    :rtype: [text_game_maker.game_objects.items.Item]
    """
    ret = []

    if not item.is_container:
        return ret

    stack = [item]

    while stack:
        subitem = stack.pop(0)

        for i in subitem.items:
            ret.append(i)

            if i.is_container:
                if stoptest and stoptest(i):
                    continue

                stack.append(i)

    return ret

def _verify_callback(obj):
    if not inspect.isfunction(obj):
        raise TypeError('callbacks must be top-level functions')

def _remove_leading_whitespace(string):
    trimmed = [s.strip() for s in string.splitlines()]
    return '\n'.join(trimmed)

def _wrap_text(text):
    return wrapper.fill(text.replace('\n', ' ').replace('\r', ''))

def _wrap_print(text):
    print('\n' + _wrap_text(replace_format_tokens(text)))

def _unrecognised(val):
    _wrap_print('Unrecognised command "%s"' % val)

def queue_command_sequence(seq):
    """
    Add to game command sequence list

    :param [str] seq: list of command strings to add
    """
    sequence.extend(seq)

def pop_command():
    """
    Pop oldest command from game command sequence list

    :return: oldest command in game command sequence list
    :rtype: str
    """
    try:
        ret = sequence.pop(0)
    except IndexError:
        ret = None

    return ret

def save_sound(sound):
    """
    Save a sound to be played when parsing of the current command is completed.
    Overwrites any previously saved sound.

    :param sound: sound ID key needed by text_game_maker.audio.audio.play_sound
    """
    info['sound'] = sound

def last_saved_sound():
    """
    Retrieve last sound ID saved with text_game_maker.save_sound

    :return: last saved sound ID
    """
    return info['sound']

def capitalize(text):
    """
    Capitalize first non-whitespace character folling each period in string

    :param str text: text to capitalize
    :return: capitalized text
    :rtype: str
    """
    ret = list(text)

    # Make sure first word is capitalized...

    i = 0
    while i < (len(text) - 1) and text[i].isspace():
        i += 1

    if text[i].isalpha() and text[i].islower():
        ret[i] = ret[i].upper()

    # Find all alpha characters following a period and make
    # sure they are uppercase...

    p = 0 # next period index

    while p < (len(text) - 1):
        p = text.find('.', p)

        if p < 0:
            break

        p += 1

        # index of first non-space character after period
        w = p

        while w < (len(text) - 1) and text[w].isspace():
            w += 1

        if text[w].isalpha() and text[w].islower():
            ret[w] = ret[w].upper()

    return ''.join(ret)

def multisplit(s, *seps):
    """
    Split a string into substrings by multiple tokens

    :param str s: string to split
    :param [str] seps: list of strings to split on
    :return: list of substrings
    :rtype: [str]
    """
    stack = [s]
    for char in seps:
        pieces = []
        for substr in stack:
            pieces.extend([x.strip() for x in substr.split(char)])

        stack = pieces

    return stack

def english_to_list(text):
    """
    Convert a string of the form 'a, b, c and d' to a list of the form
    ['a','b','c','d']

    :param str text: input string
    :return: list of items in string, split on either ',' or 'and'
    :rtype: list
    """

    return multisplit(text, ",", "and")

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

def centre_text(string, line_width=None):
    """
    Centre a line of text within a specific number of columns

    :param str string: text to be centred
    :param int line_width: line width for centreing text. If None, the\
        current line width being used for game output will be used
    :return: centred text
    :rtype: str
    """
    if not line_width:
        line_width = wrapper.width

    string = string.strip()
    diff = line_width - len(string)
    if diff <= 2:
        return string

    spaces = ' ' * (diff / 2)
    return spaces + string + spaces

def line_banner(text, width=None, bannerchar='-', spaces=1):
    """
    Centre a line of text within a specific number of columns, and surround text
    with a repeated character on either side.

    Example:

    ---------- centred text ----------

    :param str text: text to be centred
    :param int width: line width for centreing text
    :param str bannerchar: character to use for banner around centred text
    :param int spaces: number of spaces seperating centred text from banner
    :return: centred text with banner
    :rtype: str
    """
    if not width:
        width = wrapper.width

    name = (' ' * spaces) + text + (' ' * spaces)
    half = ('-' * ((width / 2) - (len(name) / 2)))
    return (half + name + half)[:width]

def container_listing(container, item_fmt=ITEM_LIST_FMT, width=50,
        bottom_border=False, name=None):
    if name is None:
        name = container.name

    banner_text = "%s (%d/%d)" % (name, len(container.items),
        container.capacity)

    ret = line_banner(banner_text, width) + '\n'

    if container.items:
        ret += '\n'
        for item in container.items:
            ret += item_fmt.format(item.name, "", item.value) + '\n'

    if bottom_border:
        ret += '\n'
        ret += ('-' * width)

    return ret

def del_from_lists(item, *lists):
    for l in lists:
        if item in l:
            del l[l.index(item)]

def read_path_autocomplete(msg):
    return prompt_toolkit_prompt(msg, completer=PathCompleter())

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
        default_desc = " [default: %s]" % default

    if cancel_word:
        cancel_desc = " (or '%s') " % cancel_word

    prompt = "%s%s%s" % (msg, cancel_desc, default_desc)
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

    prompt = "%s (yes/no/%s):" % (msg, cancel_word)

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

    msg = '\n' + _wrap_text(replace_format_tokens(msg))
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

def _find_word_end(string, i):
    while i < len(string):
        if string[i] == ' ':
            return i

        i += 1

    return len(string)

def _parser_suggestions(fsm, text, i):
    _unrecognised(text)

    if i > 0:
        print ('\nDid you mean...\n\n%s'
            % ('\n'.join(['  %s' % w for w in fsm.get_children()])))

def run_fsm(fsm, action):
    i, cmd = fsm.run(action)
    if  i > 0 and i < len(action) and action[i - 1] != ' ':
        _parser_suggestions(fsm, action[:_find_word_end(action, i)], i)
        return i, None
    elif not cmd:
        _parser_suggestions(fsm, action, i)
        return i, None

    return i, cmd

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
        if text and (text not in descs):
            ret += '\n' + text
            descs.append(text)

    return ret
