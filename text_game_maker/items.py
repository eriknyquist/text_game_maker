import text_game_maker
from text_game_maker import messages
from text_game_maker.base import GameEntity

ITEM_SIZE_SMALL = 1
ITEM_SIZE_MEDIUM = 2
ITEM_SIZE_LARGE = 3
ITEM_SIZE_VERY_LARGE = 4

class Item(GameEntity):
    """
    Base class for collectable item
    """

    def __init__(self, prefix, name, **kwargs):
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
        self.edible = True
        self.value = 0
        self.location = ""
        self.name = name
        self.prep = 'the ' + name

        self.prefix = prefix
        self.size = ITEM_SIZE_SMALL

        for key in kwargs:
            setattr(self, key, kwargs[key])

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
        if self.prefix:
            return '%s %s' % (self.prefix, self.name)

        return self.name

class Lighter(Item):
    def __init__(self, **kwargs):
        super(Lighter, self).__init__("a", "lighter", **kwargs)

    def on_burn(self, player):
        text_game_maker.game_print("You can't burn the %s with itself."
            % self.name)

class Weapon(Item):
    """
    Class to represent a weapon
    """

    def __init__(self, prefix, name, **kwargs):
        super(Weapon, self).__init__(prefix, name, **kwargs)
        self.edible = False
        self.damage = damage

class Food(Item):
    """
    Class to represent a food item
    """

    def __init__(self, prefix, name, **kwargs):
        super(Food, self).__init__(prefix, name, location, value)
        self.edbile = True
        self.energy = energy

class Coins(Item):
    def __init__(self, **kwargs):
        self.value = 1
        self.combustible = False
        super(Coins, self).__init__(None, "", **kwargs)
        self.name = "%s coin" % self.value
        if self.value > 1:
            self.verb = "are"
            self.name += "s"

    def add_to_player_inventory(self, player):
        player.coins += self.value
        self.delete()
        return True

class Paper(Item):
    def __init__(self, prefix, name, **kwargs):
        self.paragraphs = []
        self.header = None
        self.footer = None
        super(Paper, self).__init__(prefix, name, **kwargs)

    def paragraphs_text(self):
        ret = []

        for p in self.paragraphs:
            centered_lines = []
            lines = text_game_maker._wrap_text(p).split('\n')

            for line in lines:
                formatted = text_game_maker.replace_format_tokens(line)
                centered_lines.append(text_game_maker.centre_text(formatted))

            ret.append('\n'.join(centered_lines))

        return '\n\n'.join(ret)

    def header_text(self):
        htxt = text_game_maker.replace_format_tokens(self.header)
        return text_game_maker.line_banner(htxt)

    def footer_text(self):
        ftxt = text_game_maker.replace_format_tokens(self.footer)
        return text_game_maker.line_banner(ftxt)

    def on_look(self, player):
        self.on_read(player)

    def on_read(self, player):
        msg = self.paragraphs_text()
        if self.header:
            msg = "%s\n\n%s" % (self.header_text(), msg)

        if self.footer:
            msg = "%s\n\n%s" % (msg, self.footer_text())

        print('\n' + msg)

class Blueprint(Item):
    def __init__(self, ingredients, item, **kwargs):
        super(Blueprint, self).__init__("a", "blueprint for %s" % item,
            **kwargs)
        self.ingredients = ingredients
        self.item = item

    def add_to_player_inventory(self, player):
        return True

    def on_take(self, player):
        text_game_maker.crafting.add(self.ingredients, self.item)
        text_game_maker._wrap_print("You can now make %s" % self.item)
        text_game_maker.save_sound(text_game_maker.audio.NEW_ITEM_SOUND)
        self.delete()
        return True

class Furniture(Item):
    def __init__(self, prefix, name, **kwargs):
        self.scenery = True
        self.size = ITEM_SIZE_LARGE
        super(Furniture, self).__init__(prefix, name, **kwargs)

class Container(Item):
    """
    Class to represent a container with limited capacity and item size
    """

    def __init__(self, *args, **kwargs):
        super(Container, self).__init__(*args, **kwargs)
        self.is_container = True

    def add_item(self, item):
        if item is self:
            text_game_maker.game_print("How can you put the %s inside itself?"
                % (item.name))
            return False

        if len(self.items) >= self.capacity:
            text_game_maker._wrap_print("The %s is full" % self.name)
            return False

        if self.size < item.size:
            text_game_maker.game_print(messages.container_too_small_message(
                item.name, self.name))
            return False

        item.move(self.items)
        return True

class SmallTin(Container):
    def __init__(self, *args, **kwargs):
        super(SmallTin, self).__init__(*args, **kwargs)
        self.combustible = False
        self.capacity = 3

class InventoryBag(Container):
    """
    Class to represent a small bag used to carry player items
    """

    def __init__(self, *args, **kwargs):
        super(InventoryBag, self).__init__(*args, **kwargs)
        self.capacity = 10
        self.size = ITEM_SIZE_MEDIUM

    def on_take(self, player):
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

        text_game_maker.save_sound(text_game_maker.audio.NEW_ITEM_SOUND)
        text_game_maker.game_print("You now have a %s." % self.name)

class PaperBag(Container):
    """
    Class to represent a small bag used to carry player items
    """
    def __init__(self, *args, **kwargs):
        super(PaperBag, self).__init__(*args, **kwargs)
        self.capacity = 10
        self.size = ITEM_SIZE_MEDIUM

class SmallBag(InventoryBag):
    def __init__(self, *args, **kwargs):
        super(SmallBag, self).__init__(*args, **kwargs)
        self.capacity = 5

class Bag(InventoryBag):
    def __init__(self, *args, **kwargs):
        super(Bag, self).__init__(*args, **kwargs)
        self.capacity = 10

class LargeBag(InventoryBag):
    def __init__(self, *args, **kwargs):
        super(LargeBag, self).__init__(*args, **kwargs)
        self.capacity = 20
