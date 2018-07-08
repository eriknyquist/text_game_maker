import text_game_maker

from text_game_maker import map_builder as builder
from text_game_maker.parser import CommandParser

EAT_WORDS = [
    'eat', 'scoff', 'swallow', 'ingest', 'consume'
]

TAKE_WORDS = [
    'take', 'pick up', 'steal', 'acquire', 'grab', 'get', 'snatch', 'dock'
]

DROP_WORDS = [
    'drop', 'throw away', 'discard', 'chuck', 'ditch', 'delete', 'undock'
]

EQUIP_WORDS = [
    'equip', 'use', 'whip out', 'brandish', 'take out', 'get out'
]

UNEQUIP_WORDS = [
    'unequip', 'put away', 'stop using', 'stow'
]

SPEAK_WORDS = [
    'speak with', 'speak to', 'talk to', 'chat to', 'chat with', 'talk with',
    'chat', 'speak', 'talk'
]

INSPECT_WORDS = [
    'look at', 'inspect', 'examine'
]

LOOK_WORDS = [
    'look', 'peep', 'peek', 'show', 'viddy'
]

LOOT_WORDS = [
    'loot', 'search', 'rob', 'pickpocket'
]

def _take(player, item):
    # If on_take callback returns false, abort adding this item
    if not item.on_take(player):
        return False

    item.move(player.inventory['unequipped'])
    return True

def _do_eat(player, word, item_name):
    if not item_name or item_name == "":
        text_game_maker._wrap_print("What do you want to %s?" % word)
        return

    item = builder.find_inventory_item(player, item_name)
    if not item:
        item = builder.find_item(player, item_name)
        if not item:
            item = builder.find_person(player, item_name)
            if not item:
                text_game_maker._wrap_print("No %s available to %s"
                    % (item_name, word))
                return

    msg = item.on_eat(player, word)
    if msg:
        text_game_maker.game_print(msg)

def _do_take(player, word, item_name):
    if not item_name or item_name == "":
        text_game_maker._wrap_print("What do you want to %s?" % word)
        return

    if '*' in item_name:
        added = []
        item = ' '

        while item:
            item = builder.find_item_wildcard(player, item_name)
            if item and _take(player, item):
                added.append(item.name)

        if not added:
            text_game_maker._wrap_print("No matching items to %s" % word)
            return

        msg = text_game_maker.list_to_english(added)
    else:
        item = builder.find_item(player, item_name)
        if not item:
            text_game_maker._wrap_print("No %s available to %s" % (item_name, word))
            return

        msg = item.name
        if not _take(player, item):
            return

    text_game_maker.game_print('%s added to inventory' % msg)
    return

def _drop(player, n):
    # Place item on the floor in current room
    item = builder.find_inventory_item(player, n)
    if not item:
        return

    item.location = "on the floor"
    player.current.add_item(item)

def _do_drop(player, word, item_name):
    if not item_name or item_name == "":
        text_game_maker._wrap_print("What do you want to drop?")
        return

    msg = None
    if '*' in item_name:
        added = []
        item = ' '

        while item:
            item = builder.find_inventory_wildcard(player, item_name)
            if item:
                added.append(item.name)
                _drop(player, item.name)

        if not added:
            text_game_maker._wrap_print("No matching items to %s." % word)
            return

        msg = text_game_maker.list_to_english(added)
    else:
        item = builder.find_inventory_item(player, item_name)
        if not item:
            text_game_maker._wrap_print("No %s in your inventory to %s"
                % (item_name, word))
            return

        _drop(player, item.name)
        msg = item.name

    text_game_maker.game_print("Dropped %s" % msg)

def _do_speak(player, word, name):
    if not name or name == "":
        text_game_maker._wrap_print("Who do you want to speak to?")
        return

    p = builder.find_person(player, name)
    if not p:
        p = builder.find_item(player, name)
        if not p:
            text_game_maker._wrap_print("Don't know how to %s %s" % (word, name))
            return

    text_game_maker.game_print('You speak to %s.' % p.prep)
    if p.alive:
        response = p.on_speak(player)
        if response:
            p.say(response)
    else:
        text_game_maker.game_print('%s says nothing.' % p.prep)

def _do_equip(player, word, item_name):
    if not item_name or item_name == "":
        text_game_maker._wrap_print("Which inventory item do you want to %s?"
            % word)
        return

    item = builder.find_inventory_item(player, item_name)
    if not item:
        text_game_maker._wrap_print("No %s in your inventory to %s"
            % (item_name, word))
        return

    if item in player.inventory['equipped']:
        text_game_maker.game_print("%s is already equipped." % item.name)
        return

    # Move any already-equipped items back to unequipped
    if player.inventory['equipped']:
        equipped = player.inventory['equipped'][0]
        equipped.move(player.inventory['unequipped'])

    item.move(player.inventory['equipped'])
    text_game_maker.game_print("Equipped %s." % item.name)

def _do_unequip(player, word, fields):
    if not player.inventory['equipped']:
        text_game_maker.game_print('Nothing is currently equipped.')
        return

    equipped = player.inventory['equipped'][0]
    equipped.move(player.inventory['unequipped'])
    text_game_maker.game_print('%s unequipped' % equipped.name)

def _do_loot(player, word, name):
    if not name or name == "":
        text_game_maker._wrap_print("Who do you want to %s?" % word)
        return

    p = builder.find_person(player, name)
    if not p:
        p = builder.find_item(player, name)
        if not p:
            text_game_maker.game_print("Not sure how to %s %s" % (word, name))
            return

    if p.alive:
        text_game_maker.game_print("You are dead.")
        text_game_maker.game_print("You were caught trying to %s %s."
            % (word, p.name))
        text_game_maker.game_print("%s didn't like this, and killed you.\n"
            % p.name)
        sys.exit()
    else:
        player._loot(word, p)

def _do_inspect(player, word, item):
    if item == '':
        _do_look(player, word, item)
        return

    target = builder.find_item(player, item)
    if not target:
        target = builder.find_person(player, item)
        if not target:
            text_game_maker._wrap_print("No %s available to %s" % (item, word))
            return

    text_game_maker.game_print(target.on_look(player))

def _do_look(player, word, item):
    if item != '':
        _do_inspect(player, word, item)
        return

    text_game_maker.game_print(player.current_state())

def build_parser():
    ret = CommandParser()

    commands = [
        [EQUIP_WORDS, _do_equip, "equip an item from your inventory",
            "%s <item>"],

        [TAKE_WORDS, _do_take, "add an item to your inventory", "%s <item>"],

        [DROP_WORDS, _do_drop, "drop an item from your inventory", "%s <item>"],

        [SPEAK_WORDS, _do_speak, "speak with a person by name", "%s <person>"],

        [UNEQUIP_WORDS, _do_unequip, "unequip your equipped item "
            "(if any)", "%s <item>"],

        [EAT_WORDS, _do_eat, "eat something", "%s <item>"],

        [LOOT_WORDS, _do_loot, "attempt to loot a person by name",
            "%s <person>"],

        [INSPECT_WORDS, _do_inspect, "examine an item in more "
            "detail", "%s <item>"],

        [LOOK_WORDS, _do_look, "examine your current surroundings"]
    ]

    for arglist in commands:
        ret.add_command(*arglist)

    return ret

