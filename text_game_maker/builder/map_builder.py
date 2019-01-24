import time
import random
import sys
import os
import fnmatch
import errno

import parser
import text_game_maker
from text_game_maker.tile.tile import Tile, LockedDoor, reverse_direction
from text_game_maker.game_objects.items import Item
from text_game_maker.player import player
from text_game_maker.audio import audio
from text_game_maker.crafting import crafting
from text_game_maker.messages import messages
from text_game_maker.utils import utils

MIN_LINE_WIDTH = 50
MAX_LINE_WIDTH = 120
COMMAND_DELIMITERS = [',', ';', '/', '\\']

BADWORDS = [
    "fuck", "shit", "cunt", "bitch", "motherfucker"
]

info = {
    'instance': None
}

_format_tokens = {
    "<playername>": lambda: get_instance().player.name
}

def add_format_tokens():
    for tok in _format_tokens:
        utils.add_format_token(tok, _format_tokens[tok])

########## built-in command handlers ##########

def _do_quit(player, word, name):
    ret = utils.ask_yes_no("really stop playing?")
    if ret < 0:
        return
    elif ret:
        sys.exit()

def _do_show_command_list(player, word, setting):
    print utils.get_full_controls(player.fsm)

def _do_help(player, word, setting):
    text = None

    if not setting or setting == "":
        utils._wrap_print("No help available for '%s'." % setting)
    else:
        i, cmd = utils.run_fsm(player.fsm, setting)
        if cmd:
            text = cmd.help_text()

        if text is None:
            utils._wrap_print("No help available for '%s'." % setting)
            return

        print text.rstrip('\n')

def _move_direction(player, word, direction):
    if 'north'.startswith(direction):
        player._move_north(word)
    elif 'south'.startswith(direction):
        player._move_south(word)
    elif 'east'.startswith(direction):
        player._move_east(word)
    elif 'west'.startswith(direction):
        player._move_west(word)
    else:
        return False

    return True

def _do_move(player, word, direction):
    if not direction or direction == "":
        utils._wrap_print("Where do you want to go?")
        return

    if direction.startswith('to the '):
        direction = direction[7:]
    elif direction.startswith('to '):
        direction = direction[3:]

    if _move_direction(player, word, direction):
        return

    tile = find_tile(player, direction)
    if tile:
        if _move_direction(player, word, player.current.direction_to(tile)):
            return

    utils._wrap_print("Don't know how to %s %s." % (word, direction))

def _do_craft(player, word, item):
    if not item or item == "":
        utils.game_print("What do you want to %s?" % word)
        helptext = crafting.help_text()
        if helptext:
            utils._wrap_print(helptext)

        return

    if not player.inventory:
        utils.save_sound(text_game_maker.audio.FAILURE_SOUND)
        utils.game_print("No bag to hold items. "
                "Nothing to craft with.")
        return

    crafting.craft(item, word, player.inventory)

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

def _do_save(player, word, setting):
    filename = None
    save_dir = _get_save_dir()

    if not os.path.exists(save_dir):
        try:
            os.makedirs(save_dir)
        except OSError as e:
            if e.errno != errno.EEXIST:
                utils._wrap_print("Error (%d) creating directory %s"
                    % (e.errno, save_dir))
                return

    if player.loaded_file:
        ret = utils.ask_yes_no("overwrite file %s?"
            % os.path.basename(player.loaded_file))
        if ret < 0:
            return

    if player.loaded_file and ret:
        filename = player.loaded_file
    else:
        save_id = _get_next_unused_save_id(save_dir)
        default_name = "save_state_%03d" % save_id

        ret = utils.read_line_raw("Enter name to use for save file",
            cancel_word="cancel", default=default_name)

        if ret is None:
            return

        filename = os.path.join(save_dir, ret)

    player.save_to_file(filename)
    utils.game_print("Game state saved in %s." % filename)

def _do_load(player, word, setting):
    filename = None

    ret = _get_save_files()
    if ret:
        files = [os.path.basename(x) for x in ret]
        files.sort()
        files.append("None of these (let me enter a path to a save file)")

        index = utils.ask_multiple_choice(files,
            "Which save file would you like to load?")

        if index < 0:
            return False

        if index < (len(files) - 1):
            filename = os.path.join(_get_save_dir(), files[index])
    else:
        utils._wrap_print("No save files found. Put save files in "
            "%s, otherwise you can enter the full path to an alternate save "
            "file." % _get_save_dir())
        ret = utils.ask_yes_no("Enter path to alternate save file?")
        if ret <= 0:
            return False

    if filename is None:
        while True:
            filename = utils.read_line("Enter name of file to load",
                cancel_word="cancel")
            if filename is None:
                return False
            elif os.path.exists(filename):
                break
            else:
                utils._wrap_print("%s: no such file" % filename)

    player.load_from_file = filename
    utils._wrap_print("Loading game state from file %s."
        % player.load_from_file)
    return True

###############################################

def _has_badword(text):
    for word in BADWORDS:
        if word in text:
            return True

    return False

def _translate(val, min1, max1, min2, max2):
    span1 = max1 - min1
    span2 = max2 - min2

    scaled = float(val - min1) / float(span1)
    return min2 + (scaled * span2)

def find_item(player, name, locations=None):
    """
    Find an item by name in the provided locations

    :param text_game_maker.player.player.Player player: player object
    :param str name: name of item to find
    :param [[text_game_maker.game_objects.items.Item]] locations: location\
        lists to search. If None, the item list of the current tile is used
    :return: found item (None if no matching item is found)
    :rtype: text_game_maker.items.Item
    """
    if name.startswith('the '):
        name = name[4:]

    if locations is None:
        locations = player.current.items.values()

    for itemlist in locations:
        for item in itemlist:
            if ((item.name.lower().startswith(name.lower())
                    or name.lower() in item.name.lower())):
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

def find_inventory_item(player, name):
    """
    Find an item by name in player's inventory

    :param text_game_maker.player.player.Player player: player object
    :param str name: name of item to search for
    :return: found item. If no matching item is found, None is returned.
    :rtype: text_game_maker.game_objects.items.Item
    """
    if not player.inventory:
        return None

    if name.startswith('the '):
        name = name[4:]

    if player.equipped:
        if player.equipped.name.startswith(name) or name in player.equipped.name:
            return player.equipped

    for item in player.inventory.items:
        if item.name.startswith(name) or name in item.name:
            return item

    return None

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
    if not player.inventory:
        return None

    if player.equipped:
        if isinstance(player.equipped, classobj):
            return player.equipped

    for item in player.inventory.items:
        if isinstance(item, classobj):
            return item

    return None

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

def _do_set_print_speed(player, word, setting):
    if not setting or setting == "":
        utils._wrap_print("Fast or slow? e.g. 'print fast'")
        return

    if 'slow'.startswith(setting):
        utils.set_slow_printing(True)
        utils._wrap_print("OK, will do.")
    elif 'fast'.startswith(setting):
        utils._wrap_print("OK, will do.")
        utils.set_slow_printing(False)
        utils._wrap_print("OK, got it.")
    else:
        utils._wrap_print("Unrecognised speed setting '%s'. Please "
            "say 'fast' or 'slow'.")

def _do_set_print_delay(player, word, setting):
    if not setting or setting == "":
        utils._wrap_print("Please provide a delay value in seconds "
                "(e.g. 'print delay 0.01')")
        return

    try:
        floatval = float(setting)
    except ValueError:
        utils._wrap_print("Don't recognise that value for "
            "'print delay'. Enter a delay value in seconds (e.g. 'print "
            "delay 0.1')")
        return

    utils.set_chardelay(floatval)
    utils._wrap_print("OK, character print delay is set to %.2f "
        "seconds." % floatval)

    if not utils.get_slow_printing():
        utils._wrap_print("(but it won't do anything unless "
            "slow printing is enabled e.g. 'print slow'")

def _do_set_audio(player, word, setting):
    if not setting or setting == "":
        utils._wrap_print("Do you want %s on or %s off?" % (word, word))
        return

    setting = setting.lower()
    if setting == 'on':
        audio.init()
    elif setting == 'off':
        audio.quit()
    else:
        utils._wrap_print("Don't understand %s setting '%s'" % (word, setting))
        return

    utils._wrap_print("OK, %s is %s." % (word, setting))

def _do_set_print_width(player, word, setting):
    if not setting or setting == "":
        utils._wrap_print("Please provide a line width between "
            "%d-%d (e.g. 'print width 60')" % (MIN_LINE_WIDTH, MAX_LINE_WIDTH))
        return

    try:
        val = int(setting)
    except ValueError:
        utils._wrap_print("Don't recognise that value for "
            "'print width'. Enter a width value as an integer (e.g. "
            "'print width 60')")
        return

    if (val < MIN_LINE_WIDTH) or (val > MAX_LINE_WIDTH):
        utils._wrap_print("Please enter a line width between "
            "%d-%d" % (MIN_LINE_WIDTH, MAX_LINE_WIDTH))
        return

    utils._wrap_print("OK, line width set to %d." % val)
    text_game_maker.utils.wrapper.width = val

def _int_meter(name, val, maxval):
    hp_width = 17
    scaled = int(_translate(val, 1, maxval, 1, hp_width))

    nums = "(%d/%d)" % (val, maxval)
    bar = "[" + ('=' * scaled) + (' ' * (hp_width - scaled)) + "]"

    return "%-10s%-10s %10s" % (name, nums, bar)

def _player_health_listing(player, width):
    ret = [
        _int_meter("health", player.health, player.max_health),
        _int_meter("energy", player.energy, player.max_energy),
        _int_meter("power", player.power, player.max_power)
    ]

    return '\n'.join([utils.centre_text(x, width) for x in ret])

def _do_inventory_listing(player, word, setting):
    bannerwidth = 50
    fmt = "      {0:33}{1:1}({2})"

    banner = utils.line_banner("status", bannerwidth)
    print '\n' + banner + '\n'
    print _player_health_listing(player, bannerwidth) + '\n'
    print utils.centre_text(("\n" + fmt).format('COINS', "",
        player.coins), bannerwidth)

    if player.inventory is None:
        print("")
        print('-' * bannerwidth)
        print("")
        print utils.centre_text('No bag to hold items', bannerwidth)
        print("")
    else:
        banner_text = "%s (%d/%d)" % (player.inventory.name,
            len(player.inventory.items), player.inventory.capacity)

        print '\n' + utils.line_banner(banner_text,
            bannerwidth) + '\n'

        if player.equipped:
            print ("\n" + fmt).format(player.equipped.name + " (equipped)", "",
                player.equipped.value)

        print("")

        if player.inventory.items:
            for item in player.inventory.items:
                print fmt.format(item.name, "", item.value)

            print("")

    print('-' * bannerwidth)

def get_instance():
    return info['instance']

class MapBuilder(object):
    """
    Base class for building a tile-based map
    """

    def __init__(self, parser):
        """
        Initialises a MapBuilder instance.

        :param text_game_maker.parser.parser.CommandParser: command parser
        """

        if info['instance']:
            raise RuntimeError("Only one %s instance allowed"
                % self.__class__.__name__)

        info['instance'] = self

        self.reset_state_data = None
        self.on_game_run = None
        self.fsm = parser
        self.start = None
        self.current = None
        self.prompt = " > "
        random.seed(time.time())
        self.player = None

    def start_map(self, name="", description=""):
        """
        Start building the map; create the first tile

        :param str name: short name for starting Tile
        :param str description: short name for starting Tile
        """

        self.start = Tile(name, description)
        self.current = self.start

    def _is_shorthand_direction(self, word):
        for w in ['north', 'south', 'east', 'west']:
            if w.startswith(word):
                return w

        return None

    def _parse_command(self, player, action):
        if action == '':
            action = utils.get_last_command()
            print '\n' + action

        if self._is_shorthand_direction(action):
            _do_move(player, 'go', action)
        else:
            i, cmd = utils.run_fsm(self.fsm, action)
            if cmd:
                cmd.callback(player, action[:i].strip(), action[i:].strip())
            else:
                utils.save_sound(audio.ERROR_SOUND)
                return

        utils.set_last_command(action)
        player.scheduler_tick()

    def set_on_game_run(self, callback):
        """
        Set callback function to be invoked when player starts a new game (i.e.
        not from a save file). Callback function should accept one parameter:

            def callback(player):
                pass

            Callback parameters:

            * *player* (text_game_maker.player.player.Player): player instance

        :param callback: callback function
        """

        self.on_game_run = callback

    def set_name(self, name):
        """
        Add short description for current tile
        (see text_game_maker.tile.tile.Tile.set_tile_id)

        :param str desc: description text
        """

        self.current.name = name

    def set_first_visit_message(self, message):
        """
        Add text to be printed only once, on the player's first visit to the
        current tile

        :param str messsage: message to show on first player visit
        """
        self.current.first_visit_message = message

    def set_tile_id(self, tile_id):
        """
        Set tile ID for current tile
        (see text_game_maker.tile.tile.Tile.set_tile_id)

        :param tile_id: tile ID
        """
        self.current.set_tile_id(tile_id)

    def set_description(self, desc):
        """
        Add long description for current tile
        (see text_game_maker.tile.tile.Tile.set_description)

        :param str desc: description text
        """

        self.current.description = utils._remove_leading_whitespace(desc)

    def add_door(self, prefix, name, direction, doorclass=LockedDoor,
            door_id=None):
        """
        Add a locked door that blocks the player from exiting the current room

        :param str prefix: prefix for door name, e.g. "a"
        :param str name: door name, e.g. "locked door"
        :param str direction: direction to locked door from current tile, e.g.\
            "north"
        :param doorclass: class object to instantiate for door
        :param door_id: unique ID to represent door in save files
        """
        dirs = ['north', 'south', 'east', 'west']
        if direction not in dirs:
            raise ValueError('Invalid direction: must be one of %s' % dirs)

        replace = getattr(self.current, direction)
        door = doorclass(prefix, name, self.current, replace)
        if door_id:
            door.set_tile_id(door_id)

        setattr(self.current, direction, door)

    def add_item(self, item):
        """
        Add item to current tile
        (see text_game_maker.tile.tile.Tile.add_item)

        :param text_game_maker.game_objects.base.Item item: the item to add
        """

        self.current.add_item(item)

    def add_items(self, items):
        """
        Add multiple items to current tile

        :param [text_game_maker.game_objects.item.Item] items: list of items\
            to add
        """

        for item in items:
            self.current.add_item(item)

    def add_person(self, person):
        """
        Add person to current tile
        (see text_game_maker.tile.tile.Tile.add_person)

        :param text_game_maker.game_objects.person.Person person: person to add
        """

        self.current.add_person(person)

    def set_input_prompt(self, prompt):
        """
        Set the message to print when prompting a player for game input

        :param str prompt: message to print
        """

        self.prompt = prompt

    def __do_move(self, direction, name, description, tileclass):
        dest = getattr(self.current, direction)
        door = False
        new_tile = None
        replace = False

        new_tile = tileclass(name, description)

        if dest is None:
            setattr(self.current, direction, new_tile)
        elif dest.is_door():
            door = True
            if dest.replacement_tile is None:
                dest.replacement_tile = new_tile

        old = self.current

        if not door:
            setattr(self.current, direction, new_tile)

        self.current = new_tile
        setattr(self.current, reverse_direction(direction), old)

    def move_west(self, name=None, description=None, tileclass=Tile):
        """
        Create a new tile to the west of the current tile, and set the new
        tile as the current tile

        :param str name: short description of tile
        :param str description: long description of tile
        """

        self.__do_move('west', name, description, tileclass)

    def move_east(self, name=None, description=None, tileclass=Tile):
        """
        Create a new tile to the east of the current tile, and set the new
        tile as the current tile

        :param str name: short description of tile
        :param str description: long description of tile
        """

        self.__do_move('east', name, description, tileclass)

    def move_north(self, name=None, description=None, tileclass=Tile):
        """
        Create a new tile to the north of the current tile, and set the new
        tile as the current tile

        :param str name: short description of tile
        :param str description: long description of tile
        """

        self.__do_move('north', name, description, tileclass)

    def move_south(self, name=None, description=None, tileclass=Tile):
        """
        Create a new tile to the south of the current tile, and set the new
        tile as the current tile

        :param str name: short description of tile
        :param str description: long description of tile
        """

        self.__do_move('south', name, description, tileclass)

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
            utils.input_queue.put(c)

    def _run_command_sequence(self, player, sequence):
        # Inject commands into the input queue
        utils.queue_command_sequence([s.strip() for s in sequence])
        cmd = utils.pop_command()

        while not cmd is None:
            print("\n> %s" % cmd)
            self._parse_command(player, cmd)
            cmd = utils.pop_command()

        utils.set_sequence_count(None)

    def _do_scheduled_tasks(self, player):
        for task_id in player.scheduled_tasks:
            callback, turns, start = player.scheduled_tasks[task_id]
            if player.turns >= (start + turns):
                if callback(player):
                    new = (callback, turns, player.turns)
                    player.scheduled_tasks[task_id] = new
                else:
                    del player.scheduled_tasks[task_id]

    def _do_init(self):
        add_format_tokens()

        self.player = player.Player(self.start, self.prompt)
        self.player.fsm = self.fsm
        menu_choices = ["New game", "Load game", "Controls"]

        while True:
            print "\n------------ MAIN MENU ------------\n"
            choice = utils.ask_multiple_choice(menu_choices)

            if choice < 0:
                sys.exit()

            elif choice == 0:
                if self.on_game_run:
                    self.on_game_run(self.player)

                utils.game_print(self.player.current_state())
                break

            elif choice == 1:
                if _do_load(self.player, '', ''):
                    break

            elif choice == 2:
                print utils.get_full_controls()

        self.reset_state_data = self.player.save_to_string()

    def _check_flags(self):
        if self.player.load_from_file:
            filename = self.player.load_from_file
            self.player = player.load_from_file(filename)
            self.player.loaded_file = filename
            self.player.load_from_file = False
            self.player.fsm = self.fsm
            self.reset_state_data = self.player.save_to_string()
            utils.game_print(self.player.current_state())

        elif self.player.reset_game:
            ret = utils.ask_yes_no("Restart from the beginning?")
            if ret <= 0:
                sys.exit(0)

            self.player = player.load_from_string(self.reset_state_data)
            self.player.reset_game = False
            self.player.fsm = self.fsm
            self.reset_state_data = self.player.save_to_string()
            utils.game_print(self.player.current_state())

    def run_game(self):
        """
        Start running the game
        """

        self._do_init()

        while True:
            while True:
                self._check_flags()

                utils.save_sound(audio.SUCCESS_SOUND)
                raw = utils.read_line_raw("%s" % self.player.prompt)
                action = ' '.join(raw.split())

                if _has_badword(action):
                    utils.game_print(messages.badword_message())
                    continue

                delim = self._get_command_delimiter(action)
                if delim:
                    sequence = action.lstrip(delim).split(delim)
                    self._run_command_sequence(self.player, sequence)
                else:
                    self._parse_command(self.player, action.strip().lower())

                sound = utils.last_saved_sound()
                if sound:
                    audio.play_sound(sound)
