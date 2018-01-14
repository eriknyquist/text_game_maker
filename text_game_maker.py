import sys
import time
import copy
import threading
import Queue

# Might use this later...
#
#import nltk
#
#def get_nouns(text):
#    tokens = nltk.word_tokenize(text)
#    tagged = nltk.pos_tag(tokens)
#    nouns = ['%s (%s)' % (word, pos) for word,pos in tagged
#        if (pos == 'NNP' or pos == 'NNS' )]
#    downcased = [x.lower() for x in nouns]
#    return "\n".join(downcased)

info = {
    'slow_printing': False,
    'chardelay': 0.02,
    'sequence_count': None,
    'last_command': 'look'
}

COMMAND_DELIMITERS = [',', ';', '/', '\\']
SET_PRINT_WORDS = ['print']

KILL_WORDS = [
    'quit', 'stop', 'finish', 'end', 'exit'
]

GO_WORDS = [
    'go', 'move', 'walk', 'travel', 'crawl', 'shuffle', 'run', 'skip', 'jump',
    'dance', 'creep', 'sneak', 'tiptoe'
]

TAKE_WORDS = [
    'take', 'pick up', 'steal', 'acquire', 'grab', 'get', 'snatch', 'dock'
]

DROP_WORDS = [
    'drop', 'throw away', 'discard', 'chuck', 'ditch', 'delete', 'undock'
]

EQUIP_WORDS = [
    'equip', 'use', 'whip out', 'take out', 'brandish'
]

UNEQUIP_WORDS = [
    'unequip', 'put away', 'stop using'
]

SPEAK_WORDS = [
    'speak with', 'speak to', 'talk to', 'chat to', 'chat with', 'talk with',
    'chat', 'speak', 'talk'
]

SHOW_COMMAND_LIST_WORDS = [
    'show commands', 'show controls', 'show words', 'show wordlist',
    'commands', 'controls', 'wordlist', 'words'
]

LOOK_WORDS = [
    'look', 'peep', 'peek', 'show', 'viddy'
]

LOOT_WORDS = [
    'loot', 'search', 'rob', 'pickpocket'
]

INVENTORY_WORDS = [
    'i', 'inventory'
]

HELP_WORDS = [
    '?', 'help'
]

basic_controls = """
Movement
--------

Use phrases like 'east' or 'go south' to move around


Items
-----

Items are referred to by name. Use an item's name along with various verbs
to manipulate it:

 * Use 'i', 'inventory' or anything in between to show current inventory
   contents

 * Use phrases like 'get key' or 'pick up key' to add an item to your inventory
   by name (the item is named 'key' in this example and the following examples)

 * Use phrases like 'use key' or 'equip key' to equip an item by name from your
   inventory

 * Use phrases like 'put away key' or 'unequip key' to unequip an item

 * Equip inventory items to use them. For example, to use a key to unlock
   a door, walk to the door with the key equipped


People
------

People you encounter are referred to by name. Most interaction with people is
done through speaking.

* Use phrases like 'speak to alan', 'talk to alan', 'speak alan' to interact
  with a person by name (sample person is named 'Alan' in this example and the
  following examples)

* If you speak to someone with an inventory item equipped, they will see
  it and may offer to buy it.

* Use phrases like 'loot alan' or 'search alan' to try and steal a person's
  items and add them to your inventory. Attempts to loot a living person
  are usually unsuccessful.


Misc
----

* Use words like 'look' or 'show' to be reminded of your current surroundings

* Use 'print slow' to set printing mode to print one character at a time
  (looks cool for about 3 seconds)

* Use 'print fast' to set printing mode to normal printing

* Use 'print delay <seconds>', where '<seconds>' is a float value reprenting
  the number of seconds to delay between printing each charcter when slow
  printing is enabled.

* Use 'help' or '?' to show this information

* Use 'controls' or 'commands' or 'words' or 'show words'... etc. to show a
  comprehensive listing of game commands"""

input_queue = Queue.Queue()

def _read_input_task():
    while True:
        input_queue.put(sys.stdin.read(1))

enter_thread = threading.Thread(target=_read_input_task)
enter_thread.daemon = True
enter_thread.start()

def _unrecognised(player, val):
    print '\nUnrecognised command "%s"' % val

def list_to_english(strlist, conj='and'):
    """
    Convert a list of strings to description of the list in english.
    For example, ['4 coins', 'an apple', 'a sausage'] would be converted to
    '4 coins, an apple and a sausage'

    :param strlist: list of strings to convert to english
    :type strlist: str

    :return: english description of the passed list
    :rtype: str
    """

    if len(strlist) == 1:
        return strlist[0]

    msg = ""
    for i in range(len(strlist[:-1])):
        if i == (len(strlist) - 2):
            delim = ' ' + conj
        else:
            delim = ','

        msg += '%s%s ' % (strlist[i], delim)

    return msg + strlist[-1]

def _quit_hint():
    print ("\nUse %s to stop playing"
        % (list_to_english(['"%s"' % i for i in KILL_WORDS], conj='or')))

def read_line_raw(msg=''):
    """
    Read a line of input from stdin

    :param str msg: message to print before reading input
    :return: a line ending with either a newline or carriage return character
    :rtype: str
    """

    user_input = ""
    buf = ""

    sys.stdout.write(msg)
    sys.stdout.flush()

    c = ''

    while (c != '\r') and (c != '\n'):
        try:
            c = input_queue.get()
        except KeyboardInterrupt:
            _quit_hint()
            continue

        buf += c

    user_input = buf.strip()

    # If we are in the middle of command chain, decrement the count
    # of commands remaining in the input queue
    if info['sequence_count']:
        info['sequence_count'] -= 1
        print user_input

    return user_input

def read_line(msg):
    ret = ""
    while ret == "":
        ret = read_line_raw(msg)

    return ret

def ask_yes_no(prompt="[ continue (yes/no)? ]: "):
    """
    Ask player a yes/no question, and repeat the prompt until player
    gives a valid answer

    :param prompt: prompt containing question to ask
    :type prompt: str

    :return: player's response
    :rtype: str
    """

    ret = "z"
    while (not 'yes'.startswith(ret)) and (not 'no'.startswith(ret)):
        ret = read_line(prompt)

    return 'yes'.startswith(ret)

def _remove_leading_whitespace(string):
    trimmed = [s.strip() for s in string.splitlines()]
    return '\n'.join(trimmed)

def game_print(msg):
    """
    Print one character at a time if player has set 'print slow', otherwise
    print normally

    :param msg: message to print
    :type msg: str
    """

    if not info['slow_printing']:
        print msg
        return

    for i in range(len(msg)):
        if not info['sequence_count']:
            try:
                c = input_queue.get_nowait()
            except Queue.Empty:
                pass
            else:
                if c == '\n':
                    print msg[i:]
                    return

        sys.stdout.write(msg[i])
        sys.stdout.flush()
        time.sleep(info['chardelay'])

    print ''

class Tile(object):
    """
    Represents a single 'tile' or 'room' in the game
    """

    def __init__(self, name=None, description=None, on_enter=None,
            on_exit=None):
        """
        Initialise a Tile instance

        :param str name: short description, e.g. "a dark cellar"
        :param str description: long description, printed when player enters\
            the room e.g. "a dark, scary cellar with blah blah blah... "
        :param on_enter: callback to be invoked when player attempts to enter\
            this tile (see documentation for\
            text_game_maker.MapBuilder.set_on_enter()
        :param on_exit: callback to be invoked when player attempts to exit\
            this tile (see documentation for\
            text_game_maker.MapBuilder.set_on_exit()
        """

        self.name = name
        if description:
            self.description = _remove_leading_whitespace(description)

        # If tile is locked, player will only see a locked door.
        self.locked = False

        # Adjacent tiles to the north, south, east and west of this tile
        self.north = None
        self.south = None
        self.east = None
        self.west = None

        # Items on this tile
        self.items = []

        # People on this tile
        self.people = []

        # Enter/exit callbacks
        self.on_enter = on_enter
        self.on_exit = on_exit

    def _get_name(self, tile, name):
        if tile:
            if tile.locked:
                msg = "a locked door"
            else:
                msg = tile.name

            return "to the %s is %s" % (name, msg)
        else:
            return None

    def summary(self):
        """
        Return a description of all available directions from this tile
        """

        ret = []

        north = self._get_name(self.north, 'north')
        south = self._get_name(self.south, 'south')
        east = self._get_name(self.east, 'east')
        west = self._get_name(self.west, 'west')

        if north: ret.append(north)
        if south: ret.append(south)
        if east: ret.append(east)
        if west: ret.append(west)

        return '\n'.join(ret)

    def is_locked(self):
        """
        Returns true/false indicating whether this tile is locked.
        :return: True if tile is locked, False if unlocked.
        :rtype: bool
        """

        return self.locked

    def set_locked(self):
        """
        Lock this tile-- player will only see a locked door
        """

        self.locked = True

    def set_unlocked(self):
        """
        Unlock this tile-- player can enter normally
        """

        self.locked = False

class Person(object):
    """
    Represents a person that the player can interact with
    """

    def __init__(self, name, description, on_speak=None, alive=True, coins=50,
            items={}):
        """
        Initialises a Person instance

        :param str name: name of Person, e.g. "John"
        :param str description: description of Person, e.g. "squatting in the\
            corner"
        :param on_speak: on_speak callback (see \
            text_game_maker.Person.set_on_speak description for more details)
        :param bool alive: Initial living state of person .If True, person will\
            be alive. If false, person will be dead
        :param int coins: Number of coins this person has
        :param dict items: Items held by this person, where each dict item is\
            of the form {Item.name: Item}
        """

        self.name = name
        self.description = description
        self.on_speak = on_speak
        self.alive = alive
        self.coins = coins
        self.items = items

    def __str__(self):
        return '%s is %s' % (self.name, self.description)

    def die(self, msg=None):
        """
        Kill this person, and print a message to inform the player
        of this person's death.

        :param msg: message to print informing player of person's death
        :type msg: str
        """

        self.alive = False
        self.name = "%s's corpse" % self.name
        self.description = "on the floor"

        if msg is None or msg == "":
            msg = '\n%s has died.' % self.name

        game_print(msg)

    def set_on_speak(self, callback):
        """
        Set a function to be invoked whenever the player talks to this person.
        The provided function should accept two arguments:

            def callback(person, player):
                pass

            * *person* (text_game_maker.Person): Person instance
            * *player* (text_game_maker.Player): Player instance
            * *Return value* (str): the text to be spoken in response to the
              player

        :param callback: Callback function to be invoked whenever player\
            speaks to this person
        """

        self.on_speak = callback

    def is_alive(self):
        """
        Test if this person is alive

        :return: True if this person is alive, otherwise false
        :rtype: bool
        """

        return self.alive

    def say(self, msg):
        """
        Speak to the player

        :param msg: message to speak
        :type msg: str
        """

        lines = msg.splitlines()
        lines[-1] += '"'

        sys.stdout.write('\n%s: "' % self.name)
        sys.stdout.flush()
        game_print(lines[0])

        for line in lines[1:]:
            sys.stdout.write(' ' * (len(self.name) + 2))
            sys.stdout.flush()
            game_print(line)

    def buy_equipped_item(self, player):
        """
        Ask player to buy equipped item. Expects player to have something
        equipped (so check before uing this method).

        If player's equipped item costs more coins than this person has, the
        person will automatically ask if the player will accept the lower
        amount, and can still buy the item if the player says yes.

        :param player: player object
        :type player: text_game_maker.Player

        :return: Returns the item if sale was successful, None otherwise
        :rtype: text_game_maker.Item
        """

        equipped = player.inventory_items['equipped']
        cost = equipped.value
        msg = "Ah, I see you have %s %s." % (equipped.prefix, equipped.name)

        if self.coins >= cost:
            msg += " I would like to buy it for %d coins." % cost
        else:
            msg += (" I would like to buy it from you,\n"
                    "but I only have %d coins. Will you accept that price\n"
                    "instead?" % self.coins)
            cost = self.coins

        self.say(msg)
        if ask_yes_no("\n[sell %s for %d coins? (yes/no)] : "
                % (equipped.name, cost)):
            # Transfer money
            player.coins += cost
            self.coins -= cost

            # Transfer item
            equipped_copy = copy.deepcopy(equipped)
            self.items[equipped_copy.name] = equipped_copy

            player.delete_equipped()
            game_print("\nSale completed.")
            return equipped_copy

        game_print("\nSale cancelled")
        return None

class Item(object):
    """
    Base class for collectable item
    """

    def __init__(self, prefix, name, description=None, value=None,
            on_take=None):
        """
        Initialises an Item instance

        :param str prefix: Generally either "a" or "an"
        :param str name: Item name, e.g. "apple"
        :param str description: Item description, e.g. "on the floor"
        :param int value: Item value in coins
        :param on_take: callback function to invoke when player attempts to\
            add this item to their inventory
        """

        self.value = value
        self.name = name
        self.prefix = prefix
        self.description = description
        self.on_take = on_take

    def set_prefix(self, prefix):
        """
        Set item prefix word (usually 'an' or 'a')
        """

        self.prefix = prefix

    def set_name(self, name):
        """
        Set the name of this item

        :param str name: object name
        """

        self.name = name

    def set_description(self, desc):
        """
        Set the description of the item's location/sitation in the world,
        e.g. "on the floor"

        :param str desc: item description
        """

        self.description = desc

    def set_value(self, value):
        """
        Set the value of this item in coins

        :param int value: item value in coins
        """

        self.value = value

    def set_on_take(self, callback):
        """
        Set callback function to be invoked when player attempts to add this
        item to their inventory. Callback should accept one argument:

            def callback(player)
                pass

        * *player* (text_game_maker.Player): player instance

        :param callback: callback function
        """

        self.on_take = on_take

    def __str__(self):
        return '%s %s is %s' % (self.prefix, self.name, self.description)

class Player(object):
    """
    Base class to hold player related methods & data
    """

    def __init__(self, start_tile=None, input_prompt=None):
        """
        :param text_game_maker.Tile start_tile: Game starting tile
        :param str input_prompt: Custom string to prompt player for game input
        """

        self.start = start_tile
        self.current = start_tile
        self.prompt = input_prompt

        self.max_task_id = 0xffff
        self.task_id = 0
        self.scheduled_tasks = {}

        self.coins = 0
        self.inventory_items = {'equipped': None}
        self.name = ""
        self.title = ""

    def _move(self, dest, word, name):
        if dest is None:
            game_print("\nCan't go %s from here." % name)
            return self.current

        if self.current.on_exit and (not
                self.current.on_exit(self, self.current, dest)):
            return

        if dest.on_enter and not dest.on_enter(self, self.current, dest):
            return

        if dest.locked:
            game_print("\nCan't go through a locked door without a key")
            return self.current

        self.current = dest

        game_print("\nYou %s %s." % (word, name))
        game_print("%s" % self.current_state())

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

        * *player* (text_game_maker.Player): player instance

        :param str callback: function that returns the message to print
        :param float seconds: time delay in seconds before the message can be\
            printed
        :return: task ID
        :rtype: int
        """

        ret = self.task_id
        self.scheduled_tasks[self.task_id] = (callback, time.time() + seconds)
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
            game_print('\nYou %s %s, and find nothing.' % (word, person.name))
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

            game_print("\nYou %s %s.\nYou find %s." % (word, person.name,
                list_to_english(print_items)))

    def current_state(self):
        """
        Returns the full descriptive text for the current game state
        """

        items = []

        ret = "\nYou are %s" % self.current.description
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
            game_print('\n%s added to inventory' % curr.name)
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
            game_print("\nDropped %s" % i)
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
                game_print('\n%s says nothing. %s is dead.' % (p.name, p.name))

            return

    print "\n%s: no such person" % name

def _do_quit(player, word, name):
    ret = "z"
    while (not 'yes'.startswith(ret)) and (not 'no'.startswith(ret)):
        ret = read_line("[really stop playing? (yes/no)]: ")

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
            game_print("\nEquipped %s" % i)
            player.inventory_items['equipped'] = player.inventory_items[i]
            return

    print "\n%s: no such item in inventory" % item_name

def _do_unequip(player, word, fields):
    equipped = player.inventory_items['equipped']
    if not equipped:
        game_print('\nNothing is currently equipped')
    else:
        player.inventory_items['equipped'] = None
        game_print('\n%s unequipped' % equipped.name)

def _do_loot(player, word, name):
    if not name or name.strip() == "":
        print "\nWho do you want to %s?" % word
        return

    for p in player.current.people:
        if p.name.lower().startswith(name):
            if p.is_alive():
                game_print("\nYou are dead.")
                game_print("\nYou were caught trying to %s %s."
                    % (word, p.name))
                game_print("\n%s didn't like this, and killed you.\n" % p.name)
                sys.exit()
            else:
                player._loot(word, p)

def _do_set_print_speed(player, word, setting):
    if not setting or setting == "":
        print ("\nWhat printing speed would you like? (e.g. "
            "'print fast' or 'print slow')")
        return

    if 'slow'.startswith(setting):
        info['slow_printing'] = True
        print "\nOK, will do."
    elif 'fast'.startswith(setting):
        info['slow_printing'] = False
        print "\nOK, got it."
    elif setting.startswith('delay'):
        fields = setting.split()
        if len(fields) < 2:
            print("\n'delay' requires an extra argument. Please provide a delay"
                " value in seconds (e.g. 0.01)")
        else:
            try:
                info['chardelay'] = float(fields[1])
            except ValueError:
                print("\nDon't recognise that value for 'print delay'.\n"
                    "Enter a delay value in seconds (e.g. 'print delay 0.1')")
            else:
                print ("\nOK, character print delay is set to %.2f seconds."
                    % info['chardelay'])
                if not info['slow_printing']:
                    print("(but it won't do anything unless slow printing is\n"
                        " enabled-- e.g. 'print slow' -- you fucking idiot)")
    else:
        print("\nUnrecognised print speed-- please say 'print fast' "
            "or 'print slow'")

def _do_look(player, word, setting):
    print player.current_state()

def _do_inventory_listing(player, word, setting):
    print "\n--------------- INVENTORY ---------------"
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
    print get_full_controls()

def _do_help(player, word, setting):
    print basic_controls

def _check_word_set(word, word_set):
    for w in word_set:
        if word.startswith(w):
            return w

    return None

def _is_shorthand_direction(word):
    for w in ['north', 'south', 'east', 'west']:
        if w.startswith(word):
            return w

    return None

command_table = [
    (SET_PRINT_WORDS, _do_set_print_speed),
    (GO_WORDS, _do_move),
    (EQUIP_WORDS, _do_equip),
    (TAKE_WORDS, _do_take),
    (DROP_WORDS, _do_drop),
    (SPEAK_WORDS, _do_speak),
    (UNEQUIP_WORDS, _do_unequip),
    (LOOT_WORDS, _do_loot),
    (KILL_WORDS, _do_quit),
    (SHOW_COMMAND_LIST_WORDS, _do_show_command_list),
    (LOOK_WORDS, _do_look),
    (INVENTORY_WORDS, _do_inventory_listing),
    (HELP_WORDS, _do_help)
]

listable_commands = [
    (GO_WORDS, "<direction>",
        "Words/phrases to move the player in specific direction (north, south, "
        "east, west)"),
    (EQUIP_WORDS, "<item>",
        "Words/phrases to equip an item from player\'s inventory"),
    (TAKE_WORDS, "<item>",
        "Words/phrases to add an item to player's inventory"),
    (DROP_WORDS, "<item>",
        "Words/phrases to drop an item from player's inventory"),
    (SPEAK_WORDS, "<person>",
        "Words/phrases to speak with a person by name"),
    (UNEQUIP_WORDS, "<item>",
        "Words/phrases to unequip player's equipped item (if any)"),
    (LOOT_WORDS, "<person>",
        "Words/phrases to loot a person by name"),
    (KILL_WORDS, "",
        "Words/phrases to quit the game"),
    (LOOK_WORDS, "",
        "Words/phrases to examine your current surroundings"),
    (INVENTORY_WORDS, "",
        "Words/phrases to show player's inventory"),
    (SHOW_COMMAND_LIST_WORDS, "",
        "Words/phrases to show this list of command words"),
    (HELP_WORDS, "",
        "Words/phrases to show the basic 'help' screen")
]

def get_basic_controls():
    """
    Returns a basic overview of game command words
    """

    return basic_controls

def _do_listing(word_list, arg, desc):
    ret = '\n' + desc + '\n\n'
    for w in word_list:
        ret +='    "%s %s' % (w, arg)
        ret = ret.rstrip() + '"\n'

    return ret

def get_full_controls():
    """
    Returns a comprehensive listing of of all game command words
    """

    return '\n'.join([_do_listing(*a) for a in listable_commands])

def _parse_command(player, action):
    if action == '':
        action = info['last_command']
        print '\n' + action

    fields = [f.strip() for f in action.split()]

    for word_set, task in command_table:
        ret = _check_word_set(action, word_set)
        if ret:
            task(player, ret, action[len(ret):].strip())
            info['last_command'] = action
            return

    if _is_shorthand_direction(action):
        _do_move(player, 'go', action)
    else:
        _unrecognised(player, fields[0])
        return

    info['last_command'] = action

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

        self.player_title = "sir"
        self.player_name = "john"

        self.start = Tile(name, description)
        self.current = self.start
        self.prompt = "[?]: "

    def set_on_enter(self, callback):
        """
        Set callback function to be invoked when player attempts to enter the
        current tile. The callback function should accept 3 arguments:

            callback(player, source, dest):

        * *player* (text_game_maker.Player object): player instance
        * *source* (text_game_maker.Tile object): source tile (tile that player
          is trying to exit
        * *destination* (text_game_maker.Tile object): destination tile (tile
          that player is trying to enter
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

        * *player* (text_game_maker.Player object): player instance
        * *source* (text_game_maker.Tile object): source tile (tile that player
          is trying to exit
        * *destination* (text_game_maker.Tile object): destination tile (tile
          that player is trying to enter
        * *Return value* (bool): If False, player's attempt to exit the
          current tile will be blocked (silently-- up to you to print something
          if you need it here). If True, player will be allowed to continue
          normally.


        :param callback: the callback function
        """

        self.current.on_exit = callback

    def set_player_name(self, name):
        """
        Set player name

        :param str name: new player name
        """

        self.player_name = name

    def set_player_title(self, title):
        """
        Set player title

        :param str title: new player title
        """

        self.player_title = title

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

        self.current.description = _remove_leading_whitespace(desc)

    def add_item(self, item):
        """
        Add item to current tile

        :param text_game_maker.Item item: the item to add
        """

        self.current.items.append(item)

    def add_person(self, person):
        """
        Add person to current tile

        :param text_game_maker.Person person: the person to add
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

    def _run_command_sequence(self, player, sequence):
        # Inject commands into the input queue
        lines = '\n'.join(sequence) + '\n'
        [input_queue.put(c) for c in lines]

        # Set the global command sequence count, so we know how many commands
        # from the chain are left in the input queue (even if a user callback
        # 'steals' some of the commands by calling read_input)
        info['sequence_count'] = len(sequence)

        while info['sequence_count'] > 0:
            action = read_line_raw("\n> ").strip().lower()
            _parse_command(player, action)

        info['sequence_count'] = None

    def _do_scheduled_tasks(self, player):
        for task_id in player.scheduled_tasks:
            callback, expiration = player.scheduled_tasks[task_id]
            if time.time() >= expiration:
                callback(player)
                del player.scheduled_tasks[task_id]

    def run_game(self):
        """
        Start running the game
        """

        player = Player(self.start, self.prompt)
        player.set_name(self.player_name)
        player.set_title(self.player_title)
        game_print(player.current_state())

        while True:
            action = read_line_raw("\n%s" % player.prompt)
            self._do_scheduled_tasks(player)

            delim = self._get_command_delimiter(action)
            if delim:
                sequence = action.lstrip(delim).split(delim)
                self._run_command_sequence(player, sequence)
                continue

            _parse_command(player, action.strip().lower())
