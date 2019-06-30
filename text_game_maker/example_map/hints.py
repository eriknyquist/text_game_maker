from text_game_maker.crafting import crafting
from text_game_maker.example_map import room_ids
from text_game_maker.utils import utils
from text_game_maker.utils.utils import serializable_callback


# If player is still locked in the starting room and does not yet have the
# lighter equipped, give them a hint
@serializable_callback
def lighter_equip_hint(player, turns):
    # No need for a hint if player has already gotten out, or equipped lighter
    if (player.current.tile_id != room_ids.startingcell_id) or player.can_see():
        return

    # No need for a hint if player has already unlocked the cell door but is
    # still/back in the cell with no light source for some reason
    if ((not player.current.east.is_door())
            or (not player.current.east.locked)):
        return

    utils._wrap_print("Hint: say things like 'show inventory', 'inventory', or "
        "just 'i' to show your inventory. Say things like 'use lighter' or "
        "'equip lighter' to use the lighter as a light source")

@serializable_callback
def rucksack_hint_callback(player, turn):
    # Don't give a hint if player is not still in the starting room
    if player.current.tile_id != room_ids.startingcell_id:
        return

    # Don't give a hint if player already has rucksack
    if player.inventory is not None:
        return

    utils._wrap_print("Hint: say things like 'get rucksack', 'take rucksack' or"
        " just 'take sack' to acquire the rucksack and increase your inventory"
        " capacity")

@serializable_callback
def small_tin_hint_callback(player, turn):
    # Don't give a hint if player knows how to make the lockpick
    if crafting.can_craft('lockpick'):
        return

    utils._wrap_print("Hint: say things like 'look inside <item>' to see if an "
        "item contains other items. Say things like 'get <item> from <item>' "
        "to retrieve an item that is contained inside another item.")

@serializable_callback
def light_source_decay_callback(player, turns):
    if player.equipped and player.equipped.is_light_source:
        player.equipped.decrement_fuel()

        if not player.current.dark:
            utils.game_print("Your {0} is equipped, unequip by saying "
                "'unequip {0}' or 'stop using {0}' to avoid wasting "
                "batteries or fuel".format(player.equipped.name))

    player.schedule_task(light_source_decay_callback, 1)

def on_use_event(player, word, remaining):
    # As soon as player equips light source, set up hint to trigger in 10 moves
    # if they haven't acquired the rucksack yet
    if player.equipped and player.equipped.is_light_source:
        # Remove event so it doesn't trigger anymore
        player.parser.remove_event_handler('use', on_use_event)

        player.schedule_task(rucksack_hint_callback, 10)
