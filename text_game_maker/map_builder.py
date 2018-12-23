import time
import random
import sys
import pickle
import os
import fnmatch
import errno

import parser
import text_game_maker
from text_game_maker import default_commands as defaults
from text_game_maker.tile import Tile, LockedDoor, reverse_direction
from text_game_maker.items import Item
from text_game_maker.player import Player
from text_game_maker import audio, messages

MIN_LINE_WIDTH = 50
MAX_LINE_WIDTH = 120
COMMAND_DELIMITERS = [',', ';', '/', '\\']

BADWORDS = [
    "fuck", "shit", "cunt", "bitch", "motherfucker"
]

info = {
    'instance': None
}

def _translate(val, min1, max1, min2, max2):
    span1 = max1 - min1
    span2 = max2 - min2

    scaled = float(val - min1) / float(span1)
    return min2 + (scaled * span2)

def find_item(player, name, locations=None):
    if name.startswith('the '):
        name = name[4:]

    if locations is None:
        locations = player.current.items.values()

    for itemlist in locations:
        for item in itemlist:
            if ((item.name.lower().startswith(name.lower())
                    or name.lower() in item.name.lower()) and not item.scenery):
                return item

    return None


def is_location(player, name):
    for direction in player.current.iterate_directions():
        if direction and direction.is_door() and (name in direction.name):
            return True

    for loc in player.current.items:
        if name in loc:
            return True

    return False

def get_all_items(player, locations=None, except_item=None):
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
    for loc in player.current.people:
        itemlist = player.current.people[loc]
        for item in itemlist:
            if (item.name.lower().startswith(name.lower())
                    or name.lower() in item.name.lower()):
                return item

    return None

def find_inventory_item(player, name):
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
    ret = find_inventory_item(player, name)
    if not ret:
        return find_item(player, name)

    return ret

def find_inventory_item_class(player, classobj):
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
    for item in player.inventory.items:
        if fnmatch.fnmatch(item.name, name):
            return item

    return None

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

    return '\n'.join([text_game_maker.centre_text(x, width) for x in ret])

def _do_inventory_listing(player, word, setting):
    bannerwidth = 50
    fmt = "{0:33}{1:1}({2})"

    banner = text_game_maker.line_banner("status", bannerwidth)
    print '\n' + banner + '\n'
    print _player_health_listing(player, bannerwidth) + '\n'
    print text_game_maker.centre_text(("\n" + fmt).format('COINS', "",
        player.coins), bannerwidth)

    if player.inventory is None:
        print("")
        print('-' * bannerwidth)
        print("")
        print text_game_maker.centre_text('No bag to hold items', bannerwidth)
        print("")
    else:
        banner_text = "%s (%d/%d)" % (player.inventory.name,
            len(player.inventory.items), player.inventory.capacity)

        print '\n' + text_game_maker.line_banner(banner_text,
            bannerwidth) + '\n'

        if player.equipped:
            print ("\n" + fmt).format(player.equipped.name + " (equipped)", "",
                player.equipped.value)

        print("")

        if player.inventory.items:
            for item in player.inventory.items:
                print text_game_maker.centre_text((fmt).format(item.name, "",
                    item.value), bannerwidth)

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

        :param text_game_maker.parser.CommandParser: command parser
        """

        if info['instance']:
            raise RuntimeError("Only one %s instance allowed"
                % self.__class__.__name__)

        info['instance'] = self
        self.on_game_run = None
        self.fsm = parser
        self.start = None
        self.current = None
        self.prompt = " > "
        random.seed(time.time())
        self.player = None

    def start_map(self, name, description):
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
            action = text_game_maker.info['last_command']
            print '\n' + action

        if action in BADWORDS:
            text_game_maker.game_print(messages.badword_message())
            return

        if self._is_shorthand_direction(action):
            defaults._do_move(player, 'go', action)
        else:
            i, cmd = text_game_maker.run_fsm(self.fsm, action)
            if cmd:
                cmd.callback(player, action[:i].strip(), action[i:].strip())
            else:
                text_game_maker.save_sound(audio.ERROR_SOUND)

        text_game_maker.info['last_command'] = action
        player.turns += 1

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

    def set_on_game_run(self, callback):
        """
        Set callback function to be invoked when player starts a new game (i.e.
        not from a save file). Callback function should accept one parameter:

            def callback(player):
                pass

            Callback parameters:

            * *player* (text_game_maker.player.Player): player instance

        :param callback: callback function
        """

        self.on_game_run = callback

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

    def add_door(self, prefix, name, direction, doorclass=LockedDoor):
        dirs = ['north', 'south', 'east', 'west']
        if direction not in dirs:
            raise ValueError('Invalid direction: must be one of %s' % dirs)

        replace = getattr(self.current, direction)
        door = doorclass(prefix, name, self.current, replace)
        setattr(self.current, direction, door)

    def add_item(self, item):
        """
        Add item to current tile

        :param text_game_maker.base.Item item: the item to add
        """

        self.current.add_item(item)

    def add_items(self, items):
        """
        Add multiple items to current tile

        :param [text_game_maker.item.Item] items: list of items to add
        """

        for item in items:
            self.current.add_item(item)

    def add_person(self, person):
        """
        Add person to current tile

        :param text_game_maker.person.Person person: the person to add
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
            text_game_maker.input_queue.put(c)

    def _run_command_sequence(self, player, sequence):
        # Inject commands into the input queue
        text_game_maker.queue_command_sequence([s.strip() for s in sequence])
        cmd = text_game_maker.pop_command()

        while not cmd is None:
            print("\n> %s" % cmd)
            self._parse_command(player, cmd)
            cmd = text_game_maker.pop_command()

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

        self.player = Player(self.start, self.prompt)
        self.player.fsm = self.fsm
        menu_choices = ["New game", "Load game", "Controls"]

        while True:
            print "\n------------ MAIN MENU ------------\n"
            choice = text_game_maker.ask_multiple_choice(menu_choices)

            if choice < 0:
                sys.exit()

            elif choice == 0:
                if self.on_game_run:
                    self.on_game_run(self.player)

                text_game_maker.game_print(self.player.current_state())
                break

            elif choice == 1:
                if defaults._do_load(self.player, '', ''):
                    break

            elif choice == 2:
                print text_game_maker.get_full_controls()

        while True:
            while True:
                if self.player.load_from_file:
                    self.player = self._load_state(self.player, self.player.load_from_file)
                    text_game_maker.game_print(self.player.current_state())
                    break

                text_game_maker.save_sound(audio.SUCCESS_SOUND)
                raw = text_game_maker.read_line_raw("%s" % self.player.prompt)
                action = ' '.join(raw.split())
                self._do_scheduled_tasks(self.player)

                delim = self._get_command_delimiter(action)
                if delim:
                    sequence = action.lstrip(delim).split(delim)
                    self._run_command_sequence(self.player, sequence)
                else:
                    self._parse_command(self.player, action.strip().lower())

                audio.play_sound(text_game_maker.last_saved_sound())
