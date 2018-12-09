import sys

import text_game_maker

from text_game_maker import audio, messages
from text_game_maker import map_builder as builder
from text_game_maker.parser import CommandParser

EAT_WORDS = [
    'eat', 'scoff', 'swallow', 'ingest', 'consume'
]

UNLOCK_WORDS = ['unlock']

TAKE_WORDS = [
    'take', 'pick up', 'steal', 'acquire', 'grab', 'get', 'snatch', 'dock'
]

PUT_WORDS = [
    'put', 'place'
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

LOOK_INSIDE_WORDS = [
    'look in', 'look inside', 'peep in' , 'peep inside',
]

LOOT_WORDS = [
    'loot', 'search', 'rob', 'pickpocket'
]

def _dontknow(msg):
    text_game_maker._wrap_print("Don't know how to %s" % msg)
    text_game_maker.save_sound(audio.FAILURE_SOUND)

def _split_word(string, word):
    inlist = string.split()
    for i in range(len(inlist)):
        if inlist[i] == word:
            return ' '.join(inlist[:i]), ' '.join(inlist[i + 1:])

    return None, None

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
                text_game_maker._wrap_print(messages.no_item_message(item_name))
                text_game_maker.save_sound(audio.FAILURE_SOUND)
                return

    msg = item.on_eat(player, word)
    if msg:
        text_game_maker.game_print(msg)

def _do_unlock(player, word, remaining):
    if not remaining or remaining == "":
        text_game_maker._wrap_print("What do you want to %s?" % word)
        return

    door_name, item_name = _split_word(remaining, 'with')
    if door_name is None:
        text_game_maker._wrap_print("What do you want to %s %s with?" % (word, remaining))
        return

    door = None
    for tile in player.current.iterate_directions():
        if tile and tile.is_door() and (door_name in tile.short_name):
            door = tile
            break

    if door is None:
        text_game_maker._wrap_print(messages.no_item_message(door_name))
        return
     
    item = builder.find_inventory_item(player, item_name)
    if not item:
        item = builder.find_item(player, item_name)
        if not item:
            text_game_maker._wrap_print(messages.no_item_message(item_name))
            return

    door.on_unlock(player, item)

def _do_put(player, word, remaining):
    location_name = ""
    location = None
    item_name = None
    dest_item = None

    for loc in player.current.items:
        if remaining.endswith(loc):
            location = player.current.items[loc]
            location_name = loc
            item_name = remaining[:-len(loc)].strip()
            break

    if location is None:
        item_name, dest_name = _split_word(remaining, 'in')
        if item_name is None:
            item_name, dest_name = _split_word(remaining, 'inside')
            if item_name is None:
                _dontknow("%s %s" % (word, remaining))
                return

        dest_item = builder.find_inventory_item(player, dest_name)
        if not dest_item:
            dest_item = builder.find_item(player, dest_name)
            if not dest_item:
                _dontknow("%s %s" % (word, remaining))
                return

        if not dest_item.is_container():
            text_game_maker._wrap_print("Can't %s %s" % (word, remaining))
            return

        location = dest_item.items
        location_name = 'in the %s' % dest_item.name

    item = builder.find_inventory_item(player, item_name)
    if not item:
        item = builder.find_item(player, item_name)
        if not item:
            text_game_maker._wrap_print(messages.no_item_message(item_name))
            text_game_maker.save_sound(audio.FAILURE_SOUND)
            return

    if item is dest_item:
        text_game_maker.game_print("How can you %s the %s inside itself?"
            % (word, item.name))
        return

    if item.size > dest_item.max_item_size:
        text_game_maker.game_print(messages.container_too_small_message(
                item.name, dest_item.name))
        return

    text_game_maker.game_print("You %s the %s %s"
            % (word, item.name, location_name))

    item.move(location)

def _do_look_inside(player, word, remaining):
    if not remaining or remaining == "":
        text_game_maker._wrap_print("What do you want to %s?" % word)
        return

    item = builder.find_inventory_item(player, remaining)
    if not item:
        item = builder.find_item(player, remaining)
        if not item:
            text_game_maker._wrap_print(messages.no_item_message(remaining))
            return

    if item.is_container() and item.items:
        contains = text_game_maker.list_to_english(
            [str(x) for x in item.items])
    else:
        contains = "nothing"

    text_game_maker.game_print("%s contains %s." % (item.name, contains))

def _take(player, item):
    # If on_take callback returns false, abort adding this item
    if not item.on_take(player):
        return False

    if not player.inventory:
        text_game_maker._wrap_print("No bag to hold items")
        text_game_maker.save_sound(audio.FAILURE_SOUND)
        return False

    return item.add_to_player_inventory(player)

def _do_take(player, word, remaining):
    item_name = None
    locations = None

    if not remaining or remaining == "":
        text_game_maker._wrap_print("What do you want to %s?" % word)
        return

    item_name, dest_name = _split_word(remaining, 'from')
    if dest_name is None:
        item_name = remaining
        locations = player.current.items.values()
    else:
        dest_item = builder.find_inventory_item(player, dest_name)
        if not dest_item:
            dest_item = builder.find_item(player, dest_name)
            if not dest_item:
                _dontknow("%s %s" % (word, remaining))
                return

        locations = [dest_item.items]

    if '*' in item_name:
        added = []
        item = ' '

        while item:
            item = builder.find_item_wildcard(player, item_name, locations)
            if item:
                if not _take(player, item):
                    return

                added.append(item.name)

        if not added:
            text_game_maker._wrap_print("Nothing to %s" % word)
            text_game_maker.save_sound(audio.FAILURE_SOUND)
            return

        msg = text_game_maker.list_to_english(added)
    else:
        item = builder.find_item(player, item_name, locations)
        if not item:
            text_game_maker._wrap_print(messages.no_item_message(item_name))
            text_game_maker.save_sound(audio.FAILURE_SOUND)
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
    if not player.inventory:
        text_game_maker._wrap_print("No bag to %s items from." % word)
        return

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
            text_game_maker._wrap_print("Nothing to %s." % word)
            text_game_maker.save_sound(audio.FAILURE_SOUND)
            return

        msg = text_game_maker.list_to_english(added)
    else:
        item = builder.find_inventory_item(player, item_name)
        if not item:
            text_game_maker._wrap_print("No %s in your inventory to %s"
                % (item_name, word))
            text_game_maker.save_sound(audio.FAILURE_SOUND)
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
            text_game_maker.save_sound(audio.FAILURE_SOUND)
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
        text_game_maker.save_sound(audio.FAILURE_SOUND)
        return

    if item is player.equipped:
        text_game_maker.game_print("%s is already equipped." % item.name)
        return

    # Move any already-equipped items back to unequipped
    if player.equipped:
        player.equipped.move(player.inventory.items)

    player.equipped = item
    player.equipped.delete()
    text_game_maker.game_print("Equipped %s." % item.name)

def _do_unequip(player, word, fields):
    if not player.equipped:
        text_game_maker.game_print('Nothing is currently equipped.')
        return

    player.equipped.move(player.inventory.items)
    text_game_maker.game_print('%s unequipped' % player.equipped.name)
    player.equipped = None

def _do_loot(player, word, name):
    if not name or name == "":
        text_game_maker._wrap_print("Who do you want to %s?" % word)
        return

    p = builder.find_person(player, name)
    if not p:
        p = builder.find_item(player, name)
        if not p:
            text_game_maker.game_print("Not sure how to %s %s" % (word, name))
            text_game_maker.save_sound(audio.FAILURE_SOUND)
            return

    if p.alive:
        text_game_maker.game_print("You are dead.")
        text_game_maker.game_print("You were caught trying to %s %s."
            % (word, p.name))
        text_game_maker.game_print("%s didn't like this, and killed you.\n"
            % p.name)
        player.death()
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
            text_game_maker.save_sound(audio.FAILURE_SOUND)
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

        [UNLOCK_WORDS, _do_unlock, "unlock a door with a key or lockpick",
            "%s <door> with <item>"],

        [TAKE_WORDS, _do_take, "add an item to your inventory", "%s <item>"],

        [PUT_WORDS, _do_put, "put an item somewhere", "%s <item> <location>"],

        [DROP_WORDS, _do_drop, "drop an item from your inventory", "%s <item>"],

        [SPEAK_WORDS, _do_speak, "speak with a person by name", "%s <person>"],

        [UNEQUIP_WORDS, _do_unequip, "unequip your equipped item "
            "(if any)", "%s <item>"],

        [EAT_WORDS, _do_eat, "eat something", "%s <item>"],

        [LOOT_WORDS, _do_loot, "attempt to loot a person by name",
            "%s <person>"],

        [INSPECT_WORDS, _do_inspect, "examine an item in more "
            "detail", "%s <item>"],

        [LOOK_INSIDE_WORDS, _do_look_inside,
            "examine the contents of an object"],

        [LOOK_WORDS, _do_look, "examine your current surroundings"]
    ]

    for arglist in commands:
        ret.add_command(*arglist)

    return ret

