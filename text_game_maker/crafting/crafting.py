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

def deserialize(data):
    d = {}
    for key in data:
        items, item = data[key]
        d[key] = [base_deserialize(items), base_deserialize(item)]

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

def _get_inventory_item(name, inventory):
    for item in inventory.items:
        if item.name == name:
            return item

    return None

def _need_items(name, word, items):
    names = [str(x) for x in items]
    utils.save_sound(audio.FAILURE_SOUND)
    utils.game_print("Can't %s %s. Need %s."
            % (word, name, utils.list_to_english(names)))

def craft(name, word, inventory):
    """
    Craft an item by name

    :param str name: name of the item to craft
    :param str word: command/action word used by player
    :param text_game_maker.game_objects.items.Container inventory: inventory\
        object to use for crafting
    :return: crafted item
    :rtype: text_game_maker.game_objects.items.Item
    """
    items = []
    item = None

    if name in craftables:
        items, item = craftables[name]
    else:
        for k in craftables:
            if k.startswith(name) or k.endswith(name) or (k in name):
                items, item = craftables[k]
                break

    if (not items) or (not item):
        utils.save_sound(audio.FAILURE_SOUND)
        utils.game_print("Don't know how to %s %s" % (word, name))
        return

    ingredients = []

    for i in items:
        ingredient = _get_inventory_item(i.name, inventory)
        if ingredient is None:
            _need_items(name, word, items)
            return

        ingredients.append(ingredient)

    for i in ingredients:
        i.delete()

    inventory.add_item(item)
    utils.save_sound(audio.NEW_ITEM_SOUND)
    utils.game_print("Created %s." % item.name)
