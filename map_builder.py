import sys
import time
import copy
import threading
import Queue

info = {
    'slow_printing': True,
    'last_command': '?'
}

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
    'drop', 'throw away', 'discard', 'chuck', 'ditch', 'delete'
]

EQUIP_WORDS = [
    'equip', 'use', 'whip out', 'take out', 'brandish'
]

UNEQUIP_WORDS = [
    'unequip', 'put away', 'stop using'
]

SPEAK_WORDS = [
    'speak with', 'speak to', 'talk to', 'talk with', 'speak', 'talk'
]

LOOK_WORDS = [
    "?", "look", "peep", "peek", "show", "viddy"
]

INVENTORY_WORDS = [
    'i', 'inventory'
]

input_queue = Queue.Queue()

def read_input_task():
    while True:
        input_queue.put(sys.stdin.read(1))

enter_thread = threading.Thread(target=read_input_task)
enter_thread.daemon = True
enter_thread.start()

def unrecognised(player, val):
    print '\nUnrecognised command "%s"' % val

def get_input(msg='', allow_empty=False):
    user_input = ""
    buf = ""

    while True:
        sys.stdout.write(msg)
        sys.stdout.flush()

        c = ''

        while (c != '\r') and (c != '\n'):
            c = input_queue.get()
            buf += c

        user_input = buf.strip()

        if allow_empty or (len(user_input) > 0):
            break

    return user_input

def ask_yes_no(prompt="[ continue (yes/no)? ]: "):
    ret = "z"
    while not 'yes'.startswith(ret) and not 'no'.startswith(ret):
        ret = get_input(prompt)

    if 'yes'.startswith(ret):
        return True

    return False

def remove_leading_whitespace(string):
    trimmed = [s.strip() for s in string.splitlines()]
    return '\n'.join(trimmed)

def slow_print(msg, chardelay=0.02):
    if not info['slow_printing']:
        print msg
        return

    for i in range(len(msg)):
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
        time.sleep(chardelay)

    print ''

class Tile(object):
    """
    Represents a single 'tile' or 'room' in the game
    """

    def __init__(self, name=None, description=None, on_enter=None,
            on_exit=None):
        self.locked = False
        self.name = name
        self.description = remove_leading_whitespace(description)

        self.north = None
        self.south = None
        self.east = None
        self.west = None

        self.items = []
        self.people = []

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

class Person(object):
    """
    Represents a person that we can interact with
    """

    def __init__(self, name, description, on_speak=None):
        self.name = name
        self.description = description
        self.on_speak = on_speak

    def say(self, msg):
        lines = msg.splitlines()
        lines[-1] += '"'

        sys.stdout.write('\n%s: "' % self.name)
        sys.stdout.flush()
        slow_print(lines[0])

        for line in lines[1:]:
            sys.stdout.write(' ' * (len(self.name) + 2))
            sys.stdout.flush()
            slow_print(line)

    def buy_equipped_item(self, player):
        equipped = player.inventory_items['equipped']
        self.say("Ah, I see you have %s %s. I would like to buy it for "
            "%d coins." % (equipped.prefix, equipped.name, equipped.value))

        if ask_yes_no("[sell %s for %d coins? (yes/no)] : "
                % (equipped.name, equipped.value)):
            player.coins += equipped.value
            equipped_copy = copy.deepcopy(equipped)
            player.delete_equipped()
            slow_print("\nSale completed.")
            return equipped_copy

        slow_print("\nSale cancelled")
        return None

class Item(object):
    """
    Base class for collectable item
    """

    def __init__(self, prefix, name, description, value):
        self.value = value
        self.name = name
        self.prefix = prefix
        self.description = description

class Player(object):
    """
    Base class to hold player related methods & data
    """

    def __init__(self, start_tile=None, input_prompt=None):
        self.start = start_tile
        self.current = start_tile
        self.prompt = input_prompt
        self.coins = 0
        self.inventory_items = {'equipped': None}
        self.name = ""
        self.title = ""

    def _move(self, dest, word, name):
        if dest is None:
            slow_print("\nCan't go %s from here." % name)
            return self.current

        if self.current.on_exit and (not
                self.current.on_exit(self, self.current, dest)):
            return

        if dest.on_enter and not dest.on_enter(self, self.current, dest):
            return

        if dest.locked:
            slow_print("\nCan't go through a locked door without a key")
            return self.current

        self.current = dest

        slow_print("\nYou %s %s." % (word, name))
        if info['slow_printing']:
            time.sleep(1)

        slow_print("%s" % self.current_state())

        return dest

    def delete_equipped(self):
        equipped = self.inventory_items['equipped']
        if equipped:
            del self.inventory_items[equipped.name]
            self.inventory_items['equipped'] = None

    def current_state(self):
        items = []

        ret = "\nYou are %s" % self.current.description

        if self.current.people:
            for p in self.current.people:
                items.append("%s is %s" % (p.name, p.description))

            ret += "\n\n%s" % ('\n'.join(items))

        items = []
        if self.current.items:
            for i in self.current.items:
                items.append("%s %s is %s" % (i.prefix, i.name, i.description))

            ret += "\n\n%s" % ('\n'.join(items))

        ret += "\n\n%s" % self.current.summary()
        return ret

    def set_name(self, name):
        self.name = name

    def set_title(self, title):
        self.title = title

    def move_north(self, word):
        self._move(self.current.north, word, "north")

    def move_south(self, word):
        self._move(self.current.south, word, "south")

    def move_east(self, word):
        self._move(self.current.east, word, "east")

    def move_west(self, word):
        self._move(self.current.west, word, "west")

class MapBuilder(object):
    """
    Base class for building a tile-based map
    """

    def __init__(self, name=None, description=None):
        self.start = Tile(name, description)
        self.current = self.start
        self.prompt = "[?]: "

    def add_enter_callback(self, callback):
        self.current.on_enter = callback

    def add_exit_callback(self, callback):
        self.current.on_exit = callback

    def add_description(self, desc):
        self.current.description = desc

    def add_item(self, item):
        self.current.items.append(item)

    def add_person(self, person):
        self.current.people.append(person)

    def set_locked(self):
        self.current.locked = True

    def set_input_prompt(self, prompt):
        self.prompt = prompt

    def _do_move(self, dest, name, description):
        if dest is None:
            dest = Tile(name, description)

        return self.current, dest

    def move_west(self, name=None, description=None):
        old, new = self._do_move(self.current.west, name, description)
        self.current.west = new
        self.current = self.current.west
        self.current.east = old

    def move_east(self, name=None, description=None):
        old, new = self._do_move(self.current.east, name, description)
        self.current.east = new
        self.current = self.current.east
        self.current.west = old

    def move_north(self, name=None, description=None):
        old, new = self._do_move(self.current.north, name, description)
        self.current.north = new
        self.current = self.current.north
        self.current.south = old

    def move_south(self, name=None, description=None):
        old, new = self._do_move(self.current.south, name, description)
        self.current.south = new
        self.current = self.current.south
        self.current.north = old

    def build_player(self):
        return Player(self.start, self.prompt)

def do_move(player, word, direction):
    if not direction or direction.strip() == "":
        print "\nWhere do you want to go?"
        return

    if 'north'.startswith(direction):
        player.move_north(word)
    elif 'south'.startswith(direction):
        player.move_south(word)
    elif 'east'.startswith(direction):
        player.move_east(word)
    elif 'west'.startswith(direction):
        player.move_west(word)
    else:
        unrecognised(player, direction)

def do_take(player, word, item_name):
    if not item_name or item_name.strip() == "":
        print "\nWhat do you want to take?"
        return

    for i in range(len(player.current.items)):
        if (player.current.items[i].name.startswith(item_name) or
                (item_name in player.current.items[i].name)):
            full = player.current.items[i].name
            player.inventory_items[full] = player.current.items[i]
            del player.current.items[i]

            slow_print('\n%s added to inventory' % full)
            return

    print "\n%s: no such item" % item_name

def do_drop(player, word, item_name):
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
            slow_print("\nDropped %s" % i)
            return

    print "\n%s: no such item in inventory" % item_name

def do_speak(player, word, name):
    if not name or name.strip() == "":
        print "\nWho do you want to speak to?"
        return

    for p in player.current.people:
        if p.name.lower().startswith(name):
            response = p.on_speak(p, player)

            if response:
                p.say(response)

            return

    print "\n%s: no such person" % name

def do_quit(player, word, name):
    ret = 'z'

    while (not 'yes'.startswith(ret)) and (not 'no'.startswith(ret)):
        ret = get_input("[really stop playing? (yes/no)]: ")

        print ret
        if 'yes'.startswith(ret.lower()):
            sys.exit()
        elif 'no'.startswith(ret.lower()):
            return

def do_equip(player, word, item_name):
    if not item_name or item_name.strip() == "":
        print "\nWhich inventory item do you want to equip?"
        return

    for i in player.inventory_items:
        if i.startswith(item_name) or item_name in i:
            slow_print("\nEquipped %s" % i)
            player.inventory_items['equipped'] = player.inventory_items[i]
            return

    print "\n%s: no such item in inventory" % item_name

def do_unequip(player, word, fields):
    equipped = player.inventory_items['equipped']
    if not equipped:
        slow_print('\nNothing is currently equipped')
    else:
        player.inventory_items['equipped'] = None
        slow_print('\n%s unequipped' % equipped.name)

def do_set_print_speed(player, word, setting):
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
    else:
        print("\nUnrecognised print speed-- please say 'print fast' "
            "or 'print slow'")

def do_look(player, word, setting):
    print player.current_state()

def do_inventory_listing(player, word, setting):
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

def check_word_set(word, word_set):
    for w in word_set:
        if word.startswith(w):
            return w

    return None

def is_shorthand_direction(word):
    for w in ['north', 'south', 'east', 'west']:
        if w.startswith(word):
            return w

    return None

command_table = [
    (SET_PRINT_WORDS, do_set_print_speed),
    (GO_WORDS, do_move),
    (EQUIP_WORDS, do_equip),
    (TAKE_WORDS, do_take),
    (DROP_WORDS, do_drop),
    (SPEAK_WORDS, do_speak),
    (UNEQUIP_WORDS, do_unequip),
    (KILL_WORDS, do_quit),
    (LOOK_WORDS, do_look),
    (INVENTORY_WORDS, do_inventory_listing)
]

def parse_command(player, action):
    if action == '':
        action = info['last_command']
        print '\n' + action

    fields = [f.strip() for f in action.split()]

    for word_set, task in command_table:
        ret = check_word_set(action, word_set)
        if ret:
            task(player, ret, action[len(ret):].strip())
            info['last_command'] = action
            return

    if is_shorthand_direction(action):
        do_move(player, 'go', action)
    else:
        unrecognised(player, fields[0])
        return

    info['last_command'] = action

def run_game(player):
    slow_print(player.current_state())

    while True:
        action = get_input("\n%s" % player.prompt, allow_empty=True)
        parse_command(player, action.strip().lower())
