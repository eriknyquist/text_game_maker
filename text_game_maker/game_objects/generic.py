from text_game_maker.game_objects.base import GameEntity
from text_game_maker.materials.materials import Material
from text_game_maker.audio import audio
from text_game_maker.utils import utils
from text_game_maker.messages import messages


class ItemSize(object):
    SMALL = 1
    MEDIUM = 2
    LARGE = 3
    VERY_LARGE = 4


class Item(GameEntity):
    """
    Base class for collectable item
    """

    def __init__(self, prefix="", name="", **kwargs):
        """
        Initialises an Item instance

        :param str prefix: Generally either "a" or "an"
        :param str name: Item name, e.g. "apple"
        :param str location: Item location, e.g. "on the floor"
        :param int value: Item value in coins
        """

        super(Item, self).__init__()

        self.combustible = True
        self.inanimate = True
        self.edible = False
        self.damage = 0
        self.value = 0
        self.location = ""

        self.prefix = prefix
        self.name = name
        self.size = ItemSize.SMALL

        for key in kwargs:
            if not hasattr(self, key):
                raise KeyError("keyword argument '%s': %s instance has no such "
                    "attribute" % (key, self.full_class_name))

            setattr(self, key, kwargs[key])

    def on_eat(self, player, word):
        """
        Called when player eats this item

        :param text_game_maker.player.player.Player player: player object
        :param str word: command word used by player
        """
        if self.size > ItemSize.SMALL:
            utils.game_print(messages.nonsensical_action_message('%s %s'
                % (word, self.prep)))
            utils.save_sound(audio.FAILURE_SOUND)
            return

        if self.edible:
            msg = "You %s %s and gain %d energy point" % (word, self.prep,
                self.energy)

            if (self.energy == 0) or (self.energy > 1):
                msg += "s"

            player.increment_energy(self.energy)
            self.delete()

        elif self.damage > 0:
            msg = ("You try your best to %s %s, but you fail, and injure "
                "yourself. You have lost %d health points." % (word, self.prep,
                self.damage))

            if player.health <= self.damage:
                utils._wrap_print(msg + " You are dead.")
                player.death()
                sys.exit()

            player.decrement_health(self.damage)

        else:
            msg = "You %s %s. %s" % (word, self.prep, messages.bad_taste_message())
            self.delete()

        if msg:
            utils.game_print(msg)

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

    def set_location(self, desc):
        """
        Set the location description of the item, e.g. "on the floor". Items
        with the same location description will automatically be grouped when
        described to the player, e.g."an apple, a key and a knife are on the
        floor"

        :param str desc: item location description
        """

        self.location = desc

    def set_value(self, value):
        """
        Set the value of this item in coins

        :param int value: item value in coins
        """

        self.value = value

    def __eq__(self, other):
        return other and self.name == other.name

    def __neq__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        if self.prefix not in ['', None]:
            return '%s %s' % (self.prefix, self.name)

        return self.name

    def __repr__(self):
        return self.__str__()


class FuelConsumer(Item):
    def __init__(self, *args, **kwargs):
        self.max_fuel = 100.0
        self.fuel_decrement = 1.0
        super(FuelConsumer, self).__init__(*args, **kwargs)

        self.fuel = self.max_fuel
        self.spent = False
        self.original_name = None

        # Item name will change to this when fuel is spent
        self.spent_name = "dead %s" % self.name

        # Message to be used when fuel is spent but player attempts some action
        # that requires fuel
        self.spent_use_message = "%s is dead." % self.name

    def on_fuel_empty(self):
        pass

    def on_refuel(self):
        pass

    def make_spent(self, print_output=True):
        self.spent = True
        self.original_name = self.name
        self.name = self.spent_name
        self.on_fuel_empty(print_output)

    def refuel(self, fuel=None):
        if fuel is None:
            fuel = self.max_fuel

        self.fuel = min(self.max_fuel, fuel)
        if (self.fuel > 0) and self.spent:
            self.spent = False
            self.name = self.original_name
            self.on_refuel()

    def set_fuel(self, value):
        self.fuel = value

    def get_fuel(self):
        return self.fuel

    def decrement_fuel(self):
        if self.spent:
            return

        self.set_fuel(self.get_fuel() - self.fuel_decrement)

        if self.get_fuel() <= 0.0:
            self.make_spent()


class LightSource(FuelConsumer):
    """
    Base class for any item that can act as a light source
    """
    def __init__(self, *args, **kwargs):
        super(LightSource, self).__init__(*args, **kwargs)
        self.is_light_source = True

        # Message used to describe how this light source illuminates
        # player's surroundings
        self.illuminate_msg = "illuminating everything around you"

        # Message used when player equips this light source in a dark place
        self.equip_msg = ("You take out the %s, %s." % (self.name,
            self.illuminate_msg))

        # Message used when player equips this light source but it is spent
        self.spent_equip_msg = ("You take out the %s. The %s does not work "
            "anymore." % (self.name, self.name))

        # Message used when this light source becomes spent
        self.spent_message = "The %s has stopped working." % self.name

        self.original_equip_msg = self.equip_msg

    def _describe_partial(self, player):
        txt = player.current.summary() + player.describe_current_tile_contents()
        if player.current.first_visit:
            player.current.first_visit = False
            if player.current.first_visit_message:
                txt += player.current.first_visit_message

        return txt

    def on_fuel_empty(self, print_output=True):
        self.is_light_source = False
        self.original_equip_msg = self.equip_msg
        self.equip_msg = self.spent_equip_msg

        if print_output and (self.spent_message is not None):
            utils.game_print(self.spent_message)

    def on_refuel(self):
        self.is_light_source = True
        self.equip_msg = self.original_equip_msg

        builder_ins = utils.get_builder_instance()
        if builder_ins is None:
            return

        player = builder_ins.player
        if self is not player.equipped:
            return

        utils.game_print("The %s lights up, %s." % (self.name,
            self.illuminate_msg), wait=True)

        if not player.current.dark:
            return

        utils.game_print(self._describe_partial(player), wait=True)

    def on_equip(self, player):
        if not player.current.dark:
            super(LightSource, self).on_equip(player)
            return

        utils.game_print(self.equip_msg)

        if self.get_fuel() > 0.0:
            utils.game_print(self._describe_partial(player))

    def on_unequip(self, player):
        if (not player.can_see()) and (not self.spent):
            utils.game_print(player.darkness_message())


class ElectricLightSource(LightSource):
    """
    Base class for an item that can be used as a light source, and can be
    rejuvenated with batteries when dead
    """
    def __init__(self, *args, **kwargs):
        super(ElectricLightSource, self).__init__(*args, **kwargs)
        self.requires_electricity = True
        self.is_container = True
        self.capacity = 1
        self.spent_equip_msg = ("You take out the %s. The %s needs a new "
            "battery to work." % (self.name, self.name))

    def get_fuel(self):
        if not self.items:
            return 0.0

        if not self.items[0].is_electricity_source:
            return 0.0

        return self.items[0].fuel

    def set_fuel(self, value):
        if not self.items:
            return

        if not self.items[0].is_electricity_source:
            return

        self.items[0].set_fuel(value)

    def add_item(self, item):
        if not item.is_electricity_source:
            utils._wrap_print(messages.pointless_action_message(
                "put the %s in the %s" % (item.name, self.name)))
            return None

        if item.size > self.size:
            utils._wrap_print(messages.container_too_small_message(item.prep,
                self.prep))
            return None

        self.refuel()
        return item.move(self.items)


class FlameSource(LightSource):
    """
    Base class for anything that can be used as a flame source
    """
    def __init__(self, *args, **kwargs):
        super(FlameSource, self).__init__(*args, **kwargs)
        self.is_flame_source = True


class Container(Item):
    """
    Generic container with limited capacity and item size
    """
    def __init__(self, *args, **kwargs):
        super(Container, self).__init__(*args, **kwargs)
        self.is_container = True

    def add_item(self, item):
        if item is self:
            utils.game_print("How can you put the %s inside itself?"
                % (item.name))
            return None

        if len(self.items) >= self.capacity:
            utils._wrap_print("The %s is full" % self.name)
            return None

        if self.size < item.size:
            utils.game_print(messages.container_too_small_message(
                item.prep, self.prep))
            return None

        return item.move(self.items)


class LargeContainer(Container):
    """
    Generic container with limited capacity and item size
    """
    def __init__(self, *args, **kwargs):
        super(LargeContainer, self).__init__(*args, **kwargs)
        self.size = ItemSize.LARGE
        self.capacity = 2


class InventoryBag(Container):
    """
    Class to represent a small bag used to carry player items
    """

    def __init__(self, *args, **kwargs):
        super(InventoryBag, self).__init__(*args, **kwargs)
        self.material = Material.LEATHER
        self.capacity = 10
        self.size = ItemSize.MEDIUM

    def add_to_player_inventory(self, player):
        # Copy existing player items from old bag
        if player.inventory and player.inventory.items:
            for i in range(len(player.inventory.items)):
                if i == self.capacity:
                    break

                self.add_item(player.inventory.items[0])

        if player.inventory:
            # Drop old bag on the ground
            player.inventory.location = "on the ground"
            player.current.add_item(player.inventory)

        # Give new bag to player
        player.inventory = self
        self.delete()

        utils.save_sound(audio.NEW_ITEM_SOUND)
        utils.game_print("You now have a %s." % self.name)
        return player.inventory
