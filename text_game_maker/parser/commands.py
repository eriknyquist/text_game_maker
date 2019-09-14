import sys

import text_game_maker

from text_game_maker.audio import audio
from text_game_maker.utils import utils
from text_game_maker.messages import messages
from text_game_maker.game_objects.items import FlameSource

MAP_WORDS = [
    'map', 'show map', 'display map', 'world map'
]

SELF_WORDS = [
    'self', 'me', 'myself'
]

SET_NAME_WORDS = [
    "change name", "change my name", "change player name", "set name",
    "set my name", "set player name"
]

RESET_WORDS = [
    'reset', 'restart', 'start'
]

ATTACK_WORDS = [
    "attack", "fight", "hurt", "injure", "strike"
]

EAT_WORDS = [
    'eat', 'scoff', 'swallow', 'ingest', 'consume'
]

SMELL_WORDS = [
    'smell', 'sniff'
]

GROUND_WORDS = [
    'ground', 'floor'
]

TASTE_WORDS = [
    'taste', 'lick'
]

SUICIDE_WORDS = [
    "kill self", "kill myself", "suicide", "kill player", "die",
    "goodbye cruel world"
]

OPEN_WORDS = ['open']

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
    'look around', 'look', 'peep', 'peek', 'show', 'viddy'
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

def _no_item_message(player, item_name):
    if player.can_see():
        utils._wrap_print(messages.no_item_message(item_name))
    else:
        utils._wrap_print(messages.dark_search_message())

def _nothing_message(player, word):
    if player.can_see():
        utils._wrap_print("Nothing to %s" % word)
    else:
        utils._wrap_print(messages.dark_search_message())

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
    return True

def _do_eat(player, word, item_name):
    if not item_name or item_name == "":
        utils._wrap_print("What do you want to %s?" % word)
        return False

    fields = utils.english_to_list(item_name)
    if len(fields) > 1:
        utils._wrap_print("Whoa there! how about eating one thing at "
            "a time? And don't talk with your mouth full.")
        return False

    item = utils.find_any_item(player, item_name)
    if not item:
        item = utils.find_person(player, item_name)
        if not item:
            if utils.is_location(player, item_name):
                utils.game_print(messages.nonsensical_action_message(
                    '%s %s' % (word, item_name)))
            else:
                _no_item_message(player, item_name)

            return False

    item.on_eat(player, word)
    return True

def _do_read(player, word, item_name):
    if not player.can_see():
        utils._wrap_print(messages.dark_search_message())
        return False

    if not item_name or item_name == "":
        utils._wrap_print("What do you want to %s?" % word)
        return False

    fields = utils.english_to_list(item_name)
    if len(fields) > 1:
        utils._wrap_print("Really, now. You can only read *one* thing"
            " at a time.")
        return False

    item = utils.find_any_item(player, item_name)
    if item:
        item.on_read(player)
        return True

    if not player.can_see():
        utils._wrap_print(messages.dark_search_message())
        return False

    if utils.is_location(player, item_name):
        utils._wrap_print(messages.nonsensical_action_message(
            '%s the %s' % (word, item_name)))
    else:
        utils._wrap_print(messages.no_item_message(item_name))

    return False

def _look_for_door(player, item_name):
    for tile in player.current.iterate_directions():
        if tile and tile.is_door() and tile.matches_name(item_name):
            return tile

    return None

def _do_unlock(player, word, item_name):
    if not player.can_see():
        utils._wrap_print(messages.dark_search_message())
        return False

    if not item_name or item_name == "":
        utils._wrap_print("What do you want to %s?" % word)
        return False

    doorobj = _look_for_door(player, item_name)
    if not doorobj:
        utils._wrap_print("No %s to %s." % (item_name, word))

    doorobj.on_open(player)
    return True

def _do_open(player, word, item_name):
    if not player.can_see():
        utils._wrap_print(messages.dark_search_message())
        return False

    if not item_name or item_name == "":
        utils._wrap_print("What do you want to %s?" % word)
        return False

    item = utils.find_any_item(player, item_name)
    if not item:
        item = _look_for_door(player, item_name)
        if not item:
            utils._wrap_print(messages.no_item_message(item_name))
            return False

    item.on_open(player)
    return True

def _do_burn(player, word, item_name):
    fire = utils.find_inventory_item_class(player, FlameSource)
    if fire is None:
        utils._wrap_print("You can't %s anything without a flame source."
            % word)
        return True

    if not player.can_see():
        utils._wrap_print(messages.dark_search_message())
        return True

    if not item_name or item_name == "":
        utils._wrap_print("What do you want to %s?" % word)
        return False

    fields = utils.english_to_list(item_name)
    if len(fields) > 1:
        utils._wrap_print("Slow down, pyromaniac. We burn things one "
            "at a time around here.")
        return False

    if fire.get_fuel() <= 0.0:
        utils._wrap_print(fire.spent_use_message)
        return True

    item = utils.find_any_item(player, item_name)
    if item:
        item.on_burn(player)
        fire.decrement_fuel()
        return True

    if utils.is_location(player, item_name):
        utils._wrap_print(messages.burn_noncombustible_message(item_name))
        fire.decrement_fuel()
    else:
        _no_item_message(player, item_name)
        return False

    return True

def _do_set_name(player, word, remaining):
    player.read_player_name_and_set()

def _do_smell(player, word, item_name):
    if not item_name or item_name == "":
        player.current.on_smell()
        return True

    if item_name in GROUND_WORDS:
        player.current.on_smell_ground()
        return True

    if item_name in SELF_WORDS:
        player.on_smell()
        return True

    fields = utils.english_to_list(item_name.strip())
    if len(fields) > 1:
        utils._wrap_print("Slow down, big-nose. You can only %s one thing at a "
            "time." % word)
        return False

    item = utils.find_any_item(player, item_name)
    if item:
        item.on_smell(player)
        return True

    if utils.is_location(player, item_name):
        utils._wrap_print("%s doesn't smell like anything in particular."
            % item_name)
        return True

    _no_item_message(player, item_name)
    return False

def _do_taste(player, word, item_name):
    if not item_name or item_name == "":
        utils._wrap_print("What do you want to %s?" % word)
        return False

    if item_name in GROUND_WORDS:
        player.current.on_taste_ground()
        return True

    if item_name in SELF_WORDS:
        player.on_taste()
        return True

    fields = utils.english_to_list(item_name)
    if len(fields) > 1:
        utils._wrap_print("Slow down, greedy. You can only %s one thing at a "
            "time." % word)
        return False

    item = utils.find_any_item(player, item_name)
    if item:
        item.on_taste(player)
        return True

    if utils.is_location(player, item_name):
        utils._wrap_print("%s doesn't taste like anything in particular."
            % item_name)
        return True

    _no_item_message(player, item_name)

    return False

def _put(item, dest_item, location_name, location):
    if item is dest_item:
        utils.game_print("How can you put the %s inside itself?"
            % (item.name))
        return False

    if item.size >= dest_item.size:
        utils.game_print(messages.container_too_small_message(
                item.prep, dest_item.prep))
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
            return False

        dest_item = utils.find_any_item(player, dest_name)
        if not dest_item:
            _no_item_message(player, dest_name)
            return False

        if not dest_item.is_container:
            utils._wrap_print("%s cannot contain other items." % dest_item.name)
            return False

        location = dest_item.items
        location_name = 'in the %s' % dest_item.name

    items = []
    names = []

    fields = utils.english_to_list(item_name)
    if (len(fields) == 1) and (item_name in EVERYTHING_WORDS):
        items = utils.get_all_items(player, except_item=dest_item)
        if not items:
            utils._wrap_print("Nothing to %s." % word)
            return False

    elif fields:
        for name in fields:
            item = utils.find_any_item(player, name)
            if not item:
                _no_item_message(player, name)
                return False

            items.append(item)

    if not items:
        _no_item_message(player, item_name)
        return False

    real_names = []
    for item in items:
        if not dest_item.add_item(item):
            if len(real_names) > 0:
                break

            return False

        real_names.append(item.name)

    utils.game_print("You %s the %s %s."
            % (word, utils.list_to_english(real_names), location_name))
    return True

def _do_show_map(player, word, remaining):
    utils.printfunc(utils.draw_map_of_nearby_tiles(player))

def _do_look_inside(player, word, remaining):
    if not remaining or remaining == "":
        utils._wrap_print("What do you want to %s?" % word)
        return False

    item = utils.find_any_item(player, remaining)
    if not item:
        _no_item_message(player, remaining)
        return False

    if not item.is_container:
        utils.game_print("%s contains nothing." % item.name)
        return True

    utils.printfunc('\n' + utils.container_listing(item, bottom_border=True))
    return True

def _take(player, item):
    # If on_take callback returns false, abort adding this item
    if not item.on_take(player):
        return False

    return item.add_to_player_inventory(player)

def _do_take(player, word, remaining):
    item_name = None
    locations = None
    ignoredark = False
    items = []

    if not remaining or remaining == "":
        utils._wrap_print("What do you want to %s?" % word)
        return False

    item_name, dest_name = _split_word(remaining, 'from')
    if dest_name is None:
        item_name = remaining
        locations = player.current.items.values()
    else:
        dest_item = utils.find_any_item(player, dest_name)
        if not dest_item:
            _no_item_message(player, dest_name)
            return False

        if player.has_item(dest_item):
            ignoredark = True

        locations = [dest_item.items]

    if item_name in EVERYTHING_WORDS:
        items = utils.get_all_items(player, locations)
    else:
        names = []
        fields = utils.english_to_list(item_name)
        if len(fields) > 1:
            names = fields
        else:
            names = [item_name]

        for name in names:
            item = utils.find_item(player, name, locations, ignoredark)
            if not item:
                _no_item_message(player, name)
                return False

            items.append(item)

    if not items:
        _nothing_message(player, word)
        return False

    names = []
    for item in items:
        if not item:
            continue

        added_item = _take(player, item)
        if not added_item:
            if len(names) > 0:
                break

            return False

        added_item.prep = "your " + item.name
        names.append(item.name)

    utils.game_print('%s added to inventory.' % utils.list_to_english(names))
    return True

def _drop(player, items):
    equipped = None

    for item in items:
        if item and (item is player.equipped):
            equipped = player.equipped
            player.equipped = None

        item.location = "on the ground"
        dropped = player.current.add_item(item)
        dropped.prep = "the " + dropped.name

    utils.game_print("Dropped %s."
        % utils.list_to_english([x.name for x in items]))

    if equipped:
        equipped.on_unequip(player)

    return True

def _do_drop(player, word, item_name):
    if not item_name or item_name == "":
        utils._wrap_print("What do you want to drop?")
        return False

    item_names = []
    if item_name in EVERYTHING_WORDS:
        item_names = [x.name for x in player.pockets.items]
        if player.inventory:
            item_names.extend([x.name for x in player.inventory.items])
    else:
        fields = utils.english_to_list(item_name)
        if len(fields) > 1:
            item_names = fields
        else:
            item_names = [item_name]

    if not item_names:
        utils._wrap_print("Nothing to %s." % word)
        return False

    items = []
    for name in item_names:
        item = utils.find_inventory_item(player, name)
        if not item:
            utils._wrap_print("No %s in your inventory to %s."
                % (name, word))
            return False

        items.append(item)

    _drop(player, items)
    return True

def _do_speak(player, word, name):
    if not name or name == "":
        utils._wrap_print("Who do you want to speak to?")
        return False

    p = utils.find_person(player, name)
    if not p:
        p = utils.find_item(player, name)
        if not p:
            utils._wrap_print("Don't know how to %s %s." % (word, name))
            return False

    utils.game_print('You speak to %s.' % p.prep)
    p.on_speak(player)
    return True

def _do_equip(player, word, item_name):
    if not item_name or item_name == "":
        utils._wrap_print("Which inventory item do you want to %s?"
            % word)
        return False

    item = utils.find_inventory_item(player, item_name)
    if not item:
        utils._wrap_print("No %s in your inventory to %s."
            % (item_name, word))
        return False

    if item is player.equipped:
        utils.game_print("%s is already equipped." % item.name)
        return False

    # Move any already-equipped items back to unequipped
    if player.equipped:
        player.equipped.move(player.inventory.items)

    item.on_equip(player)
    player.equipped = item
    player.equipped.delete()
    return True

def _do_unequip(player, word, fields):
    if not player.equipped:
        utils.game_print('Nothing is currently equipped.')
        return False

    if player.inventory_space() == 0:
        _drop(player, [player.equipped])
        return False

    utils.game_print("Unequipped %s." % player.equipped.name)
    player.equipped.add_to_player_inventory(player)
    item = player.equipped
    player.equipped = None
    item.on_unequip(player)
    return True

def _do_loot(player, word, name):
    if not name or name == "":
        utils._wrap_print("Who do you want to %s?" % word)
        return False

    p = utils.find_person(player, name)
    if not p:
        p = utils.find_item(player, name)
        if not p:
            utils.game_print("Not sure how to %s %s." % (word, name))
            return False

    if p.alive:
        utils.game_print("You are dead.")
        utils.game_print("You were caught trying to %s %s."
            % (word, p.name))
        utils.game_print("%s didn't like this, and killed you.\n"
            % p.name)
        player.death()
    else:
        player._loot(word, p)

    return True

def _do_suicide(player, word, remaining):
    utils.game_print(messages.suicide_message())
    player.death()

def _do_reset(player, word, remaining):
    player.reset_game = True

def _do_inspect(player, word, item):
    if item == '':
        _do_look(player, word, item)
        return True

    target = utils.find_any_item(player, item)
    if not target:
        target = utils.find_person(player, item)

    if target:
        target.on_look(player)
        return True

    tile = utils.find_tile(player, item)
    if tile:
        utils.game_print("%s." % tile.name)
        return True
    else:
        utils._wrap_print(
            messages.dontknow_message("%s %s" % (word, item)))

    return False


def _do_look(player, word, item):
    if item != '':
        return _do_inspect(player, word, item)

    utils.game_print(player.describe_current_tile())
    return True

def _do_look_under(player, word, item):
    if item == '':
        utils._wrap_print("What do you want to %s?" % word)
        return False

    target = utils.find_any_item(player, item)
    if target:
        target.on_look_under(player)
        return True

    utils._wrap_print(messages.dontknow_message("%s %s"
        % (word, item)))
    return False

def _do_attack(player, word, remaining):
    if remaining == '':
        utils._wrap_print("What do you want to %s?" % word)
        return False

    target_name = None
    item_name = None

    if ' with ' in remaining:
        fields = remaining.split(' with ')
        target_name = fields[0].strip()
        item_name = fields[1].strip()

    unset_name_values = ["", None]
    if (target_name in unset_name_values) or (item_name in unset_name_values):
        utils._wrap_print("What do you want to attack %s with?" % remaining)
        return False

    item = utils.find_inventory_item(player, item_name)
    if not item:
        utils._wrap_print("No %s in your inventory to %s with."
                % (item_name, word))
        return False

    target = utils.find_item(player, target_name)
    if not target:
        target = utils.find_person(player, target_name)
        if not target:
            if utils.is_location(player, target_name):
                utils.game_print(messages.nonsensical_action_message(
                    '%s %s' % (word, target_name)))
            else:
                _no_item_message(player, target_name)
                return False

    target.on_attack(player, item)
    return True

def _do_picknose(player, word, remaining):
    utils.game_print(messages.gross_action_message("pick your nose"))
    return True

def _do_sleep(player, word, remaining):
    utils.game_print(messages.sleep_message(word))
    return True

def add_commands(parser):
    commands = [
        [EQUIP_WORDS, _do_equip, "equip an item from your inventory",
            "%s <item>"],

        [MAP_WORDS, _do_show_map, "show a map of your current area", "%s"],

        [ATTACK_WORDS, _do_attack, "attack something with a weapon",
            "%s <thing> with <item>"],

        [OPEN_WORDS, _do_open, "open a container or door", "%s <item>"],

        [UNLOCK_WORDS, _do_unlock, "unlock a locked container or door", "%s <item>"],

        [BURN_WORDS, _do_burn, "burn an item", "%s <item>"],

        [READ_WORDS, _do_read, "read an item", "%s <item>"],

        [SUICIDE_WORDS, _do_suicide, "commit suicide", "%s"],

        [RESET_WORDS, _do_reset, "reset game to the beginning", "%s"],

        [SET_NAME_WORDS, _do_set_name, "change player's name", "%s"],

        [TAKE_WORDS, _do_take, "Take an item and add it to your inventory",
            "%s <item> [from <location>]"],

        [PUT_WORDS, _do_put, "put an item somewhere", "%s <item> <location>"],

        [DROP_WORDS, _do_drop, "drop an item from your inventory", "%s <item>"],

        [SPEAK_WORDS, _do_speak, "speak with a person by name", "%s <person>"],

        [UNEQUIP_WORDS, _do_unequip, "unequip your equipped item "
            "(if any)", "%s <item>"],

        [EAT_WORDS, _do_eat, "eat something", "%s <item>"],

        [SMELL_WORDS, _do_smell, "smell an item", "%s <item>"],

        [TASTE_WORDS, _do_taste, "taste an item", "%s <item>"],

        [LOOT_WORDS, _do_loot, "attempt to loot a person by name",
            "%s <person>"],

        [INSPECT_WORDS, _do_inspect, "examine an item in more "
            "detail", "%s <item>"],

        [LOOK_UNDER_WORDS, _do_look_under, "look under an item", "%s <item>"],

        [LOOK_INSIDE_WORDS, _do_look_inside,
            "examine the contents of an object", "%s <item>"],

        [LOOK_WORDS, _do_look, "examine your current surroundings", "%s"],

        [INNOCUOUS, _do_innocuous],

        [PICK_NOSE_WORDS, _do_picknose],

        [SLEEP_WORDS, _do_sleep],

        [ALLSTAR_SONG, _do_allstar_song]
    ]

    for arglist in commands:
        if utils.is_disabled_command(*arglist[0]):
            continue

        parser.add_command(*arglist)

    return parser
