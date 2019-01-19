import text_game_maker
from text_game_maker.game_objects.items import (Item, Food, Weapon, Bag,
    SmallBag, SmallTin, Coins, Blueprint, Lighter, Paper, PaperBag, Furniture)

from text_game_maker.crafting import crafting

def prison_starting_cell(builder):
    # Start building the map; create the first tile/room
    builder.start_map()
    builder.set_name("your cell")
    builder.set_description("in a small, windowless cell of bare concrete.")

    # Create all the items in the room
    paperclip = Item("a", "paperclip", combustible=False)
    string = Item("a", "piece of string", location="on the floor")
    coins = Coins(location="on the floor", value=7)
    lockpick = Item("a", "lockpick")
    lighter = Lighter(location="on the bunk")

    idcard = Paper("an", "ID badge", locations="on the floor", paragraphs=[
            "name: <playername>",
            "occupation: field agent",
            "CID: 5545658868"
        ], header="ID CARD", footer="ID CARD"
    )

    # furniture is special, you can't take it like other items
    bunk = Furniture("a", "narrow bunk", location="in the corner",
        combustible=False)

    # bag and tin are also special, they can contain other items
    rucksack = Bag("a", "rucksack", location="on the bunk")
    paperbag = PaperBag("a", "paper bag", location="on the bunk")
    tin = SmallTin("a", "small tin", location="on the bunk")

    # Make a blueprint for a lockpick; lockpick takes one string and one paperclip
    lockpick_blueprint = Blueprint([string, paperclip], lockpick)

    rucksack.add_items([coins, paperclip])
    # Put some items inside the small tin
    tin.add_items([idcard, lockpick_blueprint])

    # Add all the items to the room
    builder.add_items([bunk, string, rucksack, tin, lighter, paperbag])

    # Add a door to the east. The door will be locked and will require a
    # lockpick to unlock.
    builder.add_door("a", "cell door", "east")

def prison_hallway_1(builder):
    # Move east and add a new room behind the locked door.
    builder.set_name("a dark hallway")
    builder.set_description("in a dark hallway, with a dim light at the end")
