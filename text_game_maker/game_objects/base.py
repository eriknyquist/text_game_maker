import sys

import text_game_maker
from text_game_maker.messages import messages
from text_game_maker.utils import utils
from text_game_maker.audio import audio

TYPE_KEY = '_type_key'

def is_deserializable_type(obj):
    return (type(obj) == dict) and (TYPE_KEY in obj)

def build_instance(type_key):
    """
    Build an instance of a registered serializable class, by the registered
    class name

    :param type_key: registered class name
    :return: instance of class associated with class name
    """
    classobj = utils.get_serializable_class(type_key)
    if not classobj:
        raise RuntimeError("Unable to de-serialize class %s" % type_key)

    try:
        ins = classobj()
    except Exception as e:
        raise RuntimeError("Can't create instance of %s: %s"
            % (classobj.__name__, e))

    return ins

def deserialize(data):
    """
    Recursively deserialize item and all contained items

    :param dict data: data to deserialize
    :return: deserialized object
    """
    if is_deserializable_type(data):
        item = build_instance(data[TYPE_KEY])
        item.set_attrs(data)
    elif type(data) == list:
        item = []

        if len(data) > 0:
            for sub in data:
                item.append(deserialize(sub))
    else:
        item = data

    return item

def serialize(attr):
    """
    Recursively serialize item and return a serializable dict representing the
    item and all contained items

    :param attr: object to serialize
    :return: serialized object
    :rtype: dict
    """
    if type(attr) == list:
        ret = []

        for item in attr:
            if isinstance(item, GameEntity):
                item = item.get_attrs()

            ret.append(item)

    elif isinstance(attr, GameEntity):
        ret = attr.get_attrs()
    else:
        ret = attr

    return ret

class GameEntity(object):
    """
    Base class for anything that the player can interact with in the
    game, like usable items, food, people, etc.

    :ivar bool inanimate: defines whether this item is an inanimate object
    :ivar bool combustible: defines whether this item can be destroyed by fire
    :ivar bool scenery: defines whether this item is scenery; an immovable prop\
        in the scene that should be mentioned before smaller interactive items\
        when describing a room, e.g. furniture, architectural features of the\
        room
    :ivar bool edible: defines whether this item is edible
    :ivar bool alive: defines whether this item is currently alive
    :ivar int energy: defines how much energy player gains by consuming this\
        item
    :ivar int damage: defines how much health player loses if damaged by this\
        item

    :ivar int value: defines how much money player will make by selling this\
        item
    :ivar str name: name that this item will be referred to as in the game\
        (e.g. "metal key")
    :ivar str prefix: preceding word required when mentioning item, e.g. "a"\
        for "a metal key", and "an" for "an apple"
    :ivar list home: list that this Item instance lives inside; required for\
        the deleting/moving items within the game world
    :ivar bool is_container: defines whether this item can contain other items
    :ivar bool is_flame_source: defines whether this item can be used as a \
        flame source
    :ivar bool is_light_source: defines whether this item can be used as a \
        light source
    :ivar int capacity: number of items this item can contain (if container)
    :ivar list items: items contained inside this item (if container)
    :ivar int size: size of this item; containers cannot contain items with a\
        larger size than themselves
    :ivar str verb: singluar verb e.g. "the key is on the floor", or plural\
        e.g. "the coins are on the floor"
    """

    __metaclass__ = utils.SubclassTrackerMetaClass

    def __init__(self):
        self.inanimate = True
        self.combustible = True
        self.scenery = False
        self.edible = False
        self.alive = False
        self.energy = 0
        self.damage = 0
        self.value = 0
        self.prefix = "a"
        self.name = None
        self.prep = None
        self.home = None
        self.is_container = False
        self.is_light_source = False
        self.is_flame_source = False
        self.is_flame_source = False
        self.capacity = 0
        self.items = []
        self.size = 1
        self.verb = "is"

    def get_special_attrs(self):
        """
        Serialize any attributes that you want to handle specially here. Any
        attributes present in the dict returned by this function will not be
        serialized by the main get_attrs method. Intended for subclasses to
        override

        :return: serializable dict of special attributes
        :rtype: dict
        """
        return {}

    def set_special_attrs(self, attrs):
        """
        Deserialize any attributes that you want to handle specially here.
        Make sure to delete any specially handled attributes from the return
        dict so that they are not deserialized by the main set_attrs method

        :param dict attrs: all serialized attributes for this object
        :return: all attributes not serialized by this method
        :rtype: dict
        """
        return attrs

    def get_attrs(self):
        """
        Recursively serialize all attributes of this item and any contained
        items

        :return: serializable dict of item and contained items
        :rtype: dict
        """
        skip_attrs = ['home']
        ret = self.get_special_attrs()

        for key in self.__dict__:
            if (key in ret) or (key in skip_attrs):
                continue

            attr = getattr(self, key)
            ret[key] = serialize(attr)

        ret.update({TYPE_KEY: self.__class__.full_class_name})
        return ret

    def set_attrs(self, attrs):
        """
        Recursively deserialize all attributes of this item and any contained
        items

        :param dict attrs: item attributes
        """
        item = None
        attrs = self.set_special_attrs(attrs)

        if ('items' in attrs) and (type(attrs['items']) == list):
            for d in attrs['items']:
                item = deserialize(d)
                self.add_item(item)

            del attrs['items']

        for key in attrs:
            if key == TYPE_KEY:
                continue

            attr = attrs[key]
            if not hasattr(self, key):
                raise RuntimeError("Error: %s object has no attribute '%s'"
                    % (type(self).__name__, key))

            item = deserialize(attr)
            setattr(self, key, item)

    def add_item(self, item):
        """
        Put an item inside this item

        :param text_game_maker.game_objects.base.GameEntity item: item to add
        """
        item.move(self.items)

    def add_items(self, items):
        """
        Put multiple items inside this item

        :param [text_game_maker.game_objects.base.GameEntity] items: list of\
            items to add
        """
        for item in items:
            item.move(self.items)

    def add_to_player_inventory(self, player):
        """
        Put this item inside player's inventory. If add_to_player_inventory
        returns True, execution of the current command will continue normally.
        If False, execution of the current command will stop immediately.

        :param text_game_maker.player.player.Player player: player object
        :return: True if command execution should continue
        :rtype: bool
        """

        if len(player.pockets.items) < player.pockets.capacity:
            return player.pockets.add_item(self)
        elif not player.inventory:
            utils._wrap_print("No bag to hold items")
            utils.save_sound(audio.FAILURE_SOUND)
            return False
        elif len(player.inventory.items) < player.inventory.capacity:
            return player.inventory.add_item(self)

        utils._wrap_print("No space to hold the %s." % self.name)
        return False

    def delete(self):
        """
        Delete the instance of this item from whatever location list it lives in
        (if any)
        """
        if self.home:
            del self.home[self.home.index(self)]
            self.home = None

    def move(self, location):
        """
        Move this item to a different location list

        :param list location: location list to move item to
        """
        location.append(self)
        self.delete()
        self.home = location

    def on_equip(self, player):
        """
        Called when player equips this item from inventory

        :param text_game_maker.player.player.Player player: player object
        """
        utils.game_print("Equipped %s." % self.name)

    def on_unequip(self, player):
        """
        Called when player unequips this item from inventory (by unequipping
        explicitly, by dropping or by equipping a different item)

        :param text_game_maker.player.player.Player player: player object
        """
        pass

    def on_burn(self, player):
        """
        Called when player burns this item.

        :param text_game_maker.player.player.Player player: player object
        """
        if self.home is player.inventory.items:
            utils.game_print("The %s is in your inventory. You "
                "shouldn't burn things in your inventory because your bag "
                "would catch fire." % self.name)
            return

        if self.combustible:
            if self.is_container:
                items = utils.get_all_contained_items(self,
                    lambda x: not x.combustible)

                for item in items:
                    if item.combustible:
                        item.delete()
                    else:
                        item.location = self.location
                        player.current.add_item(item)

            msg = messages.burn_combustible_message(self.name)
            self.delete()
        else:
            msg = messages.burn_noncombustible_message(self.name)

        utils.game_print(msg)

    def on_read(self, player):
        """
        Called when player reads this item

        :param text_game_maker.player.player.Player player: player object
        """
        msg = 'read the %s' % self.name
        utils._wrap_print(messages.nonsensical_action_message(msg))

    def on_speak(self, player):
        """
        Called when player speaks to this item

        :param text_game_maker.player.player.Player player: player object
        """
        utils.game_print("%s says nothing." % self.prep)

    def on_take(self, player):
        """
        Called when player attempts to take this item. If on_take returns True,
        this item will be added to player's inventory. If False, this item will
        not be added to player's inventory.

        :param text_game_maker.player.player.Player player: player object
        """
        return True

    def on_look(self, player):
        """
        Called when player looks at this item

        :param text_game_maker.player.player.Player player: player object
        """
        utils.game_print("It's a %s" % self.name)

    def on_look_under(self, player):
        """
        Called when player looks under this item

        :param text_game_maker.player.player.Player player: player object
        """
        utils.game_print("There is not much to see under the %s"
            % self.name)

    def on_eat(self, player, word):
        """
        Called when player eats this item

        :param text_game_maker.player.player.Player player: player object
        :param str word: command word used by player
        """
        if self.alive:
            msg = "%s is still alive. You cannot eat living things." % self.name

        if self.edible:
            utils.game_print("You %s %s." % (word, self.prep, self.energy))
            self.delete()
        else:
            utils.game_print(messages.nonsensical_action_message('%s %s'
                % (word, self.name)))
            utils.save_sound(audio.FAILURE_SOUND)
