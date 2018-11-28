import time
import pickle
import text_game_maker

from text_game_maker import audio

MOVE_ENERGY_COST = 0.25

class Player(object):
    """
    Base class to hold player related methods & data
    """

    def __init__(self, start_tile=None, input_prompt=None):
        """
        :param text_game_maker.tile.Tile start_tile: Game starting tile
        :param str input_prompt: Custom string to prompt player for game input
        """

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
        self.start = start_tile
        self.current = start_tile
        self.prompt = input_prompt

        self.max_task_id = 0xffff
        self.task_id = 0
        self.scheduled_tasks = {}

        self.coins = 0
        self.equipped = None
        self.inventory = []
        self.name = "john"
        self.title = "sir"

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
        inc = self._inc_clamp(self.energy, val, self.max_energy)
        if inc > 0:
            self.energy += inc

        return inc

    def decrement_energy(self, val=1):
        dec = self._dec_clamp(self.energy, val, 0)
        if dec > 0:
            self.energy -= dec

        return dec

    def increment_health(self, val=1):
        inc = self._inc_clamp(self.health, val, self.max_health)
        if inc > 0:
            self.health += inc

        return inc

    def decrement_health(self, val=1):
        dec = self._dec_clamp(self.health, val, 0)
        if dec > 0:
            self.health -= dec

        return dec

    def save_state(self, filename):
        with open(filename, 'w') as fh:
            pickle.dump(self, fh)

    def death(self):
        audio.play_sound(audio.DEATH_SOUND)
        audio.wait()

    def _move(self, dest, word, name):
        text_game_maker.save_sound(audio.SUCCESS_SOUND)

        if dest is None:
            text_game_maker.game_print("Can't go %s from here." % name)
            text_game_maker.save_sound(audio.FAILURE_SOUND)
            return self.current

        # Save locked state of destination tile before & after user callbacks,
        # So we can determine if dest. tile was unlocked by one of them
        locked_before = dest.is_locked()

        if self.current.on_exit and (not
                self.current.on_exit(self, self.current, dest)):
            text_game_maker.save_sound(audio.FAILURE_SOUND)
            return

        if dest.on_enter and not dest.on_enter(self, self.current, dest):
            text_game_maker.save_sound(audio.FAILURE_SOUND)
            return

        locked_after = dest.is_locked()
        move_message = "You %s %s" % (word, name)

        if locked_after:
            text_game_maker.game_print("Can't go through a locked door "
                "without a key")
            text_game_maker.save_sound(audio.FAILURE_SOUND)
            return self.current
        elif locked_before:
            move_message += ", unlocking the door"

        self.current = dest

        text_game_maker.game_print(move_message + ".")
        text_game_maker.game_print(self.current_state())
        self.decrement_energy(MOVE_ENERGY_COST)
        return dest

    def set_name(self, name):
        """
        Set player name

        :param str name: new player name
        """

        self.name = name

    def set_title(self, title):
        """
        Set player title

        :param str title: new player title
        """

        self.title = title

    def get_equipped(self):
        if not self.equipped:
            return None

        return self.equipped

    def schedule_task(self, callback, turns=1):
        """
        Add a function that will be invoked after the player has taken some
        number of turns

        The function should accept one parameter, and return a bool:

            def callback(player):
                pass

            Callback parameters:

            * *player* (text_game_maker.player.Player): player instance

            * *Return value* (bool): if True, this task will be scheduled
              again with the same number of turns

        :param str callback: function that returns the message to print
        :param float seconds: time delay in seconds before the message can be\
            printed
        :return: task ID
        :rtype: int
        """

        ret = self.task_id
        self.scheduled_tasks[self.task_id] = (callback, turns, self.turns)
        self.task_id = (self.task_id + 1) % self.max_task_id
        return ret

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

    def _loot(self, word, person):
        if not person.coins and not person.items:
            text_game_maker.game_print('\nYou %s %s, and find nothing.'
                % (word, person.name))
        else:
            print_items = []
            if person.coins:
                print_items.append('%d coins' % person.coins)
                self.coins += person.coins
                person.coins = 0

            if person.items:
                for item in person.items:
                    print_items.append('%s %s' % (item.prefix, item.name))
                    self.inventory.append(item)
                    item.home = self.inventory

                person.items = []

            text_game_maker.game_print("You %s %s.\nYou find %s."
                % (word, person.name,
                text_game_maker.list_to_english(print_items)))

    def current_state(self):
        """
        Returns the full descriptive text for the current game state
        """

        items = []

        ret = "You are %s. " % self.current.description.rstrip('.')
        #print get_nouns(self.current.description)

        summary = self.current.summary()
        if summary:
            ret += "%s. " % summary

        items = self.current.describe_items()
        if items:
            ret += items

        people = self.current.describe_people()
        if people:
            ret += people

        return ret

    def _move_north(self, word):
        self._move(self.current.north, word, "north")

    def _move_south(self, word):
        self._move(self.current.south, word, "south")

    def _move_east(self, word):
        self._move(self.current.east, word, "east")

    def _move_west(self, word):
        self._move(self.current.west, word, "west")
