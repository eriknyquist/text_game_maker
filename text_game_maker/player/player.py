import time
import zlib
import json
import text_game_maker

from text_game_maker.audio import audio
from text_game_maker.game_objects.items import SmallBag
from text_game_maker.game_objects.base import GameEntity
from text_game_maker.utils import utils
from text_game_maker.tile import tile

TILES_KEY = '_tile_list'
MOVE_ENERGY_COST = 0.25

_serializable_callbacks = {}

def add_serializable_callback(callback):
    """
    Add a callback object to registry of callbacks that can be securely
    referenced in a save file. An ID will be assigned to represent this
    callback in save files. When loading a save file, whatever object you
    pass here will be used when the same ID is seen.

    :param callback: callback object to register
    """
    _serializable_callbacks[utils.get_full_import_name(callback)] = callback

def serializable_callback(callback):
    """
    Decorator version od add_serializable_callback. Example:

    ::

        from text_game_maker.player.player import serializable_callback

        @serializable_callback
        def my_callback_function():
            pass
    """
    add_serializable_callback(callback)
    return callback

def load_from_file(filename):
    with open(filename, 'rb') as fh:
        strdata = zlib.decompress(fh.read())
        data = json.loads(strdata)

    player = Player()
    player.set_attrs(data)
    return player

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

        self.coins = 0
        self.equipped = None
        self.inventory = None
        self.name = "john"

    def get_special_attrs(self):
        ret = {}
        inventory_data = None

        tasks = {}
        for i in self.scheduled_tasks:
            callback, turns, scheduled_turns = self.scheduled_tasks[i]
            cb_name = utils.get_full_import_name(callback)

            if cb_name not in _serializable_callbacks:
                raise RuntimeError("Not allowed to serialize callback '%s'. See"
                    " text_game_maker.player.player.add_serializable_callback"
                    % cb_name)

            tasks[i] = [
                cb_name, turns, scheduled_turns
            ]

        ret[TILES_KEY] = tile.crawler(self.start)
        ret['start'] = self.start.tile_id
        ret['current'] = self.current.tile_id
        ret['scheduled_tasks'] = tasks
        ret['fsm'] = None
        return ret

    def set_special_attrs(self, attrs):
        for taskid in attrs['scheduled_tasks']:
            cb_name, turns, scheduled_turns = attrs['scheduled_tasks'][taskid]
            if cb_name not in _serializable_callbacks:
                raise RuntimeError("Cannot deserialize callback '%s'" % cb_name)

            callback = _serializable_callbacks[cb_name]
            self.scheduled_tasks[taskid] = (callback, turns, scheduled_turns)

        self.start = tile.builder(attrs[TILES_KEY], attrs['start'])
        self.current = tile.get_tile_by_id(attrs['current'])

        del attrs['scheduled_tasks']
        del attrs['start']
        del attrs['current']
        del attrs[TILES_KEY]
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

    def serialize(self):
        return zlib.compress(json_dumps(self.get_attrs()))

    def save_state(self, filename):
        with open(filename, 'wb') as fh:
            data = json.dumps(self.get_attrs(), fh)
            fh.write(zlib.compress(data))

    def death(self):
        """
        Called whenever the player dies
        """
        audio.play_sound(audio.DEATH_SOUND)
        audio.wait()
        self.reset_game = True

    def _move(self, dest, word, name):
        utils.save_sound(audio.SUCCESS_SOUND)

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

        move_message = "You %s %s" % (word, name)

        self.current = dest
        utils.game_print(move_message + ".")
        utils.game_print(self.current_state())
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
        if not person.coins and not person.items:
            utils.game_print('\nYou %s %s, and find nothing.'
                % (word, person.name))
            return

        print_items = []
        if person.coins:
            print_items.append('%d coins' % person.coins)
            self.coins += person.coins
            person.coins = 0

        if person.items:
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

    def current_state(self):
        """
        Returns the full descriptive text for the current game state

        :return: text description of current game state
        :rtype: str
        """

        items = []

        ret = "You are %s. " % self.current.description.rstrip('.')
        #print get_nouns(self.current.description)

        summary = self.current.summary()
        if summary:
            ret += "%s. " % summary

        scene = self.current.describe_scene()
        if scene:
            ret += scene

        items = self.current.describe_items()
        if items:
            ret += items

        people = self.current.describe_people()
        if people:
            ret += people

        return utils.capitalize(ret)

    def _move_north(self, word):
        self._move(self.current.north, word, "north")

    def _move_south(self, word):
        self._move(self.current.south, word, "south")

    def _move_east(self, word):
        self._move(self.current.east, word, "east")

    def _move_west(self, word):
        self._move(self.current.west, word, "west")
