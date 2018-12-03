import sys

import commands

import text_game_maker
from text_game_maker.items import Item, Food, Weapon, SmallBag
from text_game_maker.tile import Tile
from text_game_maker.person import Person
from text_game_maker.map_builder import MapBuilder
from text_game_maker import crafting

string = Item("a", "piece of string", "on the floor", 0)
paperclip = Item("a", "paperclip", "on the floor", 0)
lockpick = Item("a", "lockpick", "", 0)
smallbag = SmallBag("a", "small rucksack", "on the bunk", 15)

class CellDoor(Tile):
    def on_enter(self, player, src, dest):
        """
        :param text_game_maker.Player player: Player instance
        :param text_game_maker.Tile src: source tile (the tile that player is\
        trying to exit)
        :param text_game_maker.Tile dest: destination tile (the tile that player\
            is trying to enter)
        """
        pass

def on_start(player):
    name = text_game_maker.read_line("What is your name?")
    title = text_game_maker.read_line("What is your title (sir, lady, etc...)?")

    player.set_name(name.title())
    player.set_title(title.title())

def main():
    builder = MapBuilder(
        commands.build_parser(),
        "your cell",
        """in a small, windowless cell of bare concrete. A narrow wooden bunk is
        in the corner."""
    )

    builder.add_item(string)
    builder.add_item(paperclip)
    builder.add_item(smallbag)

    crafting.add([string, paperclip], lockpick)

    builder.move_east(
        "the cell door",
        "a dark hallway", CellDoor
    )

    builder.set_locked()

    # Set the input prompt
    builder.set_input_prompt("[action?]")

    # Set on_start callback to get player's name
    builder.set_on_start(on_start)

    # Start the game!
    builder.run_game()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('Bye!')
