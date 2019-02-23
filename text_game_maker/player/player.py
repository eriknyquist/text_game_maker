import time
import zlib
import json
import text_game_maker

from text_game_maker.audio import audio
from text_game_maker.game_objects.items import SmallBag, Lighter
from text_game_maker.game_objects.base import GameEntity
from text_game_maker.crafting import crafting
from text_game_maker.utils import utils
from text_game_maker.tile import tile
from text_game_maker.messages import messages

CRAFTABLES_KEY = '_craftables_data'
TILES_KEY = '_tile_list'
MOVE_ENERGY_COST = 0.25

def load_from_string(strdata, compression=True):
    """
    Load a serialized state from a string and create a new player instance

    :param str strdata: string data to load
    :param bool compression: whether data is compressed
    :return: new Player instance
    :rtype: text_game_maker.player.player.Player
    """
    if compression:
        strdata = zlib.decompress(strdata)

    data = json.loads(strdata)

    player = Player()
    player.set_attrs(data)
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

class Player(GameEntity):
    """
    Base class to hold player related methods & data
    """

    def __init__(self, start_tile=None, input_prompt=None):
        """
        :param text_game_maker.game_objects.tile.Tile start_tile: Starting tile
        :param str input_prompt: Custom string to prompt player for game input
        """

        super(Player, self).__init__()

        self.fsm = None
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
        lighter = Lighter()
        self.pockets.add_item(lighter)

    def has_item(self, item):
        if self.equipped and (self.equipped is item):
            return True

        if item.home is self.pockets.items:
            return True

        if self.inventory and (item.home is self.inventory.items):
            return True

        return False

    def can_see(self):
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
        used = len(self.pockets.items)
        capacity = self.pockets.capacity

        if self.inventory:
            used += len(self.inventory.items)
            capacity += self.inventory.capacity

        return capacity - used

    def previous_tile(self):
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

        ret[TILES_KEY] = tile.crawler(self.start)
        ret[CRAFTABLES_KEY] = crafting.serialize()
        ret['start'] = self.start.tile_id
        ret['current'] = self.current.tile_id
        ret['scheduled_tasks'] = tasks
        ret['fsm'] = None
        return ret

    def set_special_attrs(self, attrs):
        for taskid in attrs['scheduled_tasks']:
            cb_name, turns, scheduled_turns = attrs['scheduled_tasks'][taskid]
            callback = utils.deserialize_callback(cb_name)
            self.scheduled_tasks[taskid] = (callback, turns, scheduled_turns)

        self.start = tile.builder(attrs[TILES_KEY], attrs['start'])
        self.current = tile.get_tile_by_id(attrs['current'])

        crafting.deserialize(attrs[CRAFTABLES_KEY])

        del attrs['scheduled_tasks']
        del attrs['start']
        del attrs['current']
        del attrs[TILES_KEY]
        del attrs[CRAFTABLES_KEY]
        return attrs

    def _dec_clamp(self, curr, val, min_val):
        if curr == min_val:
            return 0

        if curr - val < min_val:
            return min_val + curr

        return val

    def _inc_clamp(self, curr, val, max_val):
        if  curr == max_val:
            return 0

        if curr + val > max_val:
            return max_val - curr

        return val

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

    def increment_health(self, val=1):
        """
        Increment player health

        :param int val: number to increment player health by
        """
        inc = self._inc_clamp(self.health, val, self.max_health)
        if inc > 0:
            self.health += inc

        return inc

    def decrement_health(self, val=1):
        """
        Decrement player health

        :param int val: number to decrement player health by
        """
        dec = self._dec_clamp(self.health, val, 0)
        if dec > 0:
            self.health -= dec

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
            return zlib.compress(data)

        return data

    def save_to_file(self, filename, compression=True):
        """
        Serialize entire map and player state and write to a file

        :param str filename: name of file to write serialized state to
        :param bool compression: whether to compress string
        """
        with open(filename, 'wb') as fh:
            fh.write(self.save_to_string(compression))

    def death(self):
        """
        Called whenever the player dies
        """
        utils.save_sound(audio.DEATH_SOUND)
        self.reset_game = True

    def _move(self, dest, word, name):
        utils.save_sound(audio.SUCCESS_SOUND)

        if not self.can_see():
            if not (dest is self.previous_tile()):
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

        self.move_history.append(self.current.tile_id)
        self.current = dest
        move_message = "You %s %s" % (word, name)
        utils.game_print(move_message + ".")
        utils.game_print(self.describe_current_tile())
        self.decrement_energy(MOVE_ENERGY_COST)
        return dest

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
        ret =""
        scene = self.current.describe_scene()
        if scene:
            ret += scene

        items = self.current.describe_items()
        if items:
            ret += items

        people = self.current.describe_people()
        if people:
            ret += people

        if capitalize:
            ret = utils.capitalize(ret)

        return ret

    def darkness_message(self):
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
