from text_game_maker.game_objects.base import GameEntity
from text_game_maker.materials.materials import Material, get_properties
from text_game_maker.audio import audio
from text_game_maker.crafting import crafting
from text_game_maker.utils import utils

from text_game_maker.game_objects.generic import *

class Battery(Item):
    def __init__(self, *args, **kwargs):
        super(Battery, self).__init__("a", "battery", **kwargs)
        self.is_electricity_source = True
        self.max_fuel = 100.0
        self.fuel = self.max_fuel
        self.size = ITEM_SIZE_SMALL
        self.spent_name = "dead %s" % self.name
        self.original_name = self.name

    def set_fuel(self, value):
        if (value == 0.0) and (self.fuel > 0.0):
            self.name = self.spent_name
        elif (value > 0.0) and (self.fuel == 0.0):
            self.name = original_name

        self.fuel = min(self.max_fuel, value)

class Flashlight(ElectricLightSource):
    def __init__(self, *args, **kwargs):
        super(Flashlight, self).__init__("a", "flashlight", **kwargs)
        self.size = ITEM_SIZE_SMALL
        self.material = Material.PLASTIC
        self.fuel = 0.0
        self.illuminate_msg = ("casting a bright white light across everything "
            "in front of you")
        self.equip_msg = ("You take out the %s, and switch it on. It has "
            "a wide beam, %s." % (self.name, self.illuminate_msg))
        self.make_spent()

    def on_take(self, player):
        if self.get_fuel() <= 0.0:
            utils.game_print("%s needs a battery to work." % self.name)

        return True

class Lighter(FlameSource):
    def __init__(self, *args, **kwargs):
        super(Lighter, self).__init__("a", "lighter", **kwargs)
        self.size = ITEM_SIZE_SMALL
        self.material = Material.PLASTIC
        self.fuel = 20.0
        self.equip_msg = ("You take out the %s, illuminating everything "
            "around you with a dancing yellow glow." % self.name)

class Matches(FlameSource):
    def __init__(self, *args, **kwargs):
        super(Matches, self).__init__("a", "box of matches", **kwargs)
        self.size = ITEM_SIZE_SMALL
        self.material = Material.CARDBOARD
        self.fuel = 10.0
        self.spent_name = "empty %s" % self.name
        self.spent_use_message = "%s is empty." % self.name
        self.equip_msg = ("You strike a match, illuminating everything "
            "around you with a soft orange glow.")
        self.spent_equip_msg = ("You take out the %s, which is empty."
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
        self.material = Material.MEAT
        self.edbile = True
        self.energy = energy

class Coins(Item):
    def __init__(self, **kwargs):
        self.value = 1
        super(Coins, self).__init__(None, "", **kwargs)
        self.material = Material.METAL
        self.combustible = False
        self.prep = "the coins"
        self._set_name()

    def _set_name(self):
        self.name = "%s coin" % self.value
        if self.value > 1:
            self.verb = "are"
            self.name += "s"

    def on_taste(self, player):
        tasteword = "taste"

        if self.value == 1:
            smellword += "s"

        taste = get_properties(self.material).taste
        utils.game_print("%s %s %s." % (self.name, tasteword, taste))

    def on_smell(self, player):
        smellword = "smell"

        if self.value == 1:
            smellword += "s"

        smell = get_properties(self.material).smell
        utils.game_print("%s %s %s." % (self.name, smellword, smell))

    def add_to_player_inventory(self, player):
        other_coins = utils.find_inventory_item_class(player, Coins)
        if not other_coins:
            return super(Coins, self).add_to_player_inventory(player)

        other_coins.value += self.value
        other_coins._set_name()
        self.delete()
        return other_coins

class Paper(Item):
    def __init__(self, prefix="", name="", **kwargs):
        self.paragraphs = []
        self.header = None
        self.footer = None
        super(Paper, self).__init__(prefix, name, **kwargs)
        self.material = Material.PAPER

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

        utils.printfunc('\n' + msg)

class Blueprint(Item):
    def __init__(self, ingredients=[], item=None, **kwargs):
        super(Blueprint, self).__init__("a", "blueprint for %s" % item,
            **kwargs)
        self.material = Material.PAPER
        self.ingredients = ingredients
        self.item = item

    def on_take(self, player):
        return True

    def add_to_player_inventory(self, player):
        crafting.add(self.ingredients, self.item)
        utils._wrap_print("You have learned how to make %s." % self.item)
        utils.save_sound(audio.NEW_ITEM_SOUND)
        self.delete()
        return self

class Furniture(Item):
    def __init__(self, prefix="", name="", **kwargs):
        super(Furniture, self).__init__(prefix, name, **kwargs)
        self.material = Material.METAL
        self.scenery = True
        self.size = ITEM_SIZE_LARGE

class SmallTin(Container):
    def __init__(self, *args, **kwargs):
        super(SmallTin, self).__init__(*args, **kwargs)
        self.material = Material.METAL
        self.combustible = False
        self.capacity = 3

class PaperBag(Container):
    """
    Class to represent a small bag used to carry player items
    """
    def __init__(self, *args, **kwargs):
        super(PaperBag, self).__init__(*args, **kwargs)
        self.material = Material.PAPER
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

class Lockpick(Item):
    def __init__(self, *args, **kwargs):
        super(Lockpick, self).__init__("a", "lockpick", **kwargs)
        self.uses = 2

class StrongLockpick(Lockpick):
    def __init__(self, *args, **kwargs):
        super(StrongLockpick, self).__init__(*args, **kwargs)
        self.uses = 5

class AdvancedLockpick(Lockpick):
    def __init__(self, *args, **kwargs):
        super(AdvancedLockpick, self).__init__(*args, **kwargs)
        self.uses = 25

class Drawing(Item):
    def __init__(self, *args, **kwargs):
        super(Drawing, self).__init__(*args, **kwargs)
