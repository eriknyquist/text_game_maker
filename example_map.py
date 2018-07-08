import sys

import commands

import text_game_maker as gamemaker
from text_game_maker.items import Item, Food, Weapon
from text_game_maker.tile import Tile
from text_game_maker.person import Person
from text_game_maker.map_builder import MapBuilder

alan_info = {
    'count': 0,
    'eaten': False
}

class Alan(Person):
    def on_speak(self, player):
        """
        "Speak" callback for a helpful game character who explains game
        rules & commands

        To attach to a Person object, pass this callback to the
        text_game_maker.Person constructor when creating a Person instance

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
            "Use words like 'look', 'show' or '?' to print current description.\n"
            "Say 'i' or 'inventory' to see what's in your inventory.\n"
            "Use words like 'get' or 'take' to add items to your inventory.\n"
            "To offer a sale, equip the inventory item you want to sell and\n"
            "speak to me.",
        ]

        # If player has an item equipped, try to buy it

        if player.get_equipped():
            item = self.buy_equipped_item(player)
            if item:
                # Sale successful
                alan_info['eaten'] = True
                if item.name == 'sausage':
                    item.delete()
                else:
                    self.die(player, '%s died from trying to eat a %s.'
                        % (self.name, item.name))

                return None
            else:
                # Sale cancelled
                return None

        else:
            # Player has no item equipped: print basic controls
            # (if we've been fed...)
            if alan_info['eaten']:
                return gamemaker.get_basic_controls()

        if alan_info['count'] < len(alan_lines):
            alan_info['count'] += 1

        return alan_lines[alan_info['count'] - 1]

class LockedRoom(Tile):
    def on_enter(self, player, src, dest):
        """
        Enter callback for a room with a locked door that can only be unlocked by
        an item named 'metal key'. Called when player attempts to enter whichever
        tile this callback is attached to.

        :param text_game_maker.Player player: Player instance
        :param text_game_maker.Tile src: source tile (the tile that player is\
        trying to exit)
        :param text_game_maker.Tile dest: destination tile (the tile that player\
            is trying to enter)
        """

        item = player.get_equipped()
        if dest.is_locked() and item and item.name == 'metal key':
            # Player has key equipped-- delete it from player's inventory
            # unlock the destination tile
            item.delete()
            dest.set_unlocked()

        return True

    def on_exit(self, player, src, dest):
        player.clear_tasks()
        return True

class DeathFallWindow(Tile):
    def on_enter(self, player, src, dest):
        """
        Enter callback for a tile that kills the player as soon as they enter.
        Called when player attempts to enter whichever room this callback is
        attached to.
        """

        # text_game_maker.game_print will print slowly, one character at a time,
        # unless player has typed 'print fast', in which case game_print will print
        # normally
        gamemaker.game_print("You are dead. You plummeted into the rocks "
            "and the sea below the window.")
        sys.exit()

def on_start(player):
    name = gamemaker.read_line("What is your name?")
    title = gamemaker.read_line("What is your title (sir, lady, etc...)?")

    player.set_name(name.title())
    player.set_title(title.title())

def main():
    builder = MapBuilder(
        commands.build_parser(),
        "the starting room",
        """in a small square room with stone walls and ceilings. The floor is
        dirt. The only light comes from the fire of the torches that line the
        walls."""
    )

    builder.add_item(Item("a", "metal key", "on the floor", 12))
    builder.add_item(Food("a", "sausage", "on the floor", 5, 10))

    crowbar = Weapon("a", "crowbar", "", 25, 15)
    builder.add_person(
        Alan(
            "Alan", "standing in the corner", items=[crowbar]
        )
    )

    builder.move_west(
        "an open window, outside of which is pitch-black darkness", "", DeathFallWindow
    )

    builder.move_east()
    builder.move_east(
        "a small closet",
        "a small closet, barely large enough inside for two people to stand"
        " upright", LockedRoom
    )

    builder.add_item(Food("a", "lemon", "in the corner", 8, 5))
    builder.add_item(Item("a", "treasure map", "on the wall", 2))

    builder.set_locked()

    builder.move_west("a cellar", "a dark cellar")

    # Set the input prompt
    builder.set_input_prompt("[action?]")

    # Set on_start callback to get player's name
    builder.set_on_start(on_start)

    # Start the game!
    builder.run_game()

if __name__ == "__main__":
    main()
