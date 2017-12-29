import sys
import time
import threading
import Queue

KILL_WORDS = [
    'quit', 'stop', 'finish', 'end'
]

CONTROLS = """
           Actions
------------------------------------------------------

go <direction>     Move player. direction can be north,
                   south, east or west

take <item>        Add item to inventory

drop <item>        Drop item from inventory

equip <item>       Equip item from inventory

unequip            Unequip currently equipped item

speak <name>       Interact with a person by name

i                  Show inventory

?                  Print current description

------------------------------------------------------
"""

input_queue = Queue.Queue()

def wait_for_enter():
    while True:
        input_queue.put(sys.stdin.read(1))

enter_thread = threading.Thread(target=wait_for_enter)
enter_thread.daemon = True
enter_thread.start()

def unrecognised(map_obj, val):
    print '\nUnrecognised command "%s"' % val

def get_input(msg=''):
    sys.stdout.write(msg)
    sys.stdout.flush()

    msg = ""
    c = ''

    while (c != '\r') and (c != '\n'):
        c = input_queue.get()
        msg += c

    return msg

def remove_leading_whitespace(string):
    trimmed = [s.strip() for s in string.splitlines()]
    return '\n'.join(trimmed)

def slow_print(msg, chardelay=0.03):
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

    def next_response(self):
        if self.response >= len(self.responses):
            ret = "Fuck off"
        else:
            ret = self.responses[self.response]
            self.response += 1

        return '%s: "%s"' % (self.name, ret)

class Item(object):
    """
    Base class for collectable item
    """

    def __init__(self, prefix, name, description, value):
        self.value = value
        self.name = name
        self.prefix = prefix
        self.description = description

class Map(object):
    """
    Base class for a tile-based map
    """

    def __init__(self, start_tile=None):
        self.start = start_tile
        self.current = start_tile
        self.inventory_items = {'equipped': None}

    def _move(self, dest, name):
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

        slow_print("\nYou moved %s." % name)
        time.sleep(1)
        slow_print("%s" % self.current_state())

        return dest

    def current_state(self):
        items = []

        ret = "\nYou are in %s" % self.current.description
       
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

    def move_north(self):
        self._move(self.current.north, "north")

    def move_south(self):
        self._move(self.current.south, "south")

    def move_east(self):
        self._move(self.current.east, "east")

    def move_west(self):
        self._move(self.current.west, "west")

class MapBuilder(object):
    """
    Base class for building a tile-based map
    """

    def __init__(self, name=None, description=None):
        self.start = Tile(name, description)
        self.current = self.start

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

    def get_map(self):
        return Map(self.start)

def do_move(map_obj, direction):
    if not direction or direction.strip() == "":
        print "\nWhere do you want to go?"
        return

    if 'north'.startswith(direction):
        map_obj.move_north()
    elif 'south'.startswith(direction):
        map_obj.move_south()
    elif 'east'.startswith(direction):
        map_obj.move_east()
    elif 'west'.startswith(direction):
        map_obj.move_west()
    else:
        unrecognised(map_obj, direction)

def do_take(map_obj, item_name):
    if not item_name or item_name.strip() == "":
        print "\nWhat do you want to take?"
        return

    for i in range(len(map_obj.current.items)):
        if map_obj.current.items[i].name.startswith(item_name):
            full = map_obj.current.items[i].name
            map_obj.inventory_items[full] = map_obj.current.items[i]
            del map_obj.current.items[i]

            slow_print('\n%s added to inventory' % full)
            return

    print "\n%s: no such item" % item_name

def do_drop(map_obj, item_name):
    if not item_name or item_name.strip() == "":
        print "\nWhat do you want to drop?"
        return

    for i in map_obj.inventory_items:
        if i.startswith(item_name):
            map_obj.inventory_items[i].description = "on the floor"
            map_obj.current.items.append(map_obj.inventory_items[i])
            del map_obj.inventory_items[i]
            slow_print("\nDropped %s" % i)
            return

    print "\n%s: no such item in inventory" % item_name

def do_speak(map_obj, name):
    if not name or name.strip() == "":
        print "\nWho do you want to speak to?"
        return

    for p in map_obj.current.people:
        if p.name.lower().startswith(name):
            sys.stdout.write('\n%s: ' % p.name)
            sys.stdout.flush()
            slow_print('"%s"' % p.on_speak(map_obj))
            return

    print "\n%s: no such person" % name

def do_quit():
    ret = 'z'

    while (not 'yes'.startswith(ret)) and (not 'no'.startswith(ret)):
        ret = get_input("[really stop playing? (yes/no)]: ")

        if 'yes'.startswith(ret.lower()):
            sys.exit()
        elif 'no'.startswith(ret.lower()):
            return

def do_equip(map_obj, item_name):
    if not item_name or item_name.strip() == "":
        print "\nWhat do you want to equip?"
        return

    for i in map_obj.inventory_items:
        if i.startswith(item_name):
            slow_print("\nEquipped %s" % i)
            map_obj.inventory_items['equipped'] = map_obj.inventory_items[i]
            return

    print "\n%s: no such item in inventory" % item_name

def do_unequip(map_obj):
    equipped = map_obj.inventory_items['equipped']
    if not equipped:
        slow_print('\nNothing is currently equipped')
    else:
        map_obj.inventory_items['equipped'] = None
        slow_print('\n%s unequipped' % equipped.name)

def parse_command(map_obj, fields):
    if fields[0] == 'go':
        do_move(map_obj, ' '.join(fields[1:]))
    elif fields[0] == 'take':
        do_take(map_obj, ' '.join(fields[1:]))
    elif fields[0] == 'drop':
        do_drop(map_obj, ' '.join(fields[1:]))
    elif fields[0] == 'speak':  
        do_speak(map_obj, ' '.join(fields[1:]))
    elif fields[0] == 'equip':
        do_equip(map_obj, ' '.join(fields[1:]))
    elif fields[0] == 'unequip':
        do_unequip(map_obj)
    elif 'inventory'.startswith(fields[0]):
        print inventory_listing(map_obj)
    elif fields[0].startswith('?'):
        print map_obj.current_state()
    elif fields[0] in KILL_WORDS:
        do_quit()
    else:
        unrecognised(map_obj, fields[0])

def inventory_listing(map_obj):
    if not map_obj.inventory_items:
        return "\nInventory is empty"

    ret = ''
    for i in map_obj.inventory_items:
        if i == 'equipped':
            continue

        item = map_obj.inventory_items[i]
        msg = item.name

        if map_obj.inventory_items[i] is map_obj.inventory_items['equipped']:
            msg += " (equipped)"

        ret += "\n{0:35}{1:1}({2})".format(msg, "", item.value)

    return ret

def run_map(map_obj):
    print CONTROLS
    slow_print(map_obj.current_state())

    while True:
        action = get_input("\n[action?]: ").strip().lower()
        fields = [f.strip() for f in action.split()]

        if len(action) < 1:
            continue

        parse_command(map_obj, fields)
