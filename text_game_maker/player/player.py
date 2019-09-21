import time
import zlib
import json
import sys

import text_game_maker

from text_game_maker.audio import audio
from text_game_maker.game_objects.living import LivingGameEntity
from text_game_maker.game_objects import __object_model_version__
from text_game_maker.game_objects.items import SmallBag, Lighter, Coins
from text_game_maker.crafting import crafting
from text_game_maker.utils import utils
from text_game_maker.tile import tile
from text_game_maker.messages import messages
from text_game_maker.materials.materials import Material, get_properties
from text_game_maker.event.event import Event

OBJECT_VERSION_KEY = '_object_model_version'
CRAFTABLES_KEY = '_craftables_data'
TILES_KEY = '_tile_list'
START_TILE_KEY = 'start'
MOVE_ENERGY_COST = 0.25

def _encode_for_zlib(data):
    if (sys.version_info > (3, 0)):
        return bytes(data, encoding="utf8")

    return data

def _old_object_model_warning(version):
    utils.printfunc("\n" + utils.line_banner("WARNING") + "\n\n" +
        utils._wrap_text("the save state you are loading contains an "
        "old object model version (%s). It can be be migrated to the current "
        "version (%s), but any future saves will not be playable when an "
        "object model version lower than %s is in use" % (version,
        __object_model_version__, __object_model_version__)) + "\n" +
        "\n" + utils.line_banner("WARNING"))

def load_from_string(strdata, compression=True):
    """
    Load a serialized state from a string and create a new player instance

    :param str strdata: string data to load
    :param bool compression: whether data is compressed
    :return: new Player instance
    :rtype: text_game_maker.player.player.Player
    """
    if compression:
        strdata = zlib.decompress(strdata).decode("utf-8")

    data = json.loads(strdata)
    version = data[OBJECT_VERSION_KEY]
    del data[OBJECT_VERSION_KEY]

    if version != __object_model_version__:
        _old_object_model_warning(version)

    player = Player()
    player.set_attrs(data, version)
    return player

def load_from_file(filename, compression=True):
    """
    Load a serialized state from a file and create a new player instance

    :param str filename: name of save file to read
    :param bool compression: whether data is compressed
    :return: new Player instance
    :rtype: text_game_maker.player.player.Player
    """

    with open(filename, 'rb') as fh:
        return load_from_string(fh.read(), compression)

class Player(LivingGameEntity):
    """
    Base class to hold player related methods & data
    """

    skip_attrs = ["parser", "new_game_event"]

    def __init__(self, start_tile=None, input_prompt=None):
        """
        :param text_game_maker.game_objects.tile.Tile start_tile: Starting tile
        :param str input_prompt: Custom string to prompt player for game input
        """

        super(Player, self).__init__()

        self.new_game_event = Event()
        self.material = Material.SKIN
        self.smell_description = None
        self.taste_description = None

        self.parser = None
        self.turns = 0
        self.max_health = 100
        self.max_energy = 100
        self.max_power = 100

        self.move_history = []
        self.health = self.max_health
        self.energy = 25
        self.power = 10

        self.loaded_file = None
        self.load_from_file = None
        self.reset_game = None
        self.start = start_tile
        self.current = start_tile
        self.prompt = input_prompt

        self.max_task_id = 0xffff
        self.task_id = 0
        self.scheduled_tasks = {}

        self.equipped = None
        self.inventory = None
        self.name = "john"

        self.pockets = SmallBag("", "your pockets")
        self.pockets.capacity = 2
        self.pockets.prep = "your pockets"

        lighter = Lighter()
        self.pockets.add_item(lighter)

    def add_coins(self, value=1):
        """
        Give player some coins

        :param int value: number of coins to add
        """
        Coins(value=value).add_to_player_inventory(self)

    def remove_coins(self, value=1):
        """
        Take some coins from player

        :param int value: number of coins to remove
        """
        coins = utils.find_inventory_item_class(self, Coins)
        if not coins:
            return

        coins.decrement(value)

    def sell_item_to(self, person):
        """
        Show player a listing of this person's shopping list, and allow player
        to sell something to person if the player has it

        :param text_game_maker.game_objects.person.Person person: person object
        """
        if not person.shopping_list:
            utils.game_print("%s is not interested in buying anything.")
            return

        names = person.shopping_list.keys()
        choices = ['%s (%d coins)' % (x, person.shopping_list[x]) for x in names]
        item = None
        coins = None

        while True:
            ret = utils.ask_multiple_choice(choices,
                    "Can you sell any of these items?")
            if ret < 0:
                utils.game_print("Cancelled.")
                return

            name = names[ret]
            price = person.shopping_list[name]

            item = utils.find_inventory_item(self, name)
            if not item:
                utils.game_print("You don't have %s to sell." % name)
                continue

            ret = utils.ask_yes_no("Do you want to sell %s for %d coins?"
                    % (item.prep, price))
            if ret != 1:
                utils.game_print("Cancelled.")
                continue

            self.add_coins(price)
            item.value = price * 2
            person.add_item(item)
            utils.game_print("You sell %s for %d coins." % (item.prep, price))

    def buy_item_from(self, person):
        """
        Show player a listing of items this person has and allow them to select
        one to purchase (if they have enough coins)

        :param text_game_maker.game_objects.person.Person person: person object
        """
        if not person.items:
            utils.game_print("%s has nothing to sell." % person.name)
            return

        while True:
            coins = utils.find_inventory_item_class(self, Coins)
            if coins:
                numcoins = coins.value
            else:
                numcoins = 0

            items = [x for x in person.items if not isinstance(x, Coins)]
            utils.game_print("You have %d coins." % numcoins)
            names = ["%s (%d coins)" % (x.name, x.value) for x in items]
            ret = utils.ask_multiple_choice(names, "Which item do you want to buy?")
            if ret < 0:
                utils.game_print("Cancelled.")
                return

            item = items[ret]

            if not coins:
                utils.game_print("You don't have any coins to buy %s" % item.prep)
                continue

            if coins.value < item.value:
                utils.game_print("You don't have enough coins to buy %s"
                    % item.prep)
                continue

            ret = utils.ask_yes_no("Do you want to buy %s for %d coins?"
                % (item.prep, item.value))

            if ret != 1:
                utils.game_print("Cancelled.")
                return

            coins.decrement(item.value)
            person.add_coins(item.value)
            item.add_to_player_inventory(self)
            utils.game_print("You bought %s." % item.prep)

    def injure(self, health_points=1):
        """
        Injure player by removing a specific number of health points. Player
        will die if resulting health is less than or equal to 0.

        param int health_points: number of health points to remove from player
        """
        msg = "You have lost %d health point" % health_points
        if health_points > 1:
            msg += "s"

        if self.health <= health_points:
            msg += ". You are dead"
            self.death()

        self.decrement_health(health_points)
        utils.game_print(msg)

    def on_smell(self):
        """
        Called when player smells themselves
        """
        if self.smell_description:
            utils.game_print(smell_description)
            return

        utils.game_print("You smell %s." % get_properties(self.material).smell)

    def on_taste(self):
        """
        Called when player tastes themselves
        """
        if self.taste_description:
            utils.game_print(taste_description)
            return

        utils.game_print("You taste %s." % get_properties(self.material).taste)

    def has_item(self, item):
        """
        Check if an item is in the player's inventory

        :param text_game_maker.game_objects.generic.Item item: item to check
        :return: True if item is in the player's inventory, False otherwise
        :rtype: bool
        """
        if self.equipped and (self.equipped is item):
            return True

        if item.home is self.pockets.items:
            return True

        if self.inventory and (item.home is self.inventory.items):
            return True

        return False

    def can_see(self):
        """
        Check if the player can see their surroundings in the current game
        location. Takes the following things into account;

        * Is the current tile dark?
        * Does the player have a light source equipped?
        * Does the light source need fuel, and if so, does it have some?

        :return: True if the player can see their surroundings, False otherwise
        :rtype: bool
        """
        if not self.current.dark:
            return True

        if not self.equipped:
            return False

        if not self.equipped.is_light_source:
            return False

        if self.equipped.get_fuel() <= 0.0:
            return False

        return True

    def inventory_space(self):
        """
        Check number of remaining items the players inventory can fit. When
        players inventory is full, this method will return 0.

        :return: number of remaining items player's inventory has space for
        ;rtype: int
        """
        used = len(self.pockets.items)
        capacity = self.pockets.capacity

        if self.inventory:
            used += len(self.inventory.items)
            capacity += self.inventory.capacity

        return capacity - used

    def previous_tile(self):
        """
        Get the tile that the player was on before the current tile

        :return: previous tile object
        :rtype: text_game_maker.tile.tile.Tile
        """
        if not self.move_history:
            return None

        return tile.get_tile_by_id(self.move_history[-1])

    def get_special_attrs(self):
        ret = {}
        inventory_data = None

        tasks = {}
        for i in self.scheduled_tasks:
            callback, turns, scheduled_turns = self.scheduled_tasks[i]

            tasks[i] = [
                utils.serialize_callback(callback), turns, scheduled_turns
            ]

        ret[OBJECT_VERSION_KEY] = __object_model_version__
        ret[TILES_KEY] = tile.crawler(self.start)
        ret[CRAFTABLES_KEY] = crafting.serialize()
        ret[START_TILE_KEY] = self.start.tile_id
        ret['current'] = self.current.tile_id
        ret['scheduled_tasks'] = tasks
        return ret

    def set_special_attrs(self, attrs, version):
        for taskid in attrs['scheduled_tasks']:
            cb_name, turns, scheduled_turns = attrs['scheduled_tasks'][taskid]
            callback = utils.deserialize_callback(cb_name)
            self.scheduled_tasks[taskid] = (callback, turns, scheduled_turns)

        self.start = tile.builder(attrs[TILES_KEY], attrs[START_TILE_KEY], version)
        self.current = tile.get_tile_by_id(attrs['current'])
        crafting.deserialize(attrs[CRAFTABLES_KEY], version)

        del attrs['scheduled_tasks']
        del attrs[START_TILE_KEY]
        del attrs['current']
        del attrs[TILES_KEY]
        del attrs[CRAFTABLES_KEY]
        return attrs

    def increment_energy(self, val=1):
        """
        Increment player energy

        :param int val: number to increment player energy by
        """
        inc = self._inc_clamp(self.energy, val, self.max_energy)
        if inc > 0:
            self.energy += inc

        return inc

    def decrement_energy(self, val=1):
        """
        Decrement player energy

        :param int val: number to decrement player energy by
        """
        dec = self._dec_clamp(self.energy, val, 0)
        if dec > 0:
            self.energy -= dec

        return dec

    def save_to_string(self, compression=True):
        """
        Serialize entire map and player state and return as a string

        :param bool compression: whether to compress string
        :return: serialized game state
        :rtype: str
        """
        data = json.dumps(self.get_attrs())
        if compression:
            return zlib.compress(_encode_for_zlib(data))

        return _encode_for_zlib(data)

    def save_to_file(self, filename, compression=True):
        """
        Serialize entire map and player state and write to a file

        :param str filename: name of file to write serialized state to
        :param bool compression: whether to compress string
        """
        with open(filename, 'wb') as fh:
            fh.write(self.save_to_string(compression=True))

    def death(self):
        """
        Called whenever the player dies
        """
        utils.save_sound(audio.DEATH_SOUND)
        self.reset_game = True

    def set_alternate_names(self, tile):
        for adj in tile.iterate_directions():
            direction = adj.direction_to(tile)
            if not direction:
                continue

            alt_name = adj.name_from_dir[direction]
            if alt_name:
                adj.original_name = adj.name
                adj.name = alt_name

    def _move(self, dest, word, name):
        utils.save_sound(audio.SUCCESS_SOUND)

        if not self.can_see():
            previous = self.previous_tile()
            if (not previous) or not (dest is previous):
                utils._wrap_print(messages.dark_stumble_message())
                return

        if dest is None:
            utils.game_print("Can't go %s from here." % name)
            utils.save_sound(audio.FAILURE_SOUND)
            return self.current

        if self.current.on_exit and (not
                self.current.on_exit(self, dest)):
            utils.save_sound(audio.FAILURE_SOUND)
            return

        if dest.on_enter and not dest.on_enter(self, self.current):
            utils.save_sound(audio.FAILURE_SOUND)
            return

        self.current.exit_event.generate(self, self.current, dest)
        old = self.current

        self.move_history.append(self.current.tile_id)
        self.current = dest
        self.current.name = self.current.original_name

        self.current.enter_event.generate(self, old, self.current)

        self.set_alternate_names(self.current)
        move_message = "You %s %s" % (word, name)
        utils.game_print(move_message + ".")
        utils.game_print(self.describe_current_tile())
        self.decrement_energy(MOVE_ENERGY_COST)
        return dest

    def read_player_name_and_set(self):
        """
        Helper function to read a name from the user and set as the player's name
        """
        default_name = utils.get_random_name()
        name = utils.read_line_raw("What is your name?", default=default_name)
        if name.strip() == "":
            name = default_name

        # captialize with name.title() and set as player name
        self.set_name(name.title())

    def set_name(self, name):
        """
        Set player name

        :param str name: new player name
        """

        self.name = name

    def get_equipped(self):
        """
        Get player equipped item

        :return: equipped item. None if no item is equipped.
        :rtype: text_game_maker.game_objects.items.Item
        """
        if not self.equipped:
            return None

        return self.equipped

    def schedule_task(self, callback, turns=1):
        """
        Add a function that will be invoked after the player has taken some
        number of moves (any valid input from the player counts as a move)

        The function should accept one parameter, and return a bool:

            def callback(player, turns):
                pass

            Callback parameters:

            * *player* (text_game_maker.player.player.Player): player instance
            * *turns* (int): number of turns this callback was scheduled for

            * *Return value* (bool): if True, this task will be scheduled
              again with the same number of turns

        :param str callback: function that returns the message to print
        :param int turns: number of turns to pass before callback will be invoked
        :return: task ID
        :rtype: int
        """

        ret = self.task_id
        args = (callback, turns, self.turns)
        self.scheduled_tasks[self.task_id] = args
        self.task_id = (self.task_id + 1) % self.max_task_id
        return ret

    def scheduler_tick(self):
        """
        'tick' function for task scheduler. Called on each move the player makes
        (unparseable or otherwise invalid input does not incur a 'tick'), and
        executes any tasks scheduled for that move.
        """
        self.turns += 1
        for task_id in list(self.scheduled_tasks):
            callback, turns, start = self.scheduled_tasks[task_id]
            if self.turns >= (start + turns):
                if callback(self, turns):
                    new = (callback, turns, self.turns)
                    self.scheduled_tasks[task_id] = new
                else:
                    del self.scheduled_tasks[task_id]

    def clear_tasks(self):
        """
        Clear all pending scheduled tasks (tasks which have been added but
        whose timers have not expired)
        """

        self.scheduled_tasks.clear()

    def clear_task(self, task_id):
        """
        Clear a specific scheduled task by task ID

        :param int task_id: task ID of the task to remove
        :return: False if the provided task ID was not found in the pending\
            scheduled tasks list, True otherwise
        :rtype: bool
        """

        if task_id not in self.scheduled_tasks:
            return False

        del self.scheduled_tasks[task_id]
        return True

    def _items_to_words(self, items):
        return [str(i) for i in items]

    def _loot_message(self, word, name, items, extra=""):
        utils.game_print("You %s %s.\nYou find %s. %s"
            % (word, name, utils.list_to_english(items), extra))

    def _loot(self, word, person):
        if not person.items:
            utils.game_print('\nYou %s %s, and find nothing.'
                % (word, person.name))
            return

        print_items = []
        if not self.inventory:
            self._loot_message(word, person.name,
                self._items_to_words(person.items), "However, you have no "
                "bag to carry items, so you can't take anything.")
            return

        if len(self.inventory.items) >= self.inventory.capacity:
            self._loot_message(word, person.name,
                self._items_to_words(person.items), "However, your bag is "
                "full, so you can't take anything.")
            return

        remaining = (self.inventory.capacity - len(self.inventory.items))
        for _ in range(remaining):
            print_items.append(str(person.items[0]))
            if not self.inventory.add_item(person.items[0]):
                return

        self._loot_message(word, person.name, print_items)

    def describe_current_tile_contents(self, capitalize=True):
        """
        Return a string that describes the game state at the players current,
        location, including people, objects and scenery on the players current
        tile, and any adjacent tiles that connect to the players current tile.

        :param bool capitalize: if True, the first letter of each sentence will\
            be capitalized
        :return: string describing the players current loca
        """
        ret = ""
        scene = self.current.describe_scene()
        if scene:
            ret += scene

        items = self.current.describe_items()
        if items:
            ret += items

        people = self.current.describe_people()
        if people:
            ret += people

        if capitalize and len(ret) > 0:
            ret = utils.capitalize(ret)

        return ret

    def darkness_message(self):
        """
        Return the message to print when the player enters an area which is dark
        and they do not have a working light source

        :return: message to print when player cannot see surrounding area
        :rtype: str
        """
        return "It is pitch black, and you cannot see anything."

    def describe_current_tile(self):
        """
        Returns the full descriptive text for the tile player is currently on,
        including everything contained in the tile and all adjacent tiles
        visible to the player

        :return: text description of current game state
        :rtype: str
        """

        items = []

        ret = "You are %s. " % self.current.description.rstrip('.')

        if (self.current.first_visit and self.current.first_visit_message and
                (self.can_see() or self.current.first_visit_message_in_dark)):
            ret += "%s. " % self.current.first_visit_message.rstrip('.')
            self.current.first_visit = False

        if self.can_see():
            summary = self.current.summary()
            if summary:
                ret += summary

            ret += self.describe_current_tile_contents(capitalize=False)
        else:
            ret += self.darkness_message() + " "

            last = self.previous_tile()
            if last is not None:
                direction = self.current.direction_to(last)
                ret += "To the %s is %s. " % (direction, last.name)

        return utils.capitalize(ret)

    def _move_north(self, word):
        self._move(self.current.north, word, "north")

    def _move_south(self, word):
        self._move(self.current.south, word, "south")

    def _move_east(self, word):
        self._move(self.current.east, word, "east")

    def _move_west(self, word):
        self._move(self.current.west, word, "west")
