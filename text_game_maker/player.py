import time
import pickle
import text_game_maker

class Player(object):
    """
    Base class to hold player related methods & data
    """

    def __init__(self, start_tile=None, input_prompt=None):
        """
        :param text_game_maker.tile.Tile start_tile: Game starting tile
        :param str input_prompt: Custom string to prompt player for game input
        """

        self.loaded_file = None
        self.load_from_file = None
        self.start = start_tile
        self.current = start_tile
        self.prompt = input_prompt

        self.max_task_id = 0xffff
        self.task_id = 0
        self.scheduled_tasks = {}

        self.coins = 0
        self.inventory_items = {'equipped': None}
        self.name = "john"
        self.title = "sir"

    def save_state(self, filename):
        with open(filename, 'w') as fh:
            pickle.dump(self, fh)

    def _move(self, dest, word, name):
        if dest is None:
            text_game_maker.game_print("Can't go %s from here." % name)
            return self.current

        # Save locked state of destination tile before & after user callbacks,
        # So we can determine if dest. tile was unlocked by one of them
        locked_before = dest.is_locked()

        if self.current.on_exit and (not
                self.current.on_exit(self, self.current, dest)):
            return

        if dest.on_enter and not dest.on_enter(self, self.current, dest):
            return

        locked_after = dest.is_locked()
        move_message = "You %s %s" % (word, name)

        if locked_after:
            text_game_maker.game_print("Can't go through a locked door "
                "without a key")
            return self.current
        elif locked_before:
            move_message += ", unlocking the door"

        self.current = dest

        text_game_maker.game_print(move_message + ".")
        text_game_maker.game_print("%s" % self.current_state())

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

    def has_equipped(self, item_name):
        """
        Check if player has specific item equipped

        :param str item_name: name of item to check for
        :return: True if player has item equipped, false otherwise
        :rtype: bool
        """

        equipped = self.inventory_items['equipped']
        return (equipped and (equipped.name == item_name))

    def delete_equipped(self):
        """
        Delete currently equipped item from inventory, if there is one
        """

        equipped = self.inventory_items['equipped']
        if equipped:
            del self.inventory_items[equipped.name]
            self.inventory_items['equipped'] = None

    def schedule_task(self, callback, seconds=10):
        """
        Add a function that will be invoked whenever some player input is next
        received *and* a specific time has elapsed.

        The function should accept one argument:

            def callback(player):
                pass

        * *player* (text_game_maker.player.Player): player instance

        :param str callback: function that returns the message to print
        :param float seconds: time delay in seconds before the message can be\
            printed
        :return: task ID
        :rtype: int
        """

        ret = self.task_id
        self.scheduled_tasks[self.task_id] = (callback, seconds, time.time())
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
                for n, i in person.items.items():
                    print_items.append('%s %s' % (i.prefix, n))

                self.inventory_items.update(person.items)
                person.items.clear()

            text_game_maker.game_print("You %s %s.\nYou find %s."
                % (word, person.name,
                text_game_maker.list_to_english(print_items)))

    def current_state(self):
        """
        Returns the full descriptive text for the current game state
        """

        items = []

        ret = "You are %s" % self.current.description
        #print get_nouns(self.current.description)

        if self.current.people:
            ret += "\n\n%s" % ('\n'.join([str(i) for i in self.current.people]))

        if self.current.items:
            ret += "\n\n%s" % ('\n'.join([str(i) for i in self.current.items]))

        summary = self.current.summary()
        if summary:
            ret += "\n\n%s" % summary

        return ret

    def _move_north(self, word):
        self._move(self.current.north, word, "north")

    def _move_south(self, word):
        self._move(self.current.south, word, "south")

    def _move_east(self, word):
        self._move(self.current.east, word, "east")

    def _move_west(self, word):
        self._move(self.current.west, word, "west")
