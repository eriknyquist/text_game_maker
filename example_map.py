import sys
import text_game_maker as gamemaker

alan_info = {
    'count': 0,
    'eaten': False
}

def alan_speak_callback(person, player):
    """
    "Speak" callback for a helpful game character who explains game
    rules & commands

    To attach to a Person object, pass this callback to the
    text_game_maker.Person constructor when creating a Person instance

    :param text_game_maker.Person person: the Person that this callback is\
        attached to
    :param text_game_maker.Player player: Player instance
    """

    # Alan will progressively give more hints about basic controls
    # each time the player tries to speak to him
    alan_lines = [
        "%s %s, do you have any food to sell? I'm terribly hungry.\n"
        "I'll help you if you can sell me something to eat."
        % (player.title, player.name),
        "Do you have anything you want to sell? I'm terribly hungry.",
        "Do you have anything you want to sell? I'm terribly hungry.\n"
        "To offer a sale, equip the inventory item you want to sell and\n"
        "speak to me.",
        "To offer a sale, equip the inventory item you want to sell and\n"
        "speak to me. Say 'i' or 'inventory' to see items in your inventory.\n",
        "Say 'i' or 'inventory' to see what's in your inventory.\n"
        "Try using words like 'get' or 'take' to add items to your inventory.\n"
        "To offer a sale, equip the inventory item you want to sell and\n"
        "speak to me.",
        "Use words like 'look', 'show' or '?' to print current description\n"
        "Say 'i' or 'inventory' to see what's in your inventory.\n"
        "Use words like 'get' or 'take' to add items to your inventory.\n"
        "To offer a sale, equip the inventory item you want to sell and\n"
        "speak to me.",
    ]

    if player.inventory_items['equipped']:
        # Player has an item equipped: try to buy it
        item = person.buy_equipped_item(player)
        if item:
            # Sale successful
            alan_info['eaten'] = True
            if item.name == 'sausage':
                del person.items[item.name]
            else:
                person.die('\n%s died from trying to eat a %s.'
                    % (person.name, item.name))

            return None
        else:
            # Sale cancelled
            return None

    else:
        # Player has no item equipped: print basic controls
        # (if we've been fed...)
        if alan_info['eaten']:
            return gamemaker.basic_controls

    if alan_info['count'] < len(alan_lines):
        alan_info['count'] += 1

    return alan_lines[alan_info['count'] - 1]

def locked_room_enter_callback(player, src, dest):
    """
    Enter callback for a room with a locked door that can only be unlocked by
    an item named 'metal key'. Called when player attempts to enter whichever
    tile this callback is attached to.

    Attach to current room with text_game_maker.set_on_enter()

    :param text_game_maker.Player player: Player instance
    :param text_game_maker.Tile src: source tile (the tile that player is\
        trying to exit)
    :param text_game_maker.Tile dest: destination tile (the tile that player\
        is trying to enter)
    """

    if player.has_equipped('metal key'):
        player.delete_equipped()
        dest.set_unlocked()
        return True

    return True

def enter_window_callback(player, src, dest):
    """
    Enter callback for a tile that kills the player as soon as they enter.
    Called when player attempts to enter whichever room this callback is
    attached to.

    Attach to current room with text_game_maker.set_on_enter()

    :param text_game_maker.Player player: text_game_maker.Player object
    :param text_game_maker.Tile src: source tile (the tile that player is\
        trying to exit)
    :param text_game_maker.Tile dest: destination tile (the tile that player\
        is trying to enter)
    """

    # text_game_maker.game_print will print slowly, one character at a time,
    # unless player has typed 'print fast', in which case game_print will print
    # normally
    gamemaker.game_print("You are dead. You plummeted into the rocks "
        "and the sea below the window.")
    sys.exit()

def main():
    builder = gamemaker.MapBuilder(
        "the starting room",
        """in a small square room with stone walls and ceilings. The floor is
        dirt. The only light comes from the fire of the torches that line the
        walls."""
    )

    builder.add_item(gamemaker.Item("a", "metal key", "on the floor", 25))
    builder.add_item(gamemaker.Item("a", "sausage", "on the floor", 5))

    builder.add_person(
        gamemaker.Person(
            "Alan", "standing in the corner", alan_speak_callback
        )
    )

    builder.move_west(
        "an open window, with nothing to be seen but darkness behind it", ""
    )

    builder.set_on_enter(enter_window_callback)

    builder.move_east()
    builder.move_east(
        "a small closet",
        """a small closet, barely large enough inside for two people to stand
        upright"""
    )

    builder.set_locked()
    builder.set_on_enter(locked_room_enter_callback)

    builder.move_west("a cellar", "a dark cellar")

    # Set the input prompt
    builder.set_input_prompt("[action?]: ")

    name = gamemaker.read_line("What is your name? : ")
    title = gamemaker.read_line("What is your title (sir, lady, etc...)? : ")

    builder.set_player_name(name.title())
    builder.set_player_title(title.title())

    # Start the game!
    builder.run_game()

if __name__ == "__main__":
    main()
