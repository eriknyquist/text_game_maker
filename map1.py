import map_builder
import sys

alan_info = {
    'count': 0,
    'eaten': False
}

alan_lines = [
    "Hey, get out of here, I'm in here.",
    "Seriously. go away.",
    "Please, get out.",
    "OK, fine, do you have anything worth trading? I'm hungry.\n"
    "I'd buy some food if you had it.",
    "Do you have anything worth trading? I'm hungry.\n"
    "I'd buy some food if you had it.",
]

def alan_speak_callback(person, player):
    if alan_info['eaten']:
        return "Didn't we talk already? Be gone."

    if player.inventory_items['equipped']:
        item = person.buy_equipped_item(player)
        if item:
            # Sale successful
            alan_info['eaten'] = True
            return None
        else:
            # Sale cancelled
            return None

    if alan_info['count'] < len(alan_lines):
        alan_info['count'] += 1

    return alan_lines[alan_info['count'] - 1]
        
def locked_room_enter_callback(player, src, dest):
    equipped = player.inventory_items['equipped']
    if equipped and equipped.name == 'metal key':
        player.delete_equipped()
        dest.locked = False
        return True
    
    return True

def exit_cb(player, src, dest):
    map_builder.slow_print("You are dead. You plummeted into the rocks and the "
        "sea below the window.")
    sys.exit()

def main():
    builder = map_builder.MapBuilder(
        "the starting room",
        """in a small square room with stone walls and ceilings. The floor is
        dirt. The only light comes from the fire of the torches that line the
        walls."""
    )

    builder.add_item(map_builder.Item("a", "metal key", "on the floor", 25))
    builder.add_item(map_builder.Item("a", "sausage", "on the floor", 5))

    builder.move_west(
        "an open window, with nothing to be seen but darkness behind it", ""
    )

    builder.add_enter_callback(exit_cb)

    builder.move_east()
    builder.move_east(
        "a small closet",
        """a small closet, barely large enough inside for two people to stand
        upright"""
    )

    builder.set_locked()
    builder.add_enter_callback(locked_room_enter_callback)

    builder.add_person(
        map_builder.Person(
            "Alan", "standing in the corner", alan_speak_callback
        )
    )

    builder.move_west("a cellar", "a dark cellar")

    # Set the input prompt
    builder.set_input_prompt("[action?]: ")

    # Finished building map-- get the player object
    player = builder.build_player()

    name = map_builder.get_input("What is your name? : ")
    title = map_builder.get_input("What is your title (sir, lady, "
        "etc...)? : ")

    player.set_name(name)
    player.set_title(name)

    # Start the game!
    map_builder.run_game(player)

main()
