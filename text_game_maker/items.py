import text_game_maker
from text_game_maker.base import GameEntity

class Item(GameEntity):
    """
    Base class for collectable item
    """

    def __init__(self, prefix, name, location, value):
        """
        Initialises an Item instance

        :param str prefix: Generally either "a" or "an"
        :param str name: Item name, e.g. "apple"
        :param str location: Item location, e.g. "on the floor"
        :param int value: Item value in coins
        """

        super(Item, self).__init__()

        self.inanimate = True
        self.edible = True
        self.value = value
        self.name = name
        self.prep = 'the ' + name

        self.prefix = prefix
        self.location = location

    def on_look(self, player):
        return "%s %s." % (self.prefix, self.name)

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
        return '%s %s' % (self.prefix, self.name)

class Weapon(Item):
    """
    Class to represent a weapon
    """

    def __init__(self, prefix, name, location, value, damage):
        super(Weapon, self).__init__(prefix, name, location, value)
        self.edible = False
        self.damage = damage

class Food(Item):
    """
    Class to represent a food item
    """

    def __init__(self, prefix, name, location, value, energy):
        super(Food, self).__init__(prefix, name, location, value)
        self.energy = energy

class InventoryBag(Item):
    """
    Class to represent a small bag used to carry player items
    """

    def __init__(self, prefix, name, location, value):
        super(InventoryBag, self).__init__(prefix, name, location, value)
        self.capacity = 5

    def on_take(self, player):
        # Copy existing player items from old bag
        if player.inventory and player.inventory.items:
            for i in range(len(player.inventory.items)):
                if i == self.capacity:
                    break

                self.add_item(player.inventory.items[0])

        if player.inventory:
            # Drop old bag on the floor
            player.inventory.location = "on the floor"
            player.current.add_item(player.inventory)

        # Give new bag to player
        player.inventory = self
        self.delete()

        text_game_maker.game_print("You now have a %s." % self.name)

    def is_container(self):
        return True

    def add_item(self, item):
        if len(self.items) >= self.capacity:
            text_game_maker._wrap_print("Your bag is full")
            return False

        item.move(self.items)
        return True

class SmallBag(InventoryBag):
    def __init__(self, prefix, name, location, value):
        super(SmallBag, self).__init__(prefix, name, location, value)
        self.capacity = 5

class Bag(InventoryBag):
    def __init__(self, prefix, name, location, value):
        super(SmallBag, self).__init__(prefix, name, location, value)
        self.capacity = 10

class LargeBag(InventoryBag):
    def __init__(self, prefix, name, location, value):
        super(SmallBag, self).__init__(prefix, name, location, value)
        self.capacity = 20
