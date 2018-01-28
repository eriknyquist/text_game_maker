import time
import sys
import pickle
import os
import fnmatch
import errno

import text_game_maker
from text_game_maker.tile import Tile
from text_game_maker.item import Item
from text_game_maker.player import Player

MIN_LINE_WIDTH = 50
MAX_LINE_WIDTH = 120
COMMAND_DELIMITERS = [',', ';', '/', '\\']

def _unrecognised(player, val):
    text_game_maker._wrap_print('Unrecognised command "%s"' % val)

def _do_move(player, word, direction):
    if not direction or direction.strip() == "":
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
        _unrecognised(player, direction)

def _find_closest_match_item_index(player, name):
    for loc in player.current.items:
        itemlist = player.current.items[loc]
        for i in range(len(itemlist)):
            curr = itemlist[i]

            if curr.name.lower().startswith(name.lower()):
                return curr, loc, i

    for loc in player.current.items:
        itemlist = player.current.items[loc]
        for i in range(len(itemlist)):
            curr = itemlist[i]

            if name.lower() in curr.name.lower():
                return curr, loc, i

    return None, None, -1

def _find_wildcard_match(player, name):
    ret = []
    for loc in player.current.items:
        itemlist = player.current.items[loc]
        for i in range(len(itemlist)):
            if fnmatch.fnmatch(itemlist[i].name, name):
                return itemlist[i], loc, i

    return None, None, None

def _find_closest_match_person_index(player, name):
    for loc in player.current.people:
        itemlist = player.current.people[loc]
        for i in range(len(itemlist)):
            curr = itemlist[i]

            if curr.name.lower().startswith(name.lower()):
                return curr, loc, i

    for loc in player.current.people:
        itemlist = player.current.people[loc]
        for i in range(len(itemlist)):
            curr = itemlist[i]

            if name.lower() in curr.name.lower():
                return curr, loc, i

    return None, None, -1

def _take(player, item, loc, i):
    # If on_take callback returns false, abort adding this item
    if item.on_take and not item.on_take(player):
        return False

    player.inventory_items[item.name] = item
    del player.current.items[loc][i]
    return True

def _do_take(player, word, item_name):
    if not item_name or item_name.strip() == "":
        text_game_maker._wrap_print("What do you want to take?")
        return

    if '*' in item_name:
        added = []
        item = ' '

        while item:
            item, loc, i = _find_wildcard_match(player, item_name)
            if item and _take(player, item, loc, i):
                added.append(item.name)

        if not added:
            text_game_maker._wrap_print("No matcing items to %s" % word)
            return

        msg = text_game_maker.list_to_english(added)
    else:
        item, loc, i  = _find_closest_match_item_index(player, item_name)
        if i < 0:
            text_game_maker._wrap_print("No %s available to %s" % (item_name, word))
            return

        msg = item.name
        if not _take(player, item, loc, i):
            return

    text_game_maker.game_print('%s added to inventory' % msg)
    return

def _find_inventory_wildcard(player, name):
    for n in player.inventory_items:
        if n != 'equipped' and fnmatch.fnmatch(n, name):
            return player.inventory_items[n], n

    return None, None

def _drop(player, n):
    # Place item on the floor in current room
    player.inventory_items[n].location = "on the floor"
    player.current.add_item(player.inventory_items[n])

    # Clear equipped slot if dropped item was equipped
    if player.inventory_items['equipped'] == player.inventory_items[n]:
        player.inventory_items['equipped'] = None

    del player.inventory_items[n]

def _do_drop(player, word, item_name):
    if not item_name or item_name.strip() == "":
        text_game_maker._wrap_print("What do you want to drop?")
        return

    if '*' in item_name:
        added = []
        item = ' '

        while item:
            item, n = _find_inventory_wildcard(player, item_name)
            if item:
                added.append(n)
                _drop(player, n)

        if not added:
            text_game_maker._wrap_print("No matching items to %s." % word)
            return

        msg = text_game_maker.list_to_english(added)
    else:
        msg = None
        for i in player.inventory_items:
            if i.startswith(item_name) or item_name in i:
                msg = i
                _drop(player, i)
                break

        if not msg:
            text_game_maker._wrap_print("No %s in your inventory to %s"
                % (item_name, word))
            return

    text_game_maker.game_print("Dropped %s" % msg)

def _do_speak(player, word, name):
    if not name or name.strip() == "":
        text_game_maker._wrap_print("Who do you want to speak to?")
        return

    p, loc, i = _find_closest_match_person_index(player, name)
    if i < 0:
        text_game_maker._wrap_print("Don't know who %s is" % name)
        return

    text_game_maker.game_print('You speak to %s.' % p.name)
    if p.is_alive():
        response = p.on_speak(p, player)
        if response:
            p.say(response)
    else:
        text_game_maker.game_print('%s says nothing.' % p.name)

def _do_quit(player, word, name):
    ret = "z"
    while (not 'yes'.startswith(ret)) and (not 'no'.startswith(ret)):
        ret = text_game_maker.ask_yes_no("really stop playing?")
        if ret < 0:
            return
        elif ret:
            sys.exit()

def _do_equip(player, word, item_name):
    if not item_name or item_name.strip() == "":
        text_game_maker._wrap_print("Which inventory item do you want to %s?"
            % word)
        return

    for i in player.inventory_items:
        if i.startswith(item_name) or item_name in i:
            text_game_maker.game_print("Equipped %s" % i)
            player.inventory_items['equipped'] = player.inventory_items[i]
            return

    text_game_maker._wrap_print("No %s in your inventory to %s"
        % (item_name, word))

def _do_unequip(player, word, fields):
    equipped = player.inventory_items['equipped']
    if not equipped:
        text_game_maker.game_print('Nothing is currently equipped')
    else:
        player.inventory_items['equipped'] = None
        text_game_maker.game_print('%s unequipped' % equipped.name)

def _do_loot(player, word, name):
    if not name or name.strip() == "":
        text_game_maker._wrap_print("Who do you want to %s?" % word)
        return

    p, loc, i = _find_closest_match_person_index(player, name)
    if p.is_alive():
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
        print ("\nWhat do you want to change about printing?%s" %
            text_game_maker.get_print_controls())
        return

    if 'slow'.startswith(setting):
        text_game_maker.info['slow_printing'] = True
        text_game_maker._wrap_print("OK, will do.")
    elif 'fast'.startswith(setting):
        text_game_maker.info['slow_printing'] = False
        text_game_maker._wrap_print("OK, got it.")
    elif setting.startswith('delay'):
        fields = setting.split()
        if len(fields) < 2:
            text_game_maker._wrap_print("'delay' requires an extra parameter. "
                "Please provide a delay value in seconds (e.g. 'print delay "
                "0.01')")
            return

        try:
            text_game_maker.info['chardelay'] = float(fields[1])
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

    elif setting.startswith('width'):
        fields = setting.split()
        if len(fields) < 2:
            text_game_maker._wrap_print("'width' requires an extra parameter. "
            "Please provide a line width between %d-%d (e.g. 'print width 60')"
                % (MIN_LINE_WIDTH, MAX_LINE_WIDTH))
            return

        try:
            val = int(fields[1])
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

    else:
        text_game_maker._wrap_print("Unrecognised print command")

def _do_inspect(player, word, item):
    if item == '':
        _do_look(player, word, item)
        return

    target, loc, i = _find_closest_match_item_index(player, item)
    if i < 0:
        target, loc, i = _find_closest_match_person_index(player, item)
        if i < 0:
            text_game_maker._wrap_print("No %s available to %s" % (item, word))
            return

    text_game_maker.game_print(target.on_look(target, player))

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
        files.append("None of these (let me enter a path)")

        index = text_game_maker.ask_multiple_choice(files,
            "Which save file would you like to load?")

        if index < 0:
            return False

        if index < (len(files) - 1):
            filename = ret[index]
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
    (text_game_maker.INSPECT_WORDS, _do_inspect),
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

        self.current.items[item.location].append(item)

    def add_person(self, person):
        """
        Add person to current tile

        :param text_game_maker.person.Person person: the person to add
        """

        if person.location not in self.current.people:
            self.current.people[person.location] = []

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
            action = text_game_maker.read_line_raw("> ").strip().lower()
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

                action = text_game_maker.read_line_raw("%s" % player.prompt)
                self._do_scheduled_tasks(player)

                delim = self._get_command_delimiter(action)
                if delim:
                    sequence = action.lstrip(delim).split(delim)
                    self._run_command_sequence(player, sequence)
                    continue

                _parse_command(player, action.strip().lower())
