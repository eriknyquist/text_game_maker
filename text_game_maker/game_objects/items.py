import text_game_maker
from text_game_maker.messages import messages
from text_game_maker.game_objects.base import GameEntity
from text_game_maker.audio import audio
from text_game_maker.crafting import crafting
from text_game_maker.utils import utils

ITEM_SIZE_SMALL = 1
ITEM_SIZE_MEDIUM = 2
ITEM_SIZE_LARGE = 3
ITEM_SIZE_VERY_LARGE = 4

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
        self.edible = True
        self.value = 0
        self.location = ""
        self.name = name
        self.prep = 'the ' + name

        self.prefix = prefix
        self.size = ITEM_SIZE_SMALL

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
        if self.alive:
            msg = "%s is still alive. You cannot eat living things." % self.name

        if self.size > ITEM_SIZE_SMALL:
            utils.game_print(messages.nonsensical_action_message('%s %s'
                % (word, self.name)))
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
            msg = "You %s the %s. %s" % messages.bad_taste_message()

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
        if self.prefix:
            return '%s %s' % (self.prefix, self.name)

        return self.name

class Lighter(Item):
    def __init__(self, **kwargs):
        super(Lighter, self).__init__("a", "lighter", **kwargs)
        self.is_light_source = True

    def on_equip(self, player):
        if player.can_see():
            super(Lighter, self).on_equip(player)
            return

        utils.game_print("You take out the %s, illuminating everything around "
            "you with a soft, pulsating orange glow." % self.name)

        txt = player.current.summary() + player.describe_current_tile_contents()
        if player.current.first_visit:
            player.current.first_visit = False
            if player.current.first_visit_message:
                txt += player.current.first_visit_message

        utils.game_print(txt)

    def on_unequip(self, player):
        if not player.can_see():
            utils.game_print(player.darkness_message())

    def on_burn(self, player):
        utils.game_print("You can't burn the %s with itself."
            % self.name)

class Weapon(Item):
    """
    Class to represent a weapon
    """

    def __init__(self, prefix="", name="", **kwargs):
        super(Weapon, self).__init__(prefix, name, **kwargs)
        self.edible = False
        self.damage = damage

class Food(Item):
    """
    Class to represent a food item
    """

    def __init__(self, prefix="", name="", **kwargs):
        super(Food, self).__init__(prefix, name, location, value)
        self.edbile = True
        self.energy = energy

class Coins(Item):
    def __init__(self, **kwargs):
        self.value = 1
        super(Coins, self).__init__(None, "", **kwargs)
        self.combustible = False
        self._set_name()

    def _set_name(self):
        self.name = "%s coin" % self.value
        if self.value > 1:
            self.verb = "are"
            self.name += "s"

    def add_to_player_inventory(self, player):
        other_coins = utils.find_inventory_item_class(player, Coins)
        if not other_coins:
            return super(Coins, self).add_to_player_inventory(player)

        other_coins.value += self.value
        other_coins._set_name()
        self.delete()
        return True

class Paper(Item):
    def __init__(self, prefix="", name="", **kwargs):
        self.paragraphs = []
        self.header = None
        self.footer = None
        super(Paper, self).__init__(prefix, name, **kwargs)

    def paragraphs_text(self):
        ret = []

        for p in self.paragraphs:
            centered_lines = []
            lines = utils._wrap_text(p).split('\n')

            for line in lines:
                formatted = utils.replace_format_tokens(line)
                centered_lines.append(utils.centre_text(formatted))

            ret.append('\n'.join(centered_lines))

        return '\n\n'.join(ret)

    def header_text(self):
        htxt = utils.replace_format_tokens(self.header)
        return utils.line_banner(htxt)

    def footer_text(self):
        ftxt = utils.replace_format_tokens(self.footer)
        return utils.line_banner(ftxt)

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
    def __init__(self, ingredients=[], item=None, **kwargs):
        super(Blueprint, self).__init__("a", "blueprint for %s" % item,
            **kwargs)
        self.ingredients = ingredients
        self.item = item

    def add_to_player_inventory(self, player):
        return True

    def on_take(self, player):
        crafting.add(self.ingredients, self.item)
        utils._wrap_print("You have learned how to make %s." % self.item)
        utils.save_sound(audio.NEW_ITEM_SOUND)
        self.delete()
        return True

class Furniture(Item):
    def __init__(self, prefix="", name="", **kwargs):
        super(Furniture, self).__init__(prefix, name, **kwargs)
        self.scenery = True
        self.size = ITEM_SIZE_LARGE

class Container(Item):
    """
    Class to represent a container with limited capacity and item size
    """

    def __init__(self, *args, **kwargs):
        super(Container, self).__init__(*args, **kwargs)
        self.is_container = True

    def add_item(self, item):
        if item is self:
            utils.game_print("How can you put the %s inside itself?"
                % (item.name))
            return False

        if len(self.items) >= self.capacity:
            utils._wrap_print("The %s is full" % self.name)
            return False

        if self.size < item.size:
            utils.game_print(messages.container_too_small_message(
                item.name, self.name))
            return False

        item.move(self.items)
        return True

class LargeContainer(Container):
    def __init__(self, *args, **kwargs):
        super(LargeContainer, self).__init__(*args, **kwargs)
        self.size = ITEM_SIZE_LARGE
        self.capacity = 2

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
        return True

class PaperBag(Container):
    """
    Class to represent a small bag used to carry player items
    """
    def __init__(self, *args, **kwargs):
        super(PaperBag, self).__init__(*args, **kwargs)
        self.capacity = 5
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
