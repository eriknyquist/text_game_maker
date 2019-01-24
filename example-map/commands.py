import sys

import text_game_maker

from text_game_maker.audio import audio
from text_game_maker.utils import utils
from text_game_maker.messages import messages
from text_game_maker.builder import map_builder as builder
from text_game_maker.game_objects.items import Lighter

EAT_WORDS = [
    'eat', 'scoff', 'swallow', 'ingest', 'consume'
]

SUICIDE_WORDS = [
    "kill self", "kill myself", "suicide", "kill player", "die",
    "goodbye cruel world"
]

UNLOCK_WORDS = ['unlock']

EVERYTHING_WORDS = [
    'everything', 'all'
]

TAKE_WORDS = [
    'take', 'pick up', 'steal', 'acquire', 'grab', 'get', 'snatch', 'dock'
]

BURN_WORDS = [
    'burn', 'light', 'torch'
]

READ_WORDS = [
    'read'
]

PUT_WORDS = [
    'put', 'place'
]

INSIDE_WORDS = [
    'in', 'inside', 'into'
]

DROP_WORDS = [
    'drop', 'throw away', 'discard', 'chuck', 'ditch', 'delete', 'undock'
]

EQUIP_WORDS = [
    'equip', 'use', 'whip out', 'brandish', 'take out', 'get out'
]

UNEQUIP_WORDS = [
    'unequip', 'stop using', 'stow'
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

look_under_adjs = [
    'under', 'underneath', 'beneath'
]

LOOK_UNDER_WORDS = []
for x in LOOK_WORDS:
    for y in look_under_adjs:
        LOOK_UNDER_WORDS.append('%s %s' % (x, y))

LOOK_INSIDE_WORDS = [
    'look in', 'look inside', 'look into', 'peep in' , 'peep inside',
    'peep into'
]

LOOT_WORDS = [
    'loot', 'search', 'rob', 'pickpocket'
]

INNOCUOUS = [
    "dance", "do a dance", "do a little dance", "do the worm", "do a backflip",
    "do a flip", "do a push up", "do a pushup", "do pushups", "do push ups",
    "breakdance", "jog on the spot", "meditate", "cough up a hairball",
    "recite poetry", "take a nap"
]

PICK_NOSE_WORDS = [
    "pick nose", "pick my nose", "pick own nose"
]

SLEEP_WORDS = [
    "take a nap", "sleep", "have a nap", "nap", "take a sleep", "have a sleep"
]

ALLSTAR_SONG = [
    "smashmouth"
]

def _split_word(string, word):
    inlist = string.split()
    for i in range(len(inlist)):
        if inlist[i] == word:
            return ' '.join(inlist[:i]), ' '.join(inlist[i + 1:])

    return None, None

def _do_allstar_song(player, word, remaining):
    utils.save_sound(audio.ALLSTAR_SOUND)

def _do_innocuous(player, word, remaining):
    utils.game_print(messages.strange_action_message(word))

def _do_eat(player, word, item_name):
    if not item_name or item_name == "":
        utils._wrap_print("What do you want to %s?" % word)
        return

    fields = utils.english_to_list(item_name)
    if len(fields) > 1:
        utils._wrap_print("Whoa there! how about eating one thing at "
            "a time? And don't talk with your mouth full.")
        return

    item = builder.find_any_item(player, item_name)
    if not item:
        item = builder.find_person(player, item_name)
        if not item:
            utils._wrap_print(messages.no_item_message(item_name))
            utils.save_sound(audio.FAILURE_SOUND)
            return

    item.on_eat(player, word)

def _do_read(player, word, item_name):
    if not item_name or item_name == "":
        utils._wrap_print("What do you want to %s?" % word)
        return

    fields = utils.english_to_list(item_name)
    if len(fields) > 1:
        utils._wrap_print("Really, now. You can only read *one* thing"
            " at a time.")
        return

    item = builder.find_any_item(player, item_name)
    if item:
        item.on_read(player)
        return

    if builder.is_location(player, item_name):
        utils._wrap_print(messages.nonsensical_action_message(
            '%s the %s' % (word, item_name)))
    else:
        utils._wrap_print(messages.no_item_message(item_name))

    utils.save_sound(audio.FAILURE_SOUND)

def _do_unlock(player, word, remaining):
    if not remaining or remaining == "":
        utils._wrap_print("What do you want to %s?" % word)
        return

    door_name, item_name = _split_word(remaining, 'with')
    if door_name is None:
        utils._wrap_print("What do you want to %s %s with?" % (word, remaining))
        return

    door = None
    for tile in player.current.iterate_directions():
        if tile and tile.is_door() and (door_name in tile.short_name):
            door = tile
            break

    if door is None:
        utils._wrap_print(messages.no_item_message(door_name))
        return

    item = builder.find_any_item(player, item_name)
    if not item:
        utils._wrap_print(messages.no_item_message(item_name))
        return

    door.on_unlock(player, item)

def _do_burn(player, word, item_name):
    lighter = builder.find_inventory_item_class(player, Lighter)
    if lighter is None:
        utils._wrap_print("You can't %s anything without a lighter."
            % word)
        return

    if not item_name or item_name == "":
        utils._wrap_print("What do you want to %s?" % word)
        return

    fields = utils.english_to_list(item_name)
    if len(fields) > 1:
        utils._wrap_print("Slow down, pyromaniac. We burn things one "
            "at a time around here.")
        return

    item = builder.find_any_item(player, item_name)
    if item:
        item.on_burn(player)
        return

    if builder.is_location(player, item_name):
        utils._wrap_print(messages.burn_noncombustible_message(item_name))
    else:
        utils._wrap_print(messages.no_item_message(item_name))

def _put(item, dest_item, location_name, location):
    if item is dest_item:
        utils.game_print("How can you put the %s inside itself?"
            % (item.name))
        return False

    if item.size >= dest_item.size:
        utils.game_print(messages.container_too_small_message(
                item.name, dest_item.name))
        return False

    item.move(location)
    return True

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
        for sep in INSIDE_WORDS:
            item_name, dest_name = _split_word(remaining, sep)
            if item_name:
                break

        if item_name is None:
            utils._wrap_print(messages.dontknow_message('%s %s'
                % (word, remaining)))
            return

        dest_item = builder.find_any_item(player, dest_name)
        if not dest_item:
            utils._wrap_print(messages.dontknow_message('%s %s'
                % (word, remaining)))
            return

        if not dest_item.is_container:
            utils._wrap_print("%s cannot contain other items." % dest_item.name)
            return

        location = dest_item.items
        location_name = 'in the %s' % dest_item.name

    items = []
    names = []

    fields = utils.english_to_list(item_name)
    if (len(fields) == 1) and (item_name in EVERYTHING_WORDS):
        items = builder.get_all_items(player, except_item=dest_item)
        if not items:
            utils._wrap_print("Nothing to %s." % word)
            utils.save_sound(audio.FAILURE_SOUND)
            return

    elif fields:
        for name in fields:
            item = builder.find_any_item(player, name)
            if not item:
                utils._wrap_print(messages.no_item_message(name))
                utils.save_sound(audio.FAILURE_SOUND)
                return

            items.append(item)

    if not items:
        utils._wrap_print(messages.no_item_message(item_name))
        utils.save_sound(audio.FAILURE_SOUND)
        return

    for item in items:
        if not dest_item.add_item(item):
            return

    real_names = [x.name for x in items]
    utils.game_print("You %s the %s %s"
            % (word, utils.list_to_english(real_names), location_name))

def _do_look_inside(player, word, remaining):
    if not remaining or remaining == "":
        utils._wrap_print("What do you want to %s?" % word)
        return

    item = builder.find_any_item(player, remaining)
    if not item:
        utils._wrap_print(messages.no_item_message(remaining))
        return

    if item.is_container and item.items:
        contains = utils.list_to_english(
            [str(x) for x in item.items])
    else:
        contains = "nothing"

    utils.game_print("%s contains %s." % (item.name, contains))

def _take(player, item):
    # If on_take callback returns false, abort adding this item
    if not item.on_take(player):
        return False

    if not player.inventory:
        utils._wrap_print("No bag to hold items")
        utils.save_sound(audio.FAILURE_SOUND)
        return False

    return item.add_to_player_inventory(player)

def _do_take(player, word, remaining):
    item_name = None
    locations = None
    items = []

    if not remaining or remaining == "":
        utils._wrap_print("What do you want to %s?" % word)
        return

    item_name, dest_name = _split_word(remaining, 'from')
    if dest_name is None:
        item_name = remaining
        locations = player.current.items.values()
    else:
        dest_item = builder.find_any_item(player, dest_name)
        if not dest_item:
            utils._wrap_print(messages.dontknow_message('%s %s'
                % (word, remaining)))
            return

        locations = [dest_item.items]

    if item_name in EVERYTHING_WORDS:
        items = builder.get_all_items(player, locations)
    else:
        names = []
        fields = utils.english_to_list(item_name)
        if len(fields) > 1:
            names = fields
        else:
            names = [item_name]

        for name in names:
            item = builder.find_item(player, name, locations)
            if not item:
                utils._wrap_print(messages.no_item_message(name))
                utils.save_sound(audio.FAILURE_SOUND)
                return

            items.append(item)

    if not items:
        utils._wrap_print("Nothing to %s" % word)
        utils.save_sound(audio.FAILURE_SOUND)
        return

    names = []
    for item in items:
        if item:
            if not _take(player, item):
                return

            names.append(item.name)

    msg = utils.list_to_english(names)
    utils.game_print('%s added to inventory' % msg)
    return

def _drop(player, item):
    item.location = "on the ground"
    player.current.add_item(item)
    return True

def _do_drop(player, word, item_name):
    if not player.inventory:
        utils._wrap_print("No bag to %s items from." % word)
        return

    if not item_name or item_name == "":
        utils._wrap_print("What do you want to drop?")
        return

    item_names = []
    if item_name in EVERYTHING_WORDS:
        item_names = [x.name for x in player.inventory.items]
    else:
        fields = utils.english_to_list(item_name)
        if len(fields) > 1:
            item_names = fields
        else:
            item_names = [item_name]

    if not item_names:
        utils._wrap_print("Nothing to %s." % word)
        utils.save_sound(audio.FAILURE_SOUND)
        return

    items = []
    for name in item_names:
        item = builder.find_inventory_item(player, name)
        if not item:
            utils._wrap_print("No %s in your inventory to %s."
                % (name, word))
            return

        items.append(item)

    for item in items:
        if not _drop(player, item):
            return

    utils.game_print("Dropped %s."
        % utils.list_to_english([x.name for x in items]))

def _do_speak(player, word, name):
    if not name or name == "":
        utils._wrap_print("Who do you want to speak to?")
        return

    p = builder.find_person(player, name)
    if not p:
        p = builder.find_item(player, name)
        if not p:
            utils._wrap_print("Don't know how to %s %s" % (word, name))
            utils.save_sound(audio.FAILURE_SOUND)
            return

    utils.game_print('You speak to %s.' % p.prep)
    if p.alive:
        response = p.on_speak(player)
        if response:
            p.say(response)
    else:
        utils.game_print('%s says nothing.' % p.prep)

def _do_equip(player, word, item_name):
    if not item_name or item_name == "":
        utils._wrap_print("Which inventory item do you want to %s?"
            % word)
        return

    item = builder.find_inventory_item(player, item_name)
    if not item:
        utils._wrap_print("No %s in your inventory to %s"
            % (item_name, word))
        utils.save_sound(audio.FAILURE_SOUND)
        return

    if item is player.equipped:
        utils.game_print("%s is already equipped." % item.name)
        return

    # Move any already-equipped items back to unequipped
    if player.equipped:
        player.equipped.move(player.inventory.items)

    player.equipped = item
    player.equipped.delete()
    utils.game_print("Equipped %s." % item.name)

def _do_unequip(player, word, fields):
    if not player.equipped:
        utils.game_print('Nothing is currently equipped.')
        return

    player.equipped.move(player.inventory.items)
    utils.game_print('%s unequipped' % player.equipped.name)
    player.equipped = None

def _do_loot(player, word, name):
    if not name or name == "":
        utils._wrap_print("Who do you want to %s?" % word)
        return

    p = builder.find_person(player, name)
    if not p:
        p = builder.find_item(player, name)
        if not p:
            utils.game_print("Not sure how to %s %s" % (word, name))
            utils.save_sound(audio.FAILURE_SOUND)
            return

    if p.alive:
        utils.game_print("You are dead.")
        utils.game_print("You were caught trying to %s %s."
            % (word, p.name))
        utils.game_print("%s didn't like this, and killed you.\n"
            % p.name)
        player.death()
    else:
        player._loot(word, p)

def _do_suicide(player, word, remaining):
    utils.game_print(messages.suicide_message())
    player.death()

def _do_inspect(player, word, item):
    if item == '':
        _do_look(player, word, item)
        return

    target = builder.find_any_item(player, item)
    if not target:
        target = builder.find_person(player, item)

    if target:
        target.on_look(player)
        return

    tile = builder.find_tile(player, item)
    if tile:
        utils.game_print("%s." % tile.name)
    else:
        utils._wrap_print(
            messages.dontknow_message("%s %s" % (word, item)))

        utils.save_sound(audio.FAILURE_SOUND)


def _do_look(player, word, item):
    if item != '':
        _do_inspect(player, word, item)
        return

    utils.game_print(player.current_state())

def _do_look_under(player, word, item):
    if item == '':
        utils._wrap_print("What do you want to %s?" % word)
        utils.save_sound(audio.FAILURE_SOUND)
        return

    target = builder.find_any_item(player, item)
    if target:
        target.on_look_under(player)
        return

    utils._wrap_print(messages.dontknow_message("%s %s"
        % (word, item)))
    utils.save_sound(audio.FAILURE_SOUND)

def _do_picknose(player, word, remaining):
    utils.game_print(messages.gross_action_message("pick your nose"))

def _do_sleep(player, word, remaining):
    utils.game_print(messages.sleep_message(word))

def build_parser(parser):
    commands = [
        [EQUIP_WORDS, _do_equip, "equip an item from your inventory",
            "%s <item>"],

        [UNLOCK_WORDS, _do_unlock, "unlock a door with a key or lockpick",
            "%s <door> with <item>"],

        [BURN_WORDS, _do_burn, "burn an item", "%s <item>"],

        [READ_WORDS, _do_read, "read an item", "%s <item>"],

        [SUICIDE_WORDS, _do_suicide, "commit suicide", "%s"],

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

        [LOOK_UNDER_WORDS, _do_look_under, "look under an item", "%s <item>"],

        [LOOK_INSIDE_WORDS, _do_look_inside,
            "examine the contents of an object"],

        [LOOK_WORDS, _do_look, "examine your current surroundings"],

        [INNOCUOUS, _do_innocuous],

        [PICK_NOSE_WORDS, _do_picknose],

        [SLEEP_WORDS, _do_sleep],

        [ALLSTAR_SONG, _do_allstar_song]
    ]

    for arglist in commands:
        parser.add_command(*arglist)

    return parser

