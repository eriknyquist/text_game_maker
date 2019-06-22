import text_game_maker

from text_game_maker.audio import audio
from text_game_maker.utils import utils
from text_game_maker.game_objects.base import serialize as base_serialize
from text_game_maker.game_objects.base import deserialize as base_deserialize

craftables = {}

def serialize():
    ret = {}
    for name in craftables:
        items, item = craftables[name]
        ret[name] = [base_serialize(items), base_serialize(item)]

    return ret

def deserialize(data, version):
    d = {}
    for key in data:
        items, item = data[key]
        d[key] = [base_deserialize(items, version), base_deserialize(item, version)]

    craftables.clear()
    craftables.update(d)

def add(items, item):
    """
    Add new craftable item

    :param [text_game_maker.game_objects.items.Item] items: list of ingredients
    :param text_game_maker.game_objects.items.Item item: new item created by\
        combining ingredients
    """
    craftables[item.name] = [items, item]

def help_text():
    """
    Retreive human-readable description of all added craftable items

    :return: description of all added craftable items
    :rtype: str
    """
    ret = []
    for name in craftables:
        items, item = craftables[name]
        item_names = utils.list_to_english([str(x) for x in items])
        ret.append("%s: requires %s" % (item.name, item_names))

    if ret:
        return '\n'.join(ret)

    return None

def _find_item(item, items):
    for i in items:
        if (i.name == item.name) and isinstance(i, item.__class__):
            return i

    return None

def _find_craftable(name):
    items = []
    item = None

    if name in craftables:
        items, item = craftables[name]
    else:
        for k in craftables:
            if k.startswith(name) or k.endswith(name) or (k in name):
                items, item = craftables[k]
                break

    return items, item

def _need_items(name, word, items):
    names = [str(x) for x in items]
    utils.save_sound(audio.FAILURE_SOUND)
    utils.game_print("Can't %s %s. Need %s."
            % (word, name, utils.list_to_english(names)))

def can_craft(name):
    """
    Check if player has the ability to craft an item by name. Note this function
    only checks if player has acquired the blueprint to craft an item, and does
    not care whether the player has ingredients required to craft the item.

    :param str name: item name
    :return: True if player can craft the item, False otherwise
    :rtype: bool
    """
    _, item = _find_craftable(name)
    return not (item is None)

def craft(name, word, player):
    """
    Craft an item by name. Deletes ingredients from player's inventory and
    places crafted item into player's inventory.

    :param str name: name of the item to craft
    :param str word: command/action word used by player
    :param text_game_maker.player.player.Player player: player instance
    :return: crafted item, or None if crafting fails
    :rtype: text_game_maker.game_objects.items.Item
    """

    items, item = _find_craftable(name)
    if item is None:
        utils.save_sound(audio.FAILURE_SOUND)
        utils.game_print("Don't know how to %s %s" % (word, name))
        return None

    ingredients = []

    player_items = []
    player_items.extend(player.pockets.items)
    if player.inventory:
        player_items.extend(player.inventory.items)

    for i in items:
        ingredient = _find_item(i, player_items)
        if ingredient is None:
            _need_items(name, word, items)
            return None

        ingredients.append(ingredient)

    for i in ingredients:
        i.delete()

    item.prep = "your " + item.name
    item.add_to_player_inventory(player)
    utils.save_sound(audio.NEW_ITEM_SOUND)
    utils.game_print("Created %s." % item.name)
    return item
