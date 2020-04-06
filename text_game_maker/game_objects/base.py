import sys
import copy
from future.utils import with_metaclass

import text_game_maker
from text_game_maker.messages import messages
from text_game_maker.utils import utils
from text_game_maker.audio import audio
from text_game_maker.materials.materials import Material, get_properties
from text_game_maker.game_objects import __object_model_version__

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

def deserialize(data, version):
    """
    Recursively deserialize item and all contained items

    :param dict data: serialized item data
    :param str version: object model version of serialized data
    :return: deserialized object
    """
    if is_deserializable_type(data):
        item = build_instance(data[TYPE_KEY])
        item.set_attrs(data, version)
    elif type(data) == list:
        item = []

        if len(data) > 0:
            for sub in data:
                item.append(deserialize(sub, version))
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

class ObjectModelMigration(object):
    def __init__(self, from_version, to_version, migration_function):
        self.from_version = from_version
        self.to_version = to_version
        self._do_migration = migration_function

    def migrate(self, attrs):
        return self._do_migration(attrs)

class GameEntity(object, with_metaclass(utils.SubclassTrackerMetaClass, object)):
    """
    Base class for anything that the player can interact with in the
    game, like usable items, food, people, etc.

    :ivar bool inanimate: defines whether this item is an inanimate object
    :ivar bool combustible: defines whether this item can be destroyed by fire
    :ivar bool scenery: defines whether this item is scenery; an immovable \
        prop in the scene that should be mentioned before smaller interactive \
        items when describing a room, e.g. furniture, architectural features \
        of the room
    :ivar bool edible: defines whether this item is edible
    :ivar bool alive: defines whether this item is currently alive
    :ivar int energy: defines how much energy player gains by consuming this \
        item
    :ivar int damage: defines how much health player loses if damaged by this \
        item

    :ivar int value: defines how much money player will make by selling this \
        item
    :ivar str name: name that this item will be referred to as in the game \
        (e.g. "metal key")
    :ivar str prefix: preceding word required when mentioning item, e.g. "a" \
        for "a metal key", and "an" for "an apple"
    :ivar list home: list that this Item instance lives inside; required for \
        the deleting/moving items within the game world
    :ivar bool is_container: defines whether this item can contain other items
    :ivar bool is_electricity_source: defines whether this item is an \
        electricity source
    :ivar bool requires_electricity: defines whether this item requires an \
        electricity source to operate
    :ivar bool is_flame_source: defines whether this item can be used as a \
        flame source
    :ivar bool is_light_source: defines whether this item can be used as a \
        light source
    :ivar Material material: material this item is made of
    :ivar int capacity: number of items this item can contain (if container)
    :ivar list items: items contained inside this item (if container)
    :ivar int size: size of this item; containers cannot contain items with a \
        larger size than themselves
    :ivar str verb: singluar verb e.g. "the key is on the floor", or plural \
        e.g. "the coins are on the floor"
    """

    global_skip_attrs = ['home', '_migrations']
    skip_attrs = []

    def __init__(self):
        self._migrations = []
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
        self._prep = None
        self.home = None
        self.is_container = False
        self.is_light_source = False
        self.is_flame_source = False
        self.is_electricity_source = False
        self.requires_electricity = False
        self.material = Material.WOOD
        self.capacity = 0
        self.items = []
        self.size = 1
        self.verb = "is"

    @property
    def prep(self):
        if self._prep in ["", None]:
            return 'the ' + str(self.name)

        return str(self._prep)

    @prep.setter
    def prep(self, val):
        self._prep = val

    def matches_name(self, name):
        """
        Tests if name matches this item's name. Will accept substrings of a
        matching name, e.g. Item(name="metal key").matches_name("key") will
        return True.

        :param str name: name to compare against this item's name
        :return: True if name matches this items name
        :rtype: bool
        """
        target = self.name.lower()
        name = name.lower()

        if name.startswith('the '):
            name = name[4:]

        if target.startswith(name) or (name in target):
            return True

        return False

    def add_migration(self, from_version, to_version, migration_function):
        """
        Add function to migrate a serialized version of this object to a new
        object model version

        :param str from_version: version to migrate from
        :param str to_version: version to migrate to
        :param migration_function: function to perform migration
        """
        m = ObjectModelMigration(from_version, to_version, migration_function)
        self._migrations.append(m)

    def migrate(self, old_version, attrs):
        """
        Migrate serialized version of this object to the current object model
        version

        :param str old_version: object model version to migrate from
        :param attrs: object to migrate as a serialized dict
        :return: migrated serialized dict
        """
        current_version = old_version
        for migration in self._migrations:
            if migration.from_version == current_version:
                attrs = migration.migrate(attrs)
                current_version = migration.to_version

        return attrs

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

    def set_special_attrs(self, attrs, version):
        """
        Deserialize any attributes that you want to handle specially here.
        Make sure to delete any specially handled attributes from the return
        dict so that they are not deserialized by the main set_attrs method

        :param dict attrs: all serialized attributes for this object
        :param str version: object model version of serialized attributes
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
        to_skip = self.__class__.global_skip_attrs + self.__class__.skip_attrs
        ret = self.get_special_attrs()

        for key in self.__dict__:
            if (key in ret) or (key in to_skip):
                continue

            attr = getattr(self, key)
            ret[key] = serialize(attr)

        ret.update({TYPE_KEY: self.__class__.full_class_name})
        return ret

    def set_attrs(self, attrs, version):
        """
        Recursively deserialize all attributes of this item and any contained
        items

        :param dict attrs: item attributes
        :param str version: object model version of item attributes
        """
        item = None

        if version != __object_model_version__:
            attrs = self.migrate(version, attrs)

        attrs = self.set_special_attrs(attrs, version)

        if ('items' in attrs) and (type(attrs['items']) == list):
            for d in attrs['items']:
                item = deserialize(d, version)
                self.add_item(item)

            del attrs['items']

        for key in attrs:
            if key == TYPE_KEY:
                continue

            attr = attrs[key]
            if not hasattr(self, key):
                raise RuntimeError("Error: %s object has no attribute '%s'"
                    % (type(self).__name__, key))

            item = deserialize(attr, version)
            setattr(self, key, item)

    def add_item(self, item):
        """
        Put an item inside this item

        :param text_game_maker.game_objects.base.GameEntity item: item to add
        :return: the item that was added
        """
        return item.move(self.items)

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
        :return: the object that was added
        """

        if len(player.pockets.items) < player.pockets.capacity:
            return player.pockets.add_item(self)
        elif not player.inventory:
            utils._wrap_print("No bag to hold items")
            utils.save_sound(audio.FAILURE_SOUND)
            return None
        elif len(player.inventory.items) < player.inventory.capacity:
            return player.inventory.add_item(self)

        utils._wrap_print("No space to hold the %s." % self.name)
        return None

    def copy(self):
        new = copy.deepcopy(self)
        new.items = []

        for item in self.items:
            new.add_item(item.copy())

        return new

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
        :return: item that was moved
        """
        location.append(self)
        self.delete()
        self.home = location
        return location[-1]

    def on_attack(self, player, item):
        """
        Called when player attacks this item

        :param text_game_maker.player.player.Player player: player instance
        :param text_game_maker.game_objects.base.GameEntity item: item that\
            player is using to attack this item
        """
        utils.game_print(messages.attack_inanimate_object_message(self.name,
            item.name))

    def on_smell(self, player):
        """
        Called when player smells this item

        :param text_game_maker.player.player.Player player: player object
        """
        utils.game_print("%s smells %s."
            % (self.name, get_properties(self.material).smell))

    def on_taste(self, player):
        """
        Called when player tastes this item

        :param text_game_maker.player.player.Player player: player object
        """
        utils.game_print("%s tastes %s."
            % (self.name, get_properties(self.material).taste))

    def on_open(self, player):
        """
        Called when player opens this item

        :param text_game_maker.player.player.Player player: player object
        """
        if not self.is_container:
            utils.game_print("%s cannot be opened." % self.prep)
            return

        utils.game_print("You open %s and look inside." % self.prep)
        utils.printfunc("\n" + utils.container_listing(self, bottom_border=True))

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

        elif self.home is player.pockets.items:
            utils.game_print("The %s is in your pocket. You shouldn't burn "
                "things in your pockets because your trousers would catch on "
                "fire." % self.name)
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
