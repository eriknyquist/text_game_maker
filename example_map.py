import sys

import commands

import text_game_maker as gamemaker
from text_game_maker import audio
from text_game_maker.items import Item, Food, Weapon, SmallBag
from text_game_maker.tile import Tile
from text_game_maker.person import Person
from text_game_maker.map_builder import MapBuilder

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
    name = gamemaker.read_line("What is your name?")
    title = gamemaker.read_line("What is your title (sir, lady, etc...)?")

    player.set_name(name.title())
    player.set_title(title.title())

def main():
    builder = MapBuilder(
        commands.build_parser(),
        "your cell",
        """in a small, windowless cell of bare concrete. A narrow wooden bunk is
        in the corner."""
    )

    builder.add_item(Item("a", "piece of string", "on the floor", 0))
    builder.add_item(Item("a", "paperclip", "on the floor", 0))
    builder.add_item(SmallBag("a", "small rucksack", "on the bunk", 15))

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
