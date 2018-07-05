import time
import sys
import pickle
import os
import fnmatch
import errno

import parser
import text_game_maker
from text_game_maker.tile import Tile
from text_game_maker.items import Item
from text_game_maker.player import Player

MIN_LINE_WIDTH = 50
MAX_LINE_WIDTH = 120
COMMAND_DELIMITERS = [',', ';', '/', '\\']

fsm = parser.SimpleTextFSM()

class Command(object):
    """
    Container class for data needed to execute a particular game command
    """

    def __init__(self, word_list, callback, desc, phrase_fmt):
        self.word_list = word_list
        self.callback = callback
        self.desc = desc

        self.desc = self.desc[0].upper() + self.desc[1:]
        if not phrase_fmt or phrase_fmt == "":
            self.phrase_fmt = '%s'
        else:
            self.phrase_fmt = phrase_fmt

    def help_text(self):
        ret = '\n' + self.desc + ':\n\n'
        for w in self.word_list:
            ret += ('    "' + self.phrase_fmt + '"\n') % w

        return ret

def _translate(val, min1, max1, min2, max2):
    span1 = max1 - min1
    span2 = max2 - min2

    scaled = float(val - min1) / float(span1)
    return min2 + (scaled * span2)

def _unrecognised(val):
    text_game_maker._wrap_print('Unrecognised command "%s"' % val)

def _parser_suggestions(text, i):
    _unrecognised(text)

    if i > 0:
        print ('\nDid you mean...\n\n%s'
            % ('\n'.join(['  %s' % w for w in fsm.get_children()])))

def _find_word_end(string, i):
    while i < len(string):
        if string[i] == ' ':
            return i

        i += 1

    return len(string)

def _run_fsm(action):
    i, cmd = fsm.run(action)
    if  i > 0 and i < len(action) and action[i - 1] != ' ':
        _parser_suggestions(action[:_find_word_end(action, i)], i)
        return i, None
    elif not cmd:
        _parser_suggestions(action, i)
        return i, None

    return i, cmd

def _do_move(player, word, direction):
    if not direction or direction == "":
        text_game_maker._wrap_print("Where do you want to go?")
        return

    if 'north'.startswith(direction):
        player._move_north(word)
    elif 'south'.startswith(direction):
        player._move_south(word)
    elif 'east'.startswith(direction):
        player._move_east(word)
    elif 'west'.startswith(direction):
        player._move_west(word)
    else:
        _unrecognised(direction)

def _find_best_match_item_index(player, name):
    if name.startswith('the '):
        name = name[4:]

    for loc in player.current.items:
        itemlist = player.current.items[loc]
        for item in itemlist:
            if (item.name.lower().startswith(name.lower())
                    or name.lower() in item.name.lower()):
                return item

    return None

def _find_wildcard_match(player, name):
    if name.startswith('the '):
        name = name[4:]

    ret = []
    for loc in player.current.items:
        for item in player.current.items[loc]:
            if fnmatch.fnmatch(item.name, name):
                return item

    return None

def _find_best_match_person_index(player, name):
    for loc in player.current.people:
        itemlist = player.current.people[loc]
        for item in itemlist:
            if (item.name.lower().startswith(name.lower())
                    or name.lower() in item.name.lower()):
                return item

    return None

def _find_best_match_inventory_item(player, name):
    if name.startswith('the '):
        name = name[4:]

    for item in player.inventory['equipped']:
        if item.name.startswith(name) or name in item.name:
                return item

    for item in player.inventory['unequipped']:
        if item.name.startswith(name) or name in item.name:
                return item

    return None

def _take(player, item):
    # If on_take callback returns false, abort adding this item
    if not item.on_take(player):
        return False

    player.inventory['unequipped'].append(item)
    item.delete()

    item.home = player.inventory['unequipped']
    return True

def _do_eat(player, word, item_name):
    if not item_name or item_name == "":
        text_game_maker._wrap_print("What do you want to %s?" % word)
        return

    item = _find_best_match_inventory_item(player, item_name)
    if not item:
        item = _find_best_match_item_index(player, item_name)
        if not item:
            item  = _find_best_match_person_index(player, item_name)
            if not item:
                text_game_maker._wrap_print("No %s available to %s"
                    % (item_name, word))
                return

    msg = item.on_eat(player, word)
    if msg:
        text_game_maker.game_print(msg)

def _do_take(player, word, item_name):
    if not item_name or item_name == "":
        text_game_maker._wrap_print("What do you want to %s?" % word)
        return

    if '*' in item_name:
        added = []
        item = ' '

        while item:
            item = _find_wildcard_match(player, item_name)
            if item and _take(player, item):
                added.append(item.name)

        if not added:
            text_game_maker._wrap_print("No matching items to %s" % word)
            return

        msg = text_game_maker.list_to_english(added)
    else:
        item = _find_best_match_item_index(player, item_name)
        if not item:
            text_game_maker._wrap_print("No %s available to %s" % (item_name, word))
            return

        msg = item.name
        if not _take(player, item):
            return

    text_game_maker.game_print('%s added to inventory' % msg)
    return

def _find_inventory_wildcard(player, name):
    for item in player.inventory['unequipped']:
        if fnmatch.fnmatch(item.name, name):
            return item

    return None

def _drop(player, n):
    # Place item on the floor in current room
    item = _find_best_match_inventory_item(player, n)
    if not item:
        return

    item.delete()

    item.location = "on the floor"
    player.current.add_item(item)

def _do_drop(player, word, item_name):
    if not item_name or item_name == "":
        text_game_maker._wrap_print("What do you want to drop?")
        return

    msg = None
    if '*' in item_name:
        added = []
        item = ' '

        while item:
            item = _find_inventory_wildcard(player, item_name)
            if item:
                added.append(item.name)
                _drop(player, item.name)

        if not added:
            text_game_maker._wrap_print("No matching items to %s." % word)
            return

        msg = text_game_maker.list_to_english(added)
    else:
        item = _find_best_match_inventory_item(player, item_name)
        if not item:
            text_game_maker._wrap_print("No %s in your inventory to %s"
                % (item_name, word))
            return

        _drop(player, item.name)
        msg = item.name

    text_game_maker.game_print("Dropped %s" % msg)

def _do_speak(player, word, name):
    if not name or name == "":
        text_game_maker._wrap_print("Who do you want to speak to?")
        return

    p = _find_best_match_person_index(player, name)
    if not p:
        p = _find_best_match_item_index(player, name)
        if not p:
            text_game_maker._wrap_print("Don't know how to %s %s" % (word, name))
            return

    text_game_maker.game_print('You speak to %s.' % p.prep)
    if p.alive:
        response = p.on_speak(player)
        if response:
            p.say(response)
    else:
        text_game_maker.game_print('%s says nothing.' % p.prep)


def _do_quit(player, word, name):
    ret = text_game_maker.ask_yes_no("really stop playing?")
    if ret < 0:
        return
    elif ret:
        sys.exit()

def _do_equip(player, word, item_name):
    if not item_name or item_name == "":
        text_game_maker._wrap_print("Which inventory item do you want to %s?"
            % word)
        return

    item = _find_best_match_inventory_item(player, item_name)
    if not item:
        text_game_maker._wrap_print("No %s in your inventory to %s"
            % (item_name, word))
        return

    if item in player.inventory['equipped']:
        text_game_maker.game_print("%s is already equipped." % item.name)
        return

    # Move any already-equipped items back to unequipped
    if player.inventory['equipped']:
        equipped = player.inventory['equipped'][0]
        player.inventory['unequipped'].append(equipped)
        equipped.delete()
        equipped.home = player.inventory['unequipped']
        
    item.delete()

    player.inventory['equipped'] = [item]
    item.home = player.inventory['equipped']

    text_game_maker.game_print("Equipped %s." % item.name)

def _do_unequip(player, word, fields):
    if not player.inventory['equipped']:
        text_game_maker.game_print('Nothing is currently equipped.')
        return
    
    equipped = player.inventory['equipped'][0]
    player.inventory['unequipped'].append(equipped)
    equipped.delete()
    equipped.home = player.inventory['unequipped']
    text_game_maker.game_print('%s unequipped' % equipped.name)

def _do_loot(player, word, name):
    if not name or name == "":
        text_game_maker._wrap_print("Who do you want to %s?" % word)
        return

    p = _find_best_match_person_index(player, name)
    if not p:
        p = _find_best_match_item_index(player, name)
        if not p:
            text_game_maker.game_print("Not sure how to %s %s" % (word, name))
            return

    if p.alive:
        text_game_maker.game_print("You are dead.")
        text_game_maker.game_print("You were caught trying to %s %s."
            % (word, p.name))
        text_game_maker.game_print("%s didn't like this, and killed you.\n"
            % p.name)
        sys.exit()
    else:
        player._loot(word, p)

def _do_set_print_speed(player, word, setting):
    if not setting or setting == "":
        text_game_maker._wrap_print("Fast or slow? e.g. 'print fast'")
        return

    if 'slow'.startswith(setting):
        text_game_maker.info['slow_printing'] = True
        text_game_maker._wrap_print("OK, will do.")
    elif 'fast'.startswith(setting):
        text_game_maker.info['slow_printing'] = False
        text_game_maker._wrap_print("OK, got it.")
    else:
        text_game_maker._wrap_print("Unrecognised speed setting '%s'. Please "
            "say 'fast' or 'slow'.")

def _do_set_print_delay(player, word, setting):
    if not setting or setting == "":
        text_game_maker._wrap_print("Please provide a delay value in seconds "
                "(e.g. 'print delay 0.01')")
        return

    try:
        text_game_maker.info['chardelay'] = float(setting)
    except ValueError:
        text_game_maker._wrap_print("Don't recognise that value for "
            "'print delay'. Enter a delay value in seconds (e.g. 'print "
            "delay 0.1')")
        return

    text_game_maker._wrap_print("OK, character print delay is set to %.2f "
        "seconds." % text_game_maker.info['chardelay'])

    if not text_game_maker.info['slow_printing']:
        text_game_maker._wrap_print("(but it won't do anything unless "
            "slow printing is enabled-- e.g. 'print slow' -- you fucking "
            "idiot)")

def _do_set_print_width(player, word, setting):
    if not setting or setting == "":
        text_game_maker._wrap_print("Please provide a line width between "
            "%d-%d (e.g. 'print width 60')" % (MIN_LINE_WIDTH, MAX_LINE_WIDTH))
        return

    try:
        val = int(setting)
    except ValueError:
        text_game_maker._wrap_print("Don't recognise that value for "
            "'print width'. Enter a width value as an integer (e.g. "
            "'print width 60')")
        return

    if (val < MIN_LINE_WIDTH) or (val > MAX_LINE_WIDTH):
        text_game_maker._wrap_print("Please enter a line width between "
            "%d-%d" % (MIN_LINE_WIDTH, MAX_LINE_WIDTH))
        return

    text_game_maker._wrap_print("OK, line width set to %d." % val)
    text_game_maker.wrapper.width = val

def _do_inspect(player, word, item):
    if item == '':
        _do_look(player, word, item)
        return

    target = _find_best_match_item_index(player, item)
    if not target:
        target = _find_best_match_person_index(player, item)
        if not target:
            text_game_maker._wrap_print("No %s available to %s" % (item, word))
            return

    text_game_maker.game_print(target.on_look(player))

def _do_look(player, word, item):
    if item != '':
        _do_inspect(player, word, item)
        return

    text_game_maker.game_print(player.current_state())

def _centre_line(string, line_width):
    diff = line_width - len(string)
    if diff <= 2:
        return string

    spaces = ' ' * (diff / 2)
    return spaces + string + spaces

def _int_meter(name, val, maxval):
    hp_width = 17
    scaled = int(_translate(val, 1, maxval, 1, hp_width))

    nums = "(%d/%d)" % (val, maxval)
    bar = "[" + ('=' * scaled) + (' ' * (hp_width - scaled)) + "]"

    return "%-10s%-10s %10s" % (name, nums, bar)

def _player_health_listing(player):
    return (
        _int_meter("health", player.health, player.max_health) + '\n'
        + _int_meter("energy", player.energy, player.max_energy) + '\n'
        + _int_meter("power", player.power, player.max_power)
    )

def _do_inventory_listing(player, word, setting):
    banner = "--------------- INVENTORY --------------"
    name_line = "%s %s's" % (player.title, player.name)
    fmt = "{0:33}{1:1}({2})"

    print '\n' + banner + '\n'
    print _player_health_listing(player) + '\n'

    print _centre_line(name_line, len(banner))
    print _centre_line('possessions', len(banner))
    print ("\n" + fmt).format('COINS', "", player.coins)

    if player.inventory['equipped']:
        item = player.inventory['equipped'][0]
        print ("\n" + fmt).format(item.name + " (equipped)", "", item.value)

    if player.inventory['unequipped']:
        print ''
        for item in player.inventory['unequipped']:
            print (fmt).format(item.name, "", item.value)

    print"\n----------------------------------------"

def _do_show_command_list(player, word, setting):
    print text_game_maker.get_full_controls()

def _do_help(player, word, setting):
    if not setting or setting == "":
        print text_game_maker.basic_controls
    else:
        i, cmd = _run_fsm(setting)
        if cmd:
            print cmd.help_text().rstrip('\n')

def _get_next_unused_save_id(save_dir):
    default_num = 1
    nums = [int(x.split('_')[2]) for x in os.listdir(save_dir)]

    while default_num in nums:
        default_num += 1

    return default_num

def _get_save_dir():
    return os.path.join(os.path.expanduser("~"), '.text_game_maker_saves')

def _get_save_files():
    ret = []
    save_dir = _get_save_dir()

    if os.path.exists(save_dir):
        ret = [os.path.join(save_dir, x) for x in os.listdir(save_dir)]

    return ret

def _do_load(player, word, setting):
    filename = None

    ret = _get_save_files()
    if ret:
        files = [os.path.basename(x) for x in ret]
        files.sort()
        files.append("None of these (let me enter a path to a save file)")

        index = text_game_maker.ask_multiple_choice(files,
            "Which save file would you like to load?")

        if index < 0:
            return False

        if index < (len(files) - 1):
            filename = os.path.join(_get_save_dir(), files[index])
    else:
        text_game_maker._wrap_print("No save files found. Put save files in "
            "%s, otherwise you can enter the full path to an alternate save "
            "file." % _get_save_dir())
        ret = text_game_maker.ask_yes_no("Enter path to alternate save file?")
        if ret <= 0:
            return False

    if filename is None:
        while True:
            filename = text_game_maker.read_line("Enter name of file to load",
                cancel_word="cancel")
            if filename is None:
                return False
            elif os.path.exists(filename):
                break
            else:
                text_game_maker._wrap_print("%s: no such file" % filename)

    player.load_from_file = filename
    text_game_maker._wrap_print("Loading game state from file %s."
        % player.load_from_file)
    return True

def _do_save(player, word, setting):
    filename = None
    save_dir = _get_save_dir()

    if not os.path.exists(save_dir):
        try:
            os.makedirs(save_dir)
        except OSError as e:
            if e.errno != errno.EEXIST:
                text_game_maker._wrap_print("Error (%d) creating directory %s"
                    % (e.errno, save_dir))
                return

    if player.loaded_file:
        ret = text_game_maker.ask_yes_no("overwrite file %s?"
            % os.path.basename(player.loaded_file))
        if ret < 0:
            return

    if player.loaded_file and ret:
        filename = player.loaded_file
    else:
        save_id = _get_next_unused_save_id(save_dir)
        default_name = "save_state_%03d" % save_id

        ret = text_game_maker.read_line_raw("Enter name to use for save file",
            cancel_word="cancel", default=default_name)

        if ret is None:
            return

        filename = os.path.join(save_dir, ret)

    player.save_state(filename)
    text_game_maker.game_print("Game state saved in %s." % filename)

def _is_shorthand_direction(word):
    for w in ['north', 'south', 'east', 'west']:
        if w.startswith(word):
            return w

    return None

def _parse_command(player, action):
    if action == '':
        action = text_game_maker.info['last_command']
        print '\n' + action

    if _is_shorthand_direction(action):
        _do_move(player, 'go', action)
    else:
        i, cmd = _run_fsm(action)
        if cmd:
            cmd.callback(player, action[:i].strip(), action[i:].strip())

    text_game_maker.info['last_command'] = action
    player.turns += 1

command_table = [
    (parser.PRINT_SPEED_WORDS, _do_set_print_speed, "set printing speed",
        "%s fast/slow"),

    (parser.PRINT_DELAY_WORDS, _do_set_print_delay, "set the per-character "
        " print delay when slow printing is enabled", "%s <seconds>"),

    (parser.PRINT_WIDTH_WORDS, _do_set_print_width, "set the maximum line "
        "width for game output", "%s <width>"),

    (parser.GO_WORDS, _do_move, "move the player (north/south/east/west)",
        "%s <direction>"),

    (parser.EQUIP_WORDS, _do_equip, "equip an item from your inventory",
        "%s <item>"),

    (parser.TAKE_WORDS, _do_take, "add an item to your inventory",
        "%s <item>"),

    (parser.DROP_WORDS, _do_drop, "drop an item from your inventory",
        "%s <item>"),

    (parser.SPEAK_WORDS, _do_speak, "speak with a person by name",
        "%s <person>"),

    (parser.UNEQUIP_WORDS, _do_unequip, "unequip your equipped item (if any)",
        "%s <item>"),

    (parser.EAT_WORDS, _do_eat, "eat something", "%s <item>"),

    (parser.LOOT_WORDS, _do_loot, "attempt to loot a person by name",
        "%s <person>"),

    (parser.KILL_WORDS, _do_quit, "guit the game", ""),

    (parser.SHOW_COMMAND_LIST_WORDS, _do_show_command_list, "show all game "
        "commands", ""),

    (parser.INSPECT_WORDS, _do_inspect, "examine an item in more detail",
        "%s <item>"),

    (parser.LOOK_WORDS, _do_look, "examine your current surroundings", ""),

    (parser.INVENTORY_WORDS, _do_inventory_listing, "show player's inventory",
        ""),

    (parser.HELP_WORDS, _do_help, "show basic help information", ""),

    (parser.SAVE_WORDS, _do_save, "save the current game state to a file", ""),

    (parser.LOAD_WORDS, _do_load, "load a previously saved game state file", "")
]

class MapBuilder(object):
    """
    Base class for building a tile-based map
    """

    def __init__(self, name=None, description=None):
        """
        Initialises a MapBuilder instance. When you create a MapBuilder
        object, it automatically creates the first tile, and sets it as the
        current tile to build on.

        :param str name: short name for starting Tile
        :param str description: short name for starting Tile
        """

        self.on_start = None
        self.start = Tile(name, description)
        self.current = self.start
        self.prompt = "[?]: "

    def set_on_enter(self, callback):
        """
        Set callback function to be invoked when player attempts to enter the
        current tile. The callback function should accept 3 parameters, and
        return a bool:

            def callback(player, source, dest):
                pass

            Callback parameters:

            * *player* (text_game_maker.player.Player object): player instance
            * *source* (text_game_maker.tile.Tile object): source tile (tile
              that player is trying to exit
            * *destination* (text_game_maker.tile.Tile object): destination tile
              (tile that player is trying to enter
            * *Return value* (bool): If False, player's attempt to enter the
              current tile will be blocked (silently-- up to you to print
              something if you need it here). If True, player will be allowed
              to continue normally

        :param callback: the callback function
        """

        self.current.set_on_enter(callback)

    def set_on_exit(self, callback):
        """
        Set callback function to be invoked when player attempts to exit the
        current tile. The callback should accept three parameters, and return
        a bool:

            def callback(player, source, dest):
                pass

            Callback parameters:

            * *player* (text_game_maker.player.Player object): player instance
            * *source* (text_game_maker.tile.Tile object): source tile (tile
              that player is trying to exit
            * *destination* (text_game_maker.tile.Tile object): destination tile
              (tile that player is trying to enter
            * *Return value* (bool): If False, player's attempt to exit the
              current tile will be blocked (silently-- up to you to print
              something if you need it here). If True, player will be allowed
              to continue normally.

        :param callback: the callback function
        """

        self.current.set_on_exit(callback)

    def set_on_start(self, callback):
        """
        Set callback function to be invoked when player starts a new game (i.e.
        not from a save file). Callback function should accept one parameter:

            def callback(player):
                pass

            Callback parameters:

            * *player* (text_game_maker.player.Player): player instance

        :param callback: callback function
        """

        self.on_start = callback

    def set_name(self, name):
        """
        Add short description for current tile

        :param str desc: description text
        """

        self.current.name = name

    def set_description(self, desc):
        """
        Add long description for current tile

        :param str desc: description text
        """

        self.current.description = text_game_maker._remove_leading_whitespace(desc)

    def add_item(self, item):
        """
        Add item to current tile

        :param text_game_maker.item.Item item: the item to add
        """

        if item.location not in self.current.items:
            self.current.items[item.location] = []

        item.delete()
        item.home = self.current.items[item.location]
        self.current.items[item.location].append(item)

    def add_person(self, person):
        """
        Add person to current tile

        :param text_game_maker.person.Person person: the person to add
        """

        if person.location not in self.current.people:
            self.current.people[person.location] = []

        person.delete()
        person.home = self.current.people[person.location]
        self.current.people[person.location].append(person)

    def set_locked(self):
        """
        Set the current tile to be locked. The player will not be able to
        enter a locked tile (unless some enter/exit callback unlocks it)
        """

        self.current.set_locked()

    def set_input_prompt(self, prompt):
        """
        Set the message to print when prompting a player for game input

        :param str prompt: message to print
        """

        self.prompt = prompt

    def __do_move(self, dest, name, description, tileclass):
        if dest is None:
            dest = tileclass(name, description)

        return self.current, dest

    def move_west(self, name=None, description=None, tileclass=Tile):
        """
        Create a new tile to the west of the current tile, and set the new
        tile as the current tile

        :param str name: short description of tile
        :param str description: long description of tile
        """

        old, new = self.__do_move(self.current.west, name, description, tileclass)
        self.current.west = new
        self.current = self.current.west
        self.current.east = old

    def move_east(self, name=None, description=None, tileclass=Tile):
        """
        Create a new tile to the east of the current tile, and set the new
        tile as the current tile

        :param str name: short description of tile
        :param str description: long description of tile
        """

        old, new = self.__do_move(self.current.east, name, description, tileclass)
        self.current.east = new
        self.current = self.current.east
        self.current.west = old

    def move_north(self, name=None, description=None, tileclass=Tile):
        """
        Create a new tile to the north of the current tile, and set the new
        tile as the current tile

        :param str name: short description of tile
        :param str description: long description of tile
        """

        old, new = self.__do_move(self.current.north, name, description, tileclass)
        self.current.north = new
        self.current = self.current.north
        self.current.south = old

    def move_south(self, name=None, description=None, tileclass=Tile):
        """
        Create a new tile to the south of the current tile, and set the new
        tile as the current tile

        :param str name: short description of tile
        :param str description: long description of tile
        """

        old, new = self.__do_move(self.current.south, name, description, tileclass)
        self.current.south = new
        self.current = self.current.south
        self.current.north = old

    def _get_command_delimiter(self, action):
        for i in COMMAND_DELIMITERS:
            if i in action:
                for j in COMMAND_DELIMITERS:
                    if j != i and j in action:
                        return None

                return i

        return None

    def inject_input(self, data):
        """
        Inject data into the game's input stream (as if player had typed it)

        :param str data: string of text to inject
        """

        for c in data:
            text_game_maker.input_queue.put(c)

    def _run_command_sequence(self, player, sequence):
        # Inject commands into the input queue
        lines = '\n'.join(sequence) + '\n'
        self.inject_input(lines)

        # Set the global command sequence count, so we know how many commands
        # from the chain are left in the input queue (even if a user callback
        # 'steals' some of the commands by calling read_input)
        text_game_maker.info['sequence_count'] = len(sequence)

        while text_game_maker.info['sequence_count'] > 0:
            action = text_game_maker.read_line_raw("> ").strip().lower()
            _parse_command(player, action)

        text_game_maker.info['sequence_count'] = None

    def _do_scheduled_tasks(self, player):
        for task_id in list(player.scheduled_tasks):
            callback, turns, start = player.scheduled_tasks[task_id]
            if player.turns >= (start + turns):
                if callback(player):
                    new = (callback, turns, player.turns)
                    player.scheduled_tasks[task_id] = new
                else:
                    del player.scheduled_tasks[task_id]

    def _load_state(self, player, filename):
        loaded_file = player.load_from_file
        with open(player.load_from_file, 'r') as fh:
            ret = pickle.load(fh)

        ret.loaded_file = loaded_file
        ret.load_from_file = None
        return ret

    def run_game(self):
        """
        Start running the game
        """

        for word_set, callback, desc, fmt in command_table:
            cmd = Command(word_set, callback, desc, fmt)
            for word in word_set:
                fsm.add_token(word, cmd)

        player = Player(self.start, self.prompt)
        menu_choices = ["New game", "Load game", "Controls"]

        while True:
            print "\n------------ MAIN MENU ------------\n"
            choice = text_game_maker.ask_multiple_choice(menu_choices)

            if choice < 0:
                sys.exit()

            elif choice == 0:
                if self.on_start:
                    self.on_start(player)

                text_game_maker.game_print(player.current_state())
                break

            elif choice == 1:
                if _do_load(player, '', ''):
                    break

            elif choice == 2:
                print text_game_maker.get_full_controls()

        while True:
            while True:
                if player.load_from_file:
                    player = self._load_state(player, player.load_from_file)
                    text_game_maker.game_print(player.current_state())
                    break

                raw = text_game_maker.read_line_raw("%s" % player.prompt)
                action = ' '.join(raw.split())
                self._do_scheduled_tasks(player)

                delim = self._get_command_delimiter(action)
                if delim:
                    sequence = action.lstrip(delim).split(delim)
                    self._run_command_sequence(player, sequence)
                    continue

                _parse_command(player, action.strip().lower())
