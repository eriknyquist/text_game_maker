import text_game_maker

craftables = {}

def add(items, item):
    craftables[item.name] = (items, item)

def _get_inventory_item(name, inventory):
    for item in inventory.items:
        if item.name == name:
            return item

    return None

def _need_items(name, word, items):
    names = ['%s %s' % (x.prefix, x.name) for x in items]
    text_game_maker.game_print("Can't %s %s. You need %s."
            % (word, name, text_game_maker.list_to_english(names)))

def craft(name, word, inventory):
    if not name in craftables:
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
    text_game_maker.save_sound(text_game_maker.audio.CRAFT_SOUND)
    text_game_maker.game_print("Created %s." % name)
