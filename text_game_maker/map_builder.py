import time
import sys
import pickle
import os
import errno

import text_game_maker
from text_game_maker.tile import Tile
from text_game_maker.player import Player

COMMAND_DELIMITERS = [',', ';', '/', '\\']

def _unrecognised(player, val):
    print '\nUnrecognised command "%s"' % val

def _do_move(player, word, direction):
    if not direction or direction.strip() == "":
        print "\nWhere do you want to go?"
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
        _unrecognised(player, direction)

def _do_take(player, word, item_name):
    if not item_name or item_name.strip() == "":
        print "\nWhat do you want to take?"
        return

    for i in range(len(player.current.items)):
        # Find the mentioned item in this tile's list of items
        curr = player.current.items[i]
        if (curr.name.startswith(item_name) or (item_name in curr.name)):
            # If on_take callback returns false, abort adding this item
            if curr.on_take and not curr.on_take(player):
                return

            player.inventory_items[curr.name] = curr
            text_game_maker.game_print('\n%s added to inventory' % curr.name)
            del player.current.items[i]
            return

    print "\n%s: no such item" % item_name

def _do_drop(player, word, item_name):
    if not item_name or item_name.strip() == "":
        print "\nWhat do you want to drop?"
        return

    for i in player.inventory_items:
        if i.startswith(item_name) or item_name in i:
            # Place item on the floor in current room
            player.inventory_items[i].description = "on the floor"
            player.current.items.append(player.inventory_items[i])

            # Clear equipped slot if dropped item was equipped
            if player.inventory_items['equipped'] == player.inventory_items[i]:
                player.inventory_items['equipped'] = None

            del player.inventory_items[i]
            text_game_maker.game_print("\nDropped %s" % i)
            return

    print "\n%s: no such item in inventory" % item_name

def _do_speak(player, word, name):
    if not name or name.strip() == "":
        print "\nWho do you want to speak to?"
        return

    for p in player.current.people:
        if p.name.lower().startswith(name):
            if p.is_alive():
                response = p.on_speak(p, player)
                if response:
                    p.say(response)
            else:
                text_game_maker.game_print('\n%s says nothing. %s is dead.'
                    % (p.name, p.name))

            return

    print "\n%s: no such person" % name

def _do_quit(player, word, name):
    ret = "z"
    while (not 'yes'.startswith(ret)) and (not 'no'.startswith(ret)):
        ret = text_game_maker.read_line("\n[really stop playing? (yes/no)]: ")

        print ret
        if 'yes'.startswith(ret.lower()):
            sys.exit()
        elif 'no'.startswith(ret.lower()):
            return

def _do_equip(player, word, item_name):
    if not item_name or item_name.strip() == "":
        print "\nWhich inventory item do you want to equip?"
        return

    for i in player.inventory_items:
        if i.startswith(item_name) or item_name in i:
            text_game_maker.game_print("\nEquipped %s" % i)
            player.inventory_items['equipped'] = player.inventory_items[i]
            return

    print "\n%s: no such item in inventory" % item_name

def _do_unequip(player, word, fields):
    equipped = player.inventory_items['equipped']
    if not equipped:
        text_game_maker.game_print('\nNothing is currently equipped')
    else:
        player.inventory_items['equipped'] = None
        text_game_maker.game_print('\n%s unequipped' % equipped.name)

def _do_loot(player, word, name):
    if not name or name.strip() == "":
        print "\nWho do you want to %s?" % word
        return

    for p in player.current.people:
        if p.name.lower().startswith(name):
            if p.is_alive():
                text_game_maker.game_print("\nYou are dead.")
                text_game_maker.game_print("\nYou were caught trying to %s %s."
                    % (word, p.name))
                text_game_maker.game_print("\n%s didn't like this, and killed "
                    "you.\n" % p.name)
                sys.exit()
            else:
                player._loot(word, p)

def _do_set_print_speed(player, word, setting):
    if not setting or setting == "":
        print ("\nWhat printing speed would you like? (e.g. "
            "'print fast' or 'print slow')")
        return

    if 'slow'.startswith(setting):
        text_game_maker.info['slow_printing'] = True
        print "\nOK, will do."
    elif 'fast'.startswith(setting):
        text_game_maker.info['slow_printing'] = False
        print "\nOK, got it."
    elif setting.startswith('delay'):
        fields = setting.split()
        if len(fields) < 2:
            print("\n'delay' requires an extra argument. Please provide a delay"
                " value in seconds (e.g. 0.01)")
        else:
            try:
                text_game_maker.info['chardelay'] = float(fields[1])
            except ValueError:
                print("\nDon't recognise that value for 'print delay'.\n"
                    "Enter a delay value in seconds (e.g. 'print delay 0.1')")
            else:
                print ("\nOK, character print delay is set to %.2f seconds."
                    % text_game_maker.info['chardelay'])
                if not text_game_maker.info['slow_printing']:
                    print("(but it won't do anything unless slow printing is\n"
                        " enabled-- e.g. 'print slow' -- you fucking idiot)")
    else:
        print("\nUnrecognised print speed-- please say 'print fast' "
            "or 'print slow'")

def _do_look(player, word, setting):
    print player.current_state()

def _centre_line(string, line_width):
    diff = line_width - len(string)
    if diff <= 2:
        return string

    spaces = ' ' * (diff / 2)
    return spaces + string + spaces

def _do_inventory_listing(player, word, setting):
    banner = "--------------- INVENTORY ---------------"
    name_line = "%s %s's" % (player.title, player.name)

    print '\n' + banner + '\n'
    print _centre_line(name_line, len(banner))
    print _centre_line('possessions', len(banner)) + '\n'
    print "\n{0:35}{1:1}({2})".format('COINS', "", player.coins)

    if len(player.inventory_items) > 1:
        print ''
        for i in player.inventory_items:
            if i == 'equipped':
                continue

            item = player.inventory_items[i]
            msg = item.name

            if player.inventory_items[i] is player.inventory_items['equipped']:
                msg += " (equipped)"

            print "{0:35}{1:1}({2})".format(msg, "", item.value)

    print"\n-----------------------------------------"

def _do_show_command_list(player, word, setting):
    print text_game_maker.get_full_controls()

def _do_help(player, word, setting):
    print text_game_maker.basic_controls

def _check_word_set(word, word_set):
    for w in word_set:
        if word.startswith(w):
            return w

    return None

def _get_next_unused_save_id(save_dir):
    default_num = 0
    nums = [int(x.split('_')[2]) for x in os.listdir(save_dir)]

    while default_num in nums:
        default_num += 1

    return default_num

def _get_save_dir():
    return os.path.join(os.path.expanduser("~"), '.text_game_maker_saves')

def _do_load(player, word, setting):
    filename = None
    save_dir = _get_save_dir()

    if os.path.exists:
        files = os.listdir(save_dir)
        files.append("None of these (let me enter the file path)")

        index = text_game_maker.ask_multiple_choice(files,
            "Which save file would you like to load?")

        if index < 0:
            return

        if index < (len(files) - 1):
            filename = os.path.join(save_dir, files[index])

    if filename is None:
        while True:
            filename = text_game_maker.read_line("\nEnter name of file to load "
                "(or 'cancel'): ")
            if 'cancel'.startswith(filename):
                return
            elif os.path.exists(filename):
                break
            else:
                print "\n%s: no such file" % filename

    player.load_from_file = filename
    print ("\nLoading game state from file %s." % player.load_from_file)

def _do_save(player, word, setting):
    filename = None
    save_dir = _get_save_dir()

    if not os.path.exists(save_dir):
        try:
            os.makedirs(save_dir)
        except OSError as e:
            if e.errno != errno.EEXIST:
                print "\nError (%d) creating directory %s" % (e.errno, save_dir)
                return

    if player.loaded_file and (text_game_maker.ask_yes_no(
            "[overwrite file %s (yes/no) ?]: "
            % os.path.basename(player.loaded_file))):
        filename = player.loaded_file
    else:
        save_id = _get_next_unused_save_id(save_dir)
        default = "save_state_%03d" % save_id

        filename = text_game_maker.read_line_raw(
            "Enter name to use for save file [default: %s]: " % default)

        if filename == "":
            filename = os.path.join(save_dir, default)

    player.save_state(filename)
    text_game_maker.game_print("\nGame state saved in %s." % filename)

def _is_shorthand_direction(word):
    for w in ['north', 'south', 'east', 'west']:
        if w.startswith(word):
            return w

    return None

def _parse_command(player, action):
    if action == '':
        action = text_game_maker.info['last_command']
        print '\n' + action

    fields = [f.strip() for f in action.split()]

    for word_set, task in command_table:
        ret = _check_word_set(action, word_set)
        if ret:
            task(player, ret, action[len(ret):].strip())
            text_game_maker.info['last_command'] = action
            return

    if _is_shorthand_direction(action):
        _do_move(player, 'go', action)
    else:
        _unrecognised(player, fields[0])
        return

    text_game_maker.info['last_command'] = action

command_table = [
    (text_game_maker.SET_PRINT_WORDS, _do_set_print_speed),
    (text_game_maker.GO_WORDS, _do_move),
    (text_game_maker.EQUIP_WORDS, _do_equip),
    (text_game_maker.TAKE_WORDS, _do_take),
    (text_game_maker.DROP_WORDS, _do_drop),
    (text_game_maker.SPEAK_WORDS, _do_speak),
    (text_game_maker.UNEQUIP_WORDS, _do_unequip),
    (text_game_maker.LOOT_WORDS, _do_loot),
    (text_game_maker.KILL_WORDS, _do_quit),
    (text_game_maker.SHOW_COMMAND_LIST_WORDS, _do_show_command_list),
    (text_game_maker.LOOK_WORDS, _do_look),
    (text_game_maker.INVENTORY_WORDS, _do_inventory_listing),
    (text_game_maker.HELP_WORDS, _do_help),
    (text_game_maker.SAVE_WORDS, _do_save),
    (text_game_maker.LOAD_WORDS, _do_load)
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
        current tile. The callback function should accept 3 arguments:

            callback(player, source, dest):

        * *player* (text_game_maker.player.Player object): player instance
        * *source* (text_game_maker.tile.Tile object): source tile (tile that
          player is trying to exit
        * *destination* (text_game_maker.tile.Tile object): destination tile
          (tile that player is trying to enter
        * *Return value* (bool): If False, player's attempt to enter the
          current tile will be blocked (silently-- up to you to print something
          if you need it here). If True, player will be allowed to continue
          normally

        :param callback: the callback function
        """

        self.current.on_enter = callback

    def set_on_exit(self, callback):
        """
        Set callback function to be invoked when player attempts to enter the
        current tile. The callback should accept three  arguments:

            callback(player, source, dest):

        * *player* (text_game_maker.player.Player object): player instance
        * *source* (text_game_maker.tile.Tile object): source tile (tile that
          player is trying to exit
        * *destination* (text_game_maker.tile.Tile object): destination tile
          (tile that player is trying to enter
        * *Return value* (bool): If False, player's attempt to exit the
          current tile will be blocked (silently-- up to you to print something
          if you need it here). If True, player will be allowed to continue
          normally.


        :param callback: the callback function
        """

        self.current.on_exit = callback

    def set_on_start(self, callback):
        """
        Set callback function to be invoked when player starts a new game (i.e.
        not from a save file). Callback function should accept one argument:

            def callback(player):
                pass

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

        self.current.items.append(item)

    def add_person(self, person):
        """
        Add person to current tile

        :param text_game_maker.person.Person person: the person to add
        """

        self.current.people.append(person)

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

    def __do_move(self, dest, name, description):
        if dest is None:
            dest = Tile(name, description)

        return self.current, dest

    def move_west(self, name=None, description=None):
        """
        Create a new tile to the west of the current tile, and set the new
        tile as the current tile

        :param str name: short description of tile
        :param str description: long description of tile
        """

        old, new = self.__do_move(self.current.west, name, description)
        self.current.west = new
        self.current = self.current.west
        self.current.east = old

    def move_east(self, name=None, description=None):
        """
        Create a new tile to the east of the current tile, and set the new
        tile as the current tile

        :param str name: short description of tile
        :param str description: long description of tile
        """

        old, new = self.__do_move(self.current.east, name, description)
        self.current.east = new
        self.current = self.current.east
        self.current.west = old

    def move_north(self, name=None, description=None):
        """
        Create a new tile to the north of the current tile, and set the new
        tile as the current tile

        :param str name: short description of tile
        :param str description: long description of tile
        """

        old, new = self.__do_move(self.current.north, name, description)
        self.current.north = new
        self.current = self.current.north
        self.current.south = old

    def move_south(self, name=None, description=None):
        """
        Create a new tile to the south of the current tile, and set the new
        tile as the current tile

        :param str name: short description of tile
        :param str description: long description of tile
        """

        old, new = self.__do_move(self.current.south, name, description)
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
            action = text_game_maker.read_line_raw("\n> ").strip().lower()
            _parse_command(player, action)

        text_game_maker.info['sequence_count'] = None

    def _do_scheduled_tasks(self, player):
        for task_id in list(player.scheduled_tasks):
            callback, seconds, start = player.scheduled_tasks[task_id]
            if time.time() >= (start + seconds):
                callback(player)
                del player.scheduled_tasks[task_id]

    def _reset_scheduled_tasks(self, player):
        new = {}
        for i in player.scheduled_tasks:
            callback, seconds, start = player.scheduled_tasks[i]
            new[i] = (callback, seconds, time.time())

        player.scheduled_tasks = new

    def _load_state(self, player, filename):
        loaded_file = player.load_from_file
        with open(player.load_from_file, 'r') as fh:
            ret = pickle.load(fh)

        self._reset_scheduled_tasks(ret)
        ret.loaded_file = loaded_file
        ret.load_from_file = None
        return ret

    def run_game(self):
        """
        Start running the game
        """

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
                _do_load(player, '', '')
                break

            elif choice == 2:
                print text_game_maker.get_full_controls()

        while True:
            while True:
                if player.load_from_file:
                    player = self._load_state(player, player.load_from_file)
                    text_game_maker.game_print(player.current_state())
                    break

                action = text_game_maker.read_line_raw("\n%s" % player.prompt)
                self._do_scheduled_tasks(player)

                delim = self._get_command_delimiter(action)
                if delim:
                    sequence = action.lstrip(delim).split(delim)
                    self._run_command_sequence(player, sequence)
                    continue

                _parse_command(player, action.strip().lower())
