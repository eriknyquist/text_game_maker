import text_game_maker as gamemaker

def reverse_direction(direction):
    """
    Returns the opposite direction for a given direction, e.g. "north" becomes
    "south"

    :param str direction: direction to reverse
    :return: opposite direction. None if invalid direction is provided
    :rtype: str
    """
    if not direction:
        return None

    if direction == 'north':
        return 'south'
    elif direction == 'south':
        return 'north'
    elif direction == 'east':
        return 'west'
    elif direction == 'west':
        return 'east'

    return None

class Tile(object):
    """
    Represents a single 'tile' or 'room' in the game
    """

    default_locations = [
        "on the ground"
    ]

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

        # Adjacent tiles to the north, south, east and west of this tile
        self.north = None
        self.south = None
        self.east = None
        self.west = None

        # Items on this tile
        self.items = {loc: [] for loc in self.default_locations}

        # People on this tile
        self.people = {}

    def iterate_directions(self):
        """
        Iterator for all tiles connected to this tile

        :return: tile iterator
        :rtype: Iterator[:class:`text_game_maker.tile.tile.Tile`]
        """
        for tile in [self.north, self.south, self.east, self.west]:
            yield tile

    def is_door(self):
        return False

    def direction_to(self, tile):
        """
        Get the direction from this tile to the given tile

        :param Tile tile: tile to check the direction to
        :return: direction to the given tile
        :rtype: str
        """
        if not tile:
            return None

        if tile == self.north:
            return 'north'
        elif tile == self.south:
            return 'south'
        elif tile == self.east:
            return 'east'
        elif tile == self.west:
            return 'west'

        return None

    def direction_from(self, tile):
        """
        Get the direction from the given tile to this tile

        :param Tile tile: tile to check the direction from
        :return: direction from the given tile to this tile
        :rtype: str
        """
        return reverse_direction(self.direction_to(tile))

    # Enter/exit methods
    def on_enter(self, player, src):
        """
        Called when player tries to move into this tile. If on_enter returns
        True, the player will be moved to this tile. If False, the move will
        not be allowed.

        :param text_game_maker.player.player.Player player: player object
        :param text_game_maker.tile.tile.Tile src: tile that player is\
            currently on
        :return: True if player move should be allowed
        :rtype: bool
        """
        return True

    def on_exit(self, player, dest):
        """
        Called when player tries to move out of this tile. If on_exit returns
        True, the player will be moved to ``dest``. If False, the move will
        not be allowed.

        :param text_game_maker.player.player.Player player: player object
        :param text_game_maker.tile.tile.Tile dest: tile that player is\
            trying to move to
        :return: True if player move should be allowed
        :rtype: bool
        """
        return True

    def _get_name(self, tile, name):
        if tile:
            return "to the %s is %s" % (name, tile.name)
        else:
            return None

    def _item_descriptions(self, items, testfunc=None):
        if not items:
            return None

        ret = ""
        for loc in items:
            itemlist = [str(i) for i in items[loc] if testfunc and testfunc(i)]

            if not itemlist:
                continue
            elif len(itemlist) > 1:
                english = gamemaker.list_to_english(itemlist)
                sentence = '%s are %s. ' % (english, loc)
            else:
                sentence = '%s %s %s. ' % (itemlist[0], items[loc][0].verb, loc)

            ret += sentence

        return ret

    def describe_scene(self):
        """
        Return sentences describing all scenery items on this tile

        :return: description of scenery on this tile
        :rtype: str
        """

        return self._item_descriptions(self.items, lambda x: x.scenery)

    def describe_items(self):
        """
        Return sentences describing all non-scenery items on this tile

        :return: description of non-scenery on this tile
        :rtype: str
        """

        return self._item_descriptions(self.items, lambda x: not x.scenery)

    def describe_people(self):
        """
        Return sentences describing all people on this tile

        :return: description of all people (NPCs) on this tile
        :rtype: str
        """

        return self._item_descriptions(self.people)

    def add_item(self, item):
        """
        Add item to this tile

        :param GameEntity item: item to add
        """
        if item.location not in self.items:
            self.items[item.location] = []

        item.move(self.items[item.location])

    def add_person(self, person):
        """
        Add person to this tile

        :param text_game_maker.game_objects.person.Person: person to add
        """
        if person.location not in self.people:
            self.people[person.location] = []

        person.move(self.people[person.location])

    def summary(self):
        """
        Return a description of all available directions from this tile that the
        player can see

        :return: description of all available directions from this tile
        :rtype: str
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

class LockedDoor(Tile):
    def __init__(self, prefix, name, src_tile, replacement_tile):
        super(LockedDoor, self).__init__(name, "")
        self.name = '%s %s' % (prefix, name)
        self.short_name = name
        self.prefix = prefix
        self.locked = True
        self.source_tile = src_tile
        self.replacement_tile = replacement_tile

    def is_door(self):
        return True

    def on_unlock(self, player, item):
        if item.name == "lockpick":
            self.unlock()
        else:
            text_game_maker._wrap_print("%s cannot be unlocked with %s"
                % (self.short_name, item.prep))

    def unlock(self):
        if not self.locked:
            return

        direction = self.source_tile.direction_to(self)
        if not direction:
            return

        setattr(self.source_tile, direction, self.replacement_tile)
        gamemaker.game_print("You unlock the %s." % self.short_name)

    def on_enter(self, player, src):
        if self.locked:
            gamemaker._wrap_print("%s is locked." % self.short_name)
            return False
