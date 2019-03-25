import text_game_maker
from text_game_maker.utils import utils
from text_game_maker.materials.materials import get_properties
from text_game_maker.game_objects.base import GameEntity, serialize, deserialize
from text_game_maker.game_objects.items import Lockpick

_tiles = {}

def _register_tile(tile, tile_id=None):
    if tile_id is None:
        ret = Tile.tile_id
        Tile.tile_id += 1
    else:
        ret = tile_id

    _tiles[ret] = tile
    return ret

def get_tile_by_id(tile_id):
    """
    Get Tile instance by tile ID

    :param tile_id: ID of tile to fetch
    :return: tile instance
    :rtype: text_game_maker.tile.tile.Tile
    """
    if tile_id not in _tiles:
        return None

    return _tiles[tile_id]

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

def crawler(start):
    """
    Crawl over a map and serialize all tiles and contained items

    :param text_game_maker.tile.tile.Tile start: map starting tile
    :return: serializable dict representing all tiles and contained items
    :rtype: dict
    """
    ret = []
    tilestack = [start]
    seen = []

    if not isinstance(start, Tile):
        raise ValueError("%s should be called with a Tile object" % __func__)

    while tilestack:
        tile = tilestack.pop()
        if tile.tile_id in seen:
            continue

        ret.append(tile.get_attrs())
        seen.append(tile.tile_id)

        if isinstance(tile, LockedDoor) and tile.replacement_tile:
            tilestack.append(tile.replacement_tile)
        else:
            for t in tile.iterate_directions():
                tilestack.append(t)

    return ret

def builder(tiledata, start_tile_id):
    """
    Deserialize a list of serialized tiles, then re-link all the tiles to
    re-create the map described by the tile links

    :param list tiledata: list of serialized tiles
    :param start_tile_id: tile ID of tile that should be used as the start tile
    :return: starting tile of built map
    :rtype: text_game_maker.tile.tile.Tile
    """
    tiles = {}
    visited = []
    _tiles.clear()

    for d in tiledata:
        tile = deserialize(d)
        tiles[tile.tile_id] = tile

    if start_tile_id not in tiles:
        raise RuntimeError("No tile found with ID '%s'" % start_tile_id)

    tilestack = [tiles[start_tile_id]]
    while tilestack:
        t = tilestack.pop(0)
        if t.tile_id in visited:
            continue

        visited.append(t.tile_id)
        if isinstance(t, LockedDoor) and t.replacement_tile:
            if t.replacement_tile:
                t.replacement_tile = tiles[t.replacement_tile]
                tilestack.append(t.replacement_tile)
            if t.source_tile:
                t.source_tile = tiles[t.source_tile]
                tilestack.append(t.source_tile)
        else:
            for direction in ['north', 'south', 'east', 'west']:
                tile_id = getattr(t, direction)
                if not tile_id:
                    continue

                setattr(t, direction, tiles[tile_id])
                tilestack.append(tiles[tile_id])

    return tiles[start_tile_id]

class Tile(GameEntity):
    """
    Represents a single 'tile' or 'room' in the game
    """

    tile_id = 0

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

        super(Tile, self).__init__()

        self.description = ""
        self.name = name
        self.original_name = self.name

        self.name_from_dir = {
            "north": None,
            "south": None,
            "east": None,
            "west": None
        }

        if description:
            self.description = utils._remove_leading_whitespace(description)

        # Adjacent tiles to the north, south, east and west of this tile
        self.north = None
        self.south = None
        self.east = None
        self.west = None

        # First time visiting this tile?
        self.first_visit = True
        self.first_visit_message = None

        # Show first visit message even if player can't see anything?
        self.first_visit_message_in_dark = False

        # Does this tile require a light source?
        self.dark = False

        # Items on this tile
        self.items = {loc: [] for loc in self.default_locations}

        # People on this tile
        self.people = {}

        self.smell_description = None
        self.ground_smell_description = None
        self.ground_taste_description = None
        self.material = None

        self.tile_id = _register_tile(self)

    def on_smell(self):
        """
        Called when player types 'smell' or equivalent on this tile
        """
        if self.smell_description:
            utils.game_print(self.smell_description)
            return

        utils.game_print("It doesn't smell like anything in particular here.")

    def on_smell_ground(self):
        """
        Called when player types 'smell ground' or equivalent on this tile
        """
        if self.ground_smell_description:
            utils.game_print(self.ground_smell_description)
            return

        if self.material:
            utils.game_print("The ground smells %s."
                % get_properties(self.material).smell)
            return

        utils.game_print("The ground doesn't smell like anything in "
            "particular.")

    def on_taste_ground(self):
        """
        Called when player types 'taste ground' or equivalent on this tile
        """
        if self.ground_taste_description:
            utils.game_print(self.ground_taste_description)
            return

        if self.material:
            utils.game_print("The ground tastes %s."
                % get_properties(self.material).taste)
            return

        utils.game_print("The ground doesn't taste like anything in "
            "particular.")

    def set_tile_id(self, tile_id):
        """
        Sets the ID for this tile. This ID will be used to represent the tile in
        save files. Setting explicit tile names is recommended, as it ensures
        that the tile IDs will not change. If the ID of a tile changes, save
        files created with previous tile IDs will no longer work as expected.

        :param tile_id: tile ID
        """
        if tile_id in _tiles:
            raise RuntimeError("tile ID '%s' is already in use" % tile_id)

        if self.tile_id in _tiles:
            del _tiles[self.tile_id]

        _tiles[tile_id] = self
        self.tile_id = tile_id

    def get_special_attrs(self):
        ret = {}
        for tile in self.iterate_directions():
            d = self.direction_to(tile)
            ret[d] = tile.tile_id

        ret['items'] = {x:serialize(self.items[x]) for x in self.items}
        ret['people'] = {x:serialize(self.people[x]) for x in self.people}

        return ret

    def set_special_attrs(self, data):
        for loc in data['items']:
            for d in data['items'][loc]:
                item = deserialize(d)
                self.add_item(item)

        self.people = {x:deserialize(data['people'][x]) for x in data['people']}
        self.set_tile_id(data['tile_id'])

        del data['items']
        del data['people']
        del data['tile_id']
        return data

    def iterate_directions(self):
        """
        Iterator for all tiles connected to this tile

        :return: tile iterator
        :rtype: Iterator[:class:`text_game_maker.tile.tile.Tile`]
        """
        for tile in [self.north, self.south, self.east, self.west]:
            if tile is None:
                continue

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
                english = utils.list_to_english(itemlist)
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
        :return: the added item
        """
        if item.location not in self.items:
            self.items[item.location] = []

        return item.move(self.items[item.location])

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

        return '%s. ' % ('. '.join(ret))

class LockedDoor(Tile):
    def __init__(self, prefix="", name="", src_tile="", replacement_tile=""):
        super(LockedDoor, self).__init__(name, "")
        self.name = '%s %s' % (prefix, name)
        self.short_name = name
        self.prep = "the " + self.short_name
        self.prefix = prefix
        self.locked = True
        self.source_tile = src_tile
        self.replacement_tile = replacement_tile

    def get_special_attrs(self):
        ret = super(LockedDoor, self).get_special_attrs()
        for name in ['source_tile', 'replacement_tile']:
            tile = getattr(self, name)
            if isinstance(tile, GameEntity):
                ret[name] = tile.tile_id
            else:
                ret[name] = tile

        return ret

    def is_door(self):
        return True

    def on_open(self, player):
        pick = utils.find_inventory_item_class(player, Lockpick)
        if not pick:
            utils._wrap_print("You need a key or a lockpick to unlock %s"
                % self.prep)
            return

        # TODO: add logic for unlocking with keys

        self.unlock()
        if pick.uses <= 1:
            utils.game_print("%s has seen its last use, and breaks into pieces "
                "in your hand" % pick.prep)
            pick.delete()
        else:
            pick.uses -= 1

    def matches_name(self, name):
        if name.startswith("the"):
            name = name[4:]

        return name in self.short_name

    def unlock(self):
        if not self.locked:
            return

        direction = self.source_tile.direction_to(self)
        if not direction:
            return

        setattr(self.source_tile, direction, self.replacement_tile)
        msg = "You unlock the %s, revealing %s to the %s." % (self.short_name,
            self.replacement_tile.name, direction)

        utils.game_print(msg)
        self.locked = False

    def on_enter(self, player, src):
        if self.locked:
            utils._wrap_print("%s is locked." % self.short_name)
            return False

class LockedDoorWithKeypad(LockedDoor):
    def __init__(self, unlock_code, **kwargs):
        super(LockedDoorWithKeypad, self).__init__(**kwargs)
        self.unlock_code = unlock_code

    def on_open(self, player):
        while True:
            code = utils.read_line_raw("Enter keypad code to unlock the door",
                cancel_word="cancel")
            if (code == None) or (code.strip() == ""):
                utils.game_print("Cancelled.")
                return

            try:
                intcode = int(code)
            except:
                utils.game_print("Keypad code not acccepted.")
                continue

            if intcode != self.unlock_code:
                utils.game_print("Keypad code not acccepted.")
                continue

            break

        utils.game_print("Keypad code accepted!")
        self.unlock()

    def on_enter(self, player, src):
        self.on_open(player)
