from __future__ import unicode_literals, print_function
import time
import random
import sys
import os
import json
import zlib
import pdb
import errno

from text_game_maker.tile.tile import (Tile, LockedDoor, reverse_direction,
    LockedDoorWithKeypad
)

from text_game_maker.game_objects.items import Item
from text_game_maker.player import player
from text_game_maker.tile import tile
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
    'instance': None,
    'debug_next': False
}

_format_tokens = {
    "<playername>": lambda: get_instance().player.name
}

def _debug_next():
    info['debug_next'] = True

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
    utils.printfunc(utils.get_full_controls(player.parser))

def _do_help(player, word, setting):
    text = None

    if not setting or setting == "":
        _do_show_command_list(player, word, setting)
        return

    i, cmd = utils.run_parser(player.parser, setting)
    if cmd and (not cmd.hidden):
        text = cmd.help_text()

    if text is None:
        utils._wrap_print("No help available for '%s'." % setting)
        return

    utils.printfunc(text.rstrip('\n'))

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
        return False

    if direction.startswith('to the '):
        direction = direction[7:]
    elif direction.startswith('to '):
        direction = direction[3:]

    if _move_direction(player, word, direction):
        return True

    tile = utils.find_tile(player, direction)
    if tile:
        if _move_direction(player, word, player.current.direction_to(tile)):
            return True

    utils._wrap_print("Don't know how to %s %s." % (word, direction))
    return False

def _do_craft(player, word, item):
    if not item or item == "":
        utils.game_print("What do you want to %s?" % word)
        helptext = crafting.help_text()
        if helptext:
            utils._wrap_print(helptext)

        return False

    fields = item.split()
    if (len(fields) > 1) and fields[0] == 'a':
        item = ' '.join(fields[1:])

    item = crafting.craft(item, word, player)
    if not item:
        return False

    return True

def _get_next_unused_save_id(save_dir):
    default_num = 1
    nums = []
    for f in os.listdir(save_dir):
        if not f.startswith('save_state_'):
            continue

        fields = f.split('_')
        if len(fields) != 3:
            continue

        try:
            num = int(fields[2])
        except:
            continue

        nums.append(num)

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

        ret = utils.read_path_autocomplete("Enter save file path [default: %s]: "
                % default_name)
        if not ret or ret.strip() == "":
            filename = os.path.join(save_dir, default_name)
        else:
            filename = ret

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
            "Which save file would you like to load?", default=len(files))

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
            filename = utils.read_path_autocomplete("Enter path of file to load: ")
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
    utils.set_wrap_width(val)

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
    fmt = utils.ITEM_LIST_FMT

    banner = utils.line_banner("status", bannerwidth)
    ret = ('\n' + banner + '\n\n')
    ret += (_player_health_listing(player, bannerwidth) + '\n\n')
    if player.equipped:
        ret += ((fmt + "\n\n").format(player.equipped.name + " (equipped)", "",
            player.equipped.value))

    if player.inventory:
            ret += utils.container_listing(player.inventory, fmt) + "\n"

    ret += (utils.container_listing(player.pockets, fmt, name="pockets",
            bottom_border=True) + "\n")

    utils.printfunc(ret)
    return True

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
        utils.set_builder_instance(self)
        self.reset_state_data = None
        self.on_game_run = None
        self.parser = parser
        self.start = None
        self.current = None
        random.seed(time.time())
        self.player = player.Player()

    def load_map_data(self, filename):
        """
        Load a map file saved from the map editor GUI

        :param str filename: name of map editor save file to load
        """
        with open(filename, 'rb') as fh:
            strdata = fh.read()

        decompressed = zlib.decompress(strdata).decode("utf-8")
        attrs = json.loads(decompressed)

        self.start = tile.builder(attrs[player.TILES_KEY],
                                  attrs[player.START_TILE_KEY],
                                  attrs[player.OBJECT_VERSION_KEY])

    def set_current_tile(self, tile_id):
        """
        Set the current tile to build on by tile ID

        :param str tile_id: tile ID of tile to set as current tile
        """
        self.current = tile.get_tile_by_id(tile_id)

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
        if info['debug_next']:
            info['debug_next'] = False
            pdb.set_trace()

        if action == '':
            action = utils.get_last_command()
            utils.printfunc('\n' + action)

        cmd = None
        word = None
        remaining = None

        if self._is_shorthand_direction(action):
            if not _do_move(player, 'go', action):
                return

            word = action
        else:
            i, cmd = utils.run_parser(self.parser, action)
            if not cmd:
                utils.save_sound(audio.ERROR_SOUND)
                return

            word = action[:i].strip()
            remaining = action[i:].strip()

            ret = cmd.callback(player, word, remaining)
            if not ret:
                utils.save_sound(audio.FAILURE_SOUND)
                return

        utils.flush_waiting_prints()
        utils.set_last_command(action)

        if cmd is not None:
            cmd.event.generate(player, word, remaining)

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

    def set_ground_material(self, material):
        """
        Set the material type of the ground on this tile
        :param Material material: material type
        """

        self.current.material = material

    def set_smell(self, text):
        """
        Set the text that will be printed when player types 'smell' or
        equivalent on this tile

        :param str text: text to be printed on smell command
        """

        self.current.smell_description = text

    def set_ground_smell(self, text):
        """
        Set the text that will be printed when player types 'smell ground' or
        equivalent on this tile

        :param str text: text to be printed on smell ground command
        """

        self.current.ground_smell_description = text

    def set_dark(self, value):
        """
        Set whether this tile is dark or not. Dark tiles require player to equip
        a light source

        :param bool value: True for dark, False for not dark
        """

        self.current.dark = value

    def set_name_from_north(self, name):
        """
        Set the name that will be shown when player looks at the current tile
        from an adjacent tile to the north

        :param str desc: description text
        """

        self.current.set_name_from_north(name)

    def set_name_from_south(self, name):
        """
        Set the name that will be shown when player looks at the current tile
        from an adjacent tile to the south

        :param str desc: description text
        """

        self.current.set_name_from_south(name)

    def set_name_from_east(self, name):
        """
        Set the name that will be shown when player looks at the current tile
        from an adjacent tile to the east

        :param str desc: description text
        """

        self.current.set_name_from_east(name)

    def set_name_from_west(self, name):
        """
        Set the name that will be shown when player looks at the current tile
        from an adjacent tile to the west

        :param str desc: description text
        """

        self.current.set_name_from_west(name)

    def set_name(self, name):
        """
        Add short description for current tile
        (see text_game_maker.tile.tile.Tile.set_tile_id)

        :param str desc: description text
        """

        self.current.name = name
        self.current.original_name = name

    def set_first_visit_message(self, message):
        """
        Add text to be printed only once, on the player's first visit to the
        current tile

        :param str messsage: message to show on first player visit
        """
        self.current.first_visit_message = message

    def set_first_visit_message_in_dark(self, value):
        """
        Defines whether the current tile shows a first visit message in the
        dark. if False, first visit message for current tile will be shown
        the first player is on the current tile and has a light source.

        :param bool value: value to set
        """
        self.current.first_visit_message_in_dark = value

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

    def add_keypad_door(self, prefix, name, direction, code,
            doorclass=LockedDoorWithKeypad, door_id=None, prompt=None):
        """
        Add a locked door that blocks the player from exiting the current room,
        and requires a specific code to be entered on the keypad to unlock it.

        :param str prefix: prefix for door name, e.g. "a"
        :param str name: door name, e.g. "locked door"
        :param str direction: direction to locked door from current tile, e.g.\
            "north"
        :param int code: keypad code required to unlock door
        :param doorclass: class object to instantiate for door
        :param door_id: unique ID to represent door in save files
        """
        dirs = ['north', 'south', 'east', 'west']
        if direction not in dirs:
            raise ValueError('Invalid direction: must be one of %s' % dirs)

        replace = getattr(self.current, direction)
        door = doorclass(code, prefix=prefix, name=name, src_tile=self.current, replacement_tile=replace)
        if door_id:
            door.set_tile_id(door_id)
        if prompt:
            door.set_prompt(prompt)

        setattr(self.current, direction, door)

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

    def add_enter_event_handler(self, handler):
        """
        Add a handler to be invoked when player enters the current tile

        :param handler: handler of the form ``handler(player, src, dest)``,\
            where ``player`` is the ``text_game_maker.player.player.Player``\
            instance, ``src`` is the ``text_game_maker.tile.tile.Tile``\
            instance that the player just exited, and ``dest`` is the\
            ``text_game_maker.tile.tile.Tile`` instance the player has just\
            entered
        """
        self.current.enter_event.add_handler(handler)

    def clear_enter_event_handler(self, handler):
        """
        Clear specific enter event handler attached to the current tile

        :param handler: enter event handler that was previously added to the\
            current tile
        """
        self.current.enter_event.clear_handler(handler)

    def clear_enter_event_handlers(self):
        """
        Clear all enter event handler attached to the current tile
        """
        self.current.enter_event.clear_handlers()

    def add_exit_event_handler(self, handler):
        """
        Add a handler to be invoked when player exits the current tile

        :param handler: handler of the form ``handler(player, src, dest)``,\
            where ``player`` is the ``text_game_maker.player.player.Player``\
            instance, ``src`` is the ``text_game_maker.tile.tile.Tile``\
            instance that the player just exited, and ``dest`` is the\
            ``text_game_maker.tile.tile.Tile`` instance the player has just\
            entered
        """
        self.current.exit_event.add_handler(handler)

    def clear_exit_event_handler(self, handler):
        """
        Clear specific exit event handler attached to the current tile

        :param handler: exit event handler that was previously added to the\
            current tile
        """
        self.current.exit_event.clear_handler(handler)

    def clear_exit_event_handlers(self):
        """
        Clear all exit event handler attached to the current tile
        """
        self.current.exit_event.clear_handlers()

    def add_new_game_start_event_handler(self, handler):
        """
        Add a handler to be invoked when a new game is started

        :param handler: handler to be invoked when a new game is started.\
            Handler should be of the form ``handler(player)`` where ``player``\
            is the ``text_game_maker.player.player.Player`` instance
        """
        self.player.new_game_event.add_handler(handler)

    def set_input_prompt(self, prompt):
        """
        Set the message to print when prompting a player for game input

        :param str prompt: message to print
        """

        self.player.prompt = prompt

    def __do_move(self, direction, name, description, tileclass):
        dest = getattr(self.current, direction)
        door = False
        new_tile = None
        replace = False

        if dest is None:
            new_tile = tileclass(name, description)
            setattr(self.current, direction, new_tile)
        elif dest.is_door():
            door = True
            if dest.replacement_tile is None:
                new_tile = tileclass(name, description)
                dest.replacement_tile = new_tile
            else:
                new_tile = dest.replacement_tile
        else:
            new_tile = dest

        old = self.current

        if not door and (getattr(self.current, direction) is None):
            setattr(self.current, direction, new_tile)

        self.current = new_tile
        rdir = reverse_direction(direction)
        if getattr(self.current, rdir) is None:
            setattr(self.current, rdir, old)

    def move_west(self, num=1, name=None, description=None, tileclass=Tile):
        """
        Move west by one or more tiles. On each move, if a tile does not already
        exist at the current position, a new tile will be created and set as the
        current tile to build on. If a tile already exists at the current
        position, it will be set to the current tile and no new tile will be
        created.

        :param str name: short description of tile
        :param str description: long description of tile
        :param tileclass: class object to create tile from
        :param int num: distance ot move in tiles
        """

        for _ in range(num):
            self.__do_move('west', name, description, tileclass)

    def move_east(self, num=1, name=None, description=None, tileclass=Tile):
        """
        Move east by one or more tiles. On each move, if a tile does not already
        exist at the current position, a new tile will be created and set as the
        current tile to build on. If a tile already exists at the current
        position, it will be set to the current tile and no new tile will be
        created.

        :param str name: short description of tile
        :param str description: long description of tile
        :param tileclass: class object to create tile from
        :param int num: distance ot move in tiles
        """

        for _ in range(num):
            self.__do_move('east', name, description, tileclass)

    def move_north(self, num=1, name=None, description=None, tileclass=Tile):
        """
        Move north by one or more tiles. On each move, if a tile does not
        already exist at the current position, a new tile will be created and
        set as the current tile to build on. If a tile already exists at the
        current position, it will be set to the current tile and no new tile
        will be created.

        :param str name: short description of tile
        :param str description: long description of tile
        :param tileclass: class object to create tile from
        :param int num: distance ot move in tiles
        """

        for _ in range(num):
            self.__do_move('north', name, description, tileclass)

    def move_south(self, num=1, name=None, description=None, tileclass=Tile):
        """
        Move south by one or more tiles. On each move, if a tile does not
        already exist at the current position, a new tile will be created and
        set as the current tile to build on. If a tile already exists at the
        current position, it will be set to the current tile and no new tile
        will be created.

        :param str name: short description of tile
        :param str description: long description of tile
        :param tileclass: class object to create tile from
        :param int num: distance ot move in tiles
        """

        for _ in range(num):
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
            utils.printfunc("\n> %s" % cmd)
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

        self.player.start = self.start
        self.player.current = self.start
        self.player.parser = self.parser
        menu_choices = ["New game", "Load game", "Controls"]

        while True:
            utils.printfunc("\n------------ MAIN MENU ------------\n")
            choice = utils.ask_multiple_choice(menu_choices, default=1)

            if choice < 0:
                sys.exit()

            elif choice == 0:
                if self.on_game_run:
                    self.on_game_run(self.player)

                # First, generate the new game event, to ensure any tasks
                # started here get serialized when we save the game state for
                # resets on the next line
                self.player.new_game_event.generate(self.player)

                # Save the game state as a string, to reload if the player
                # dies or resets
                self.reset_state_data = self.player.save_to_string()

                # Describe the current scene to the player
                utils.game_print(self.player.describe_current_tile())
                break

            elif choice == 1:
                if _do_load(self.player, '', ''):
                    self.reset_state_data = self.player.save_to_string()
                    break

            elif choice == 2:
                utils.printfunc(utils.get_full_controls(self.player.parser))

    def _check_flags(self):
        if self.player.load_from_file:
            filename = self.player.load_from_file
            self.player = player.load_from_file(filename)
            self.player.loaded_file = filename
            self.player.load_from_file = False
            self.player.parser = self.parser
            self.reset_state_data = self.player.save_to_string()
            utils.game_print(self.player.describe_current_tile())

        elif self.player.reset_game:
            ret = utils.ask_yes_no("Restart from the beginning?")
            if ret <= 0:
                sys.exit(0)

            self.player = player.load_from_string(self.reset_state_data)
            self.player.reset_game = False
            self.player.parser = self.parser
            self.reset_state_data = self.player.save_to_string()
            utils.game_print(self.player.describe_current_tile())

    def run_game(self):
        """
        Start running the game
        """

        self._do_init()

        while True:
            while True:
                self._check_flags()

                utils.save_sound(audio.SUCCESS_SOUND)
                raw = utils.read_line_raw(self.player.prompt)
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
