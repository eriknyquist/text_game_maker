import sys

import commands

import text_game_maker
from text_game_maker.items import (Item, Food, Weapon, SmallBag, SmallTin,
    Coins, Blueprint, Lighter, Paper, Furniture)

from text_game_maker.tile import Tile
from text_game_maker.person import Person
from text_game_maker.map_builder import MapBuilder
from text_game_maker import crafting

def on_start(player):
    name = text_game_maker.read_line("What is your name?")
    player.set_name(name.title())

def main():
    builder = MapBuilder(
        commands.build_parser(),
        "your cell",
        """in a small, windowless cell of bare concrete."""
    )

    paperclip = Item("a", "paperclip", "", 0)
    paperclip.combustible = False

    bunk = Furniture("a", "narrow bunk", "in the corner", combustible=False)
    string = Item("a", "piece of string", "on the floor", 0)
    smallbag = SmallBag("a", "rucksack", "on the bunk", 15)
    tin = SmallTin("a", "small tin", "on the bunk", 0)
    coins = Coins("on the floor", 7)
    lockpick = Item("a", "lockpick", "", 0)
    lighter = Lighter("on the bunk")

    poster = Paper("a", "poster", "on the wall", [
            "<playername>",
            "Wanted for crimes against the State. $50000 to be "
            "awarded for capture, dead or alive."
        ],
        "WANTED!", "WANTED!"
    )

    lockpick_blueprint = Blueprint([string, paperclip], lockpick)

    tin.add_items([coins, paperclip, lockpick_blueprint])
    builder.add_items([bunk, string, smallbag, tin, lighter, poster])
    builder.add_door("a", "cell door", "east")

    builder.move_east(
        "a dark hallway",
        "a dark hallway, with a dim light at the end"
    )

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
