import text_game_maker

craftables = {}

def add(items, item):
    """
    Add new craftable item

    :param [text_game_maker.items.Item] items: list of ingredients
    :param text_game_maker.items.Item item: new item created by combining\
        ingredients
    """
    craftables[item.name] = (items, item)

def help_text():
    """
    Retreive human-readable description of all added craftable items

    :return: description of all added craftable items
    :rtype: str
    """
    ret = []
    for name in craftables:
        items, item = craftables[name]
        item_names = text_game_maker.list_to_english([str(x) for x in items])
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
    text_game_maker.save_sound(text_game_maker.audio.FAILURE_SOUND)
    text_game_maker.game_print("Can't %s %s. Need %s."
            % (word, name, text_game_maker.list_to_english(names)))

def craft(name, word, inventory):
    """
    Craft an item by name

    :param str name: name of the item to craft
    :param str word: command/action word used by player
    :param text_game_maker.items.Container inventory: inventory object to use\
        for crafting
    """
    if not name in craftables:
        text_game_maker.save_sound(text_game_maker.audio.FAILURE_SOUND)
        text_game_maker.game_print("Don't know how to %s %s" % (word, name))
        return

    ingredients = []
    items, item = craftables[name]

    for i in items:
        ingredient = _get_inventory_item(i.name, inventory)
        if ingredient is None:
            _need_items(name, word, items)
            return

        ingredients.append(ingredient)

    for i in ingredients:
        i.delete()

    inventory.add_item(item)
    text_game_maker.save_sound(text_game_maker.audio.NEW_ITEM_SOUND)
    text_game_maker.game_print("Created %s." % name)
