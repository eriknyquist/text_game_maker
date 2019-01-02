import sys

import commands

import text_game_maker
from text_game_maker.items import (Item, Food, Weapon, Bag, SmallBag, SmallTin,
    Coins, Blueprint, Lighter, Paper, PaperBag, Furniture, Car)

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
    parser = commands.build_parser()
    builder = MapBuilder(parser)

    # Start building the map; create the first tile/room
    builder.start_map(
        "the field",
        """standing in a field beside a desolate country road."""
    )

    idcard = Paper("an", "ID badge", "on the floor", [
            "name: <playername>",
            "occupation: field agent",
            "CID: 5545658868"
        ], header="ID CARD", footer="ID CARD"
    )
    
    # Create all the items in the room
    paperclip = Item("a", "paperclip", "", 0, combustible=False)
    string = Item("a", "piece of string", "", 0)

    # furniture is special, you can't take it like other items
    car = Car("a", "car", "beside you", 0)

    # bag and tin are also special, they can contain other items
    rucksack = Bag("a", "rucksack", "on the bunk", 15)
    paperbag = PaperBag("a", "paper bag", "on the bunk", 15)
    tin = SmallTin("a", "small tin", "on the bunk", 0)

    lockpick = Item("a", "lockpick", "", 0)
    coins = Coins("on the floor", 7)
    lighter = Lighter("on the ground")

    # Make a blueprint for a lockpick; lockpick takes one string and one paperclip
    lockpick_blueprint = Blueprint([string, paperclip], lockpick)

    sword = Weapon("a", "sword", "on the ground", 200, 10)
    # Put some items inside the small tin
    tin.add_items([coins, paperclip, lockpick_blueprint])

    # Add all the items to the room
    car.add_items([string, rucksack, tin, lighter, paperbag])

    builder.add_items([car, lighter, idcard, sword])

    # Move east and add a new room behind the locked door.
    builder.move_east(
        "a forest",
        "a dark forest with scobby lods"
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
