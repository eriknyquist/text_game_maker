import text_game_maker as gamemaker

class Tile(object):
    """
    Represents a single 'tile' or 'room' in the game
    """

    def __init__(self, name=None, description=None):
        """
        Initialise a Tile instance

        :param str name: short description, e.g. "a dark cellar"
        :param str description: long description, printed when player enters\
            the room e.g. "a dark, scary cellar with blah blah blah... "
        """

        self.name = name
        if description:
            self.description = gamemaker._remove_leading_whitespace(description)

        # If tile is locked, player will only see a locked door.
        self.locked = False

        # Adjacent tiles to the north, south, east and west of this tile
        self.north = None
        self.south = None
        self.east = None
        self.west = None

        # Items on this tile
        self.items = {}

        # People on this tile
        self.people = {}

    # Enter/exit methods
    def on_enter(self, player, src, dest):
        return True

    def on_exit(self, player, src, dest):
        return True

    def _get_name(self, tile, name):
        if tile:
            if tile.locked:
                msg = "a locked door"
            else:
                msg = tile.name

            return "to the %s is %s" % (name, msg)
        else:
            return None

    def _describe_locations(self, items):
        if not items:
            return None

        ret = ""
        for loc in items:
            itemlist = [str(i) for i in items[loc]]

            if not itemlist:
                continue
            elif len(itemlist) > 1:
                english = gamemaker.list_to_english(itemlist)
                sentence = '%s are %s. ' % (english, loc)
            else:
                sentence = '%s is %s. ' % (itemlist[0], loc)

            ret += sentence

        return ret

    def describe_items(self):
        """
        Return sentences describing all item locations on this tile
        """

        return self._describe_locations(self.items)

    def describe_people(self):
        """
        Return sentences describing all people on this tile
        """

        return self._describe_locations(self.people)

    def add_item(self, item):
        if item.location not in self.items:
            self.items[item.location] = []

        item.move(self.items[item.location])

    def add_person(self, person):
        if person.location not in self.people:
            self.people[person.location] = []

        person.move(self.people[person.location])

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

        return '. '.join(ret)

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
