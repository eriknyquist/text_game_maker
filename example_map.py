import sys

import commands

import text_game_maker
from text_game_maker.items import (Item, Food, Weapon, Bag, SmallBag, SmallTin,
    Coins, Blueprint, Lighter, Paper, Furniture)

from text_game_maker.map_builder import MapBuilder
from text_game_maker import crafting

# Called when the game starts
def on_game_run(player):
    # read name from player
    name = text_game_maker.read_line("What is your name?: ")

    # captialize with name.title() and set as player name
    player.set_name(name.title())

def main():
    # Create a MapBuilder object with the command parser
    builder = MapBuilder(commands.build_parser())

    # Start building the map; create the first tile/room
    builder.start_map(
        "your cell",
        """in a small, windowless cell of bare concrete."""
    )

    # Create all the items in the room
    paperclip = Item("a", "paperclip", "", 0, combustible=False)
    string = Item("a", "piece of string", "on the floor", 0)
    coins = Coins("on the floor", 7)
    lockpick = Item("a", "lockpick", "", 0)
    lighter = Lighter("on the bunk")

    poster = Paper("a", "poster", "on the wall", [
            "<playername>",
            "Wanted for crimes against the State. $50000 to be "
            "awarded for capture, dead or alive."
        ],

        header="WANTED!", footer="WANTED!"
    )

    # furniture is special, you can't take it like other items
    bunk = Furniture("a", "narrow bunk", "in the corner", combustible=False)

    # bag and tin are also special, they can contain other items
    rucksack = Bag("a", "rucksack", "on the bunk", 15)
    paperbag = SmallBag("a", "paper bag", "on the bunk", 15)
    tin = SmallTin("a", "small tin", "on the bunk", 0)

    # Make a blueprint for a lockpick; lockpick takes one string and one paperclip
    lockpick_blueprint = Blueprint([string, paperclip], lockpick)

    # Put some items inside the small tin
    tin.add_items([coins, paperclip, lockpick_blueprint])

    # Add all the items to the room
    builder.add_items([bunk, string, rucksack, tin, lighter, poster, paperbag])

    # Add a door to the east. The door will be locked and will require a
    # lockpick to unlock.
    builder.add_door("a", "cell door", "east")

    # Move east and add a new room behind the locked door.
    builder.move_east(
        "a dark hallway",
        "a dark hallway, with a dim light at the end"
    )

    # Set the input prompt
    builder.set_input_prompt(" > ")

    # Set on_game_run callback to get player's name
    builder.set_on_game_run(on_game_run)

    # Start the game!
    builder.run_game()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('Bye!')
