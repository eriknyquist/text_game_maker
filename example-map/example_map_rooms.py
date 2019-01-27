import text_game_maker
from text_game_maker.game_objects.items import (Item, Food, Weapon, Bag,
    SmallBag, SmallTin, Coins, Blueprint, Paper, PaperBag, LargeContainer,
    Furniture
)

from text_game_maker.crafting import crafting

celldoor_id = "cell_door"
prisondoor_id = "prison_main_door"
startingcell_id = "cell_01"
othercell_id = "cell_02"
prisonoffice_id = "prison_office"
darkhallway_id = "prison_hallway"

def prison_starting_cell(builder):
    # Start building the map; create the first tile/room
    builder.start_map()
    builder.set_tile_id(startingcell_id)
    builder.set_name("your cell")
    builder.set_description("in a small, windowless cell of bare concrete")
    builder.set_first_visit_message(
        "you do not know where you are, and you cannot remember how you got "
        "here. In fact, you can't remember anything at all, except for your "
        "name. Your name is <playername>."
    )

    builder.set_dark(True)

    # Create all the items in the room
    paperclip = Item("a", "paperclip", location="on the floor", combustible=False)
    string = Item("a", "piece of string", location="on the floor")
    lockpick = Item("a", "lockpick")

    # furniture is special, you can't take it like other items
    bunk = Furniture("a", "narrow bunk", location="in the corner",
        combustible=False)

    # bag and tin are also special, they can contain other items
    rucksack = Bag("a", "rucksack", location="on the bunk")
    tin = SmallTin("a", "small tin", location="on the bunk")

    # Make a blueprint for a lockpick; lockpick takes one string and one paperclip
    lockpick_blueprint = Blueprint([string, paperclip], lockpick)

    # Put something inside the small tin
    tin.add_items([lockpick_blueprint])

    # Put tin inside the rucksack
    rucksack.add_items([tin])

    # Add all the items to the room
    builder.add_items([bunk, string, paperclip, rucksack])
    builder.add_door("a", "cell door", "east", door_id=celldoor_id)

def prison_hallway_1(builder):
    # Move east and add a new room behind the locked door.
    builder.set_tile_id(darkhallway_id)
    builder.set_name("a dark hallway")
    builder.set_description("in the prison hallway")
    builder.set_first_visit_message("It is not quite so dark in here, and you"
        "can see clearly.")

    # Add a door to the east. The door will be locked and will require a
    # lockpick to unlock.
    builder.add_door("a", "heavy iron door", "east", door_id=prisondoor_id)

def other_cell(builder):
    builder.set_tile_id(othercell_id)
    builder.set_name("another cell")
    builder.set_description("in a small cell identical to your own cell.")
    builder.set_dark(True)

    coins = Coins(location="on the floor", value=7)
    paperbag = PaperBag("a", "paper bag", location="on the bunk")
    paperbag.add_item(coins)

    bunk = Furniture("a", "narrow bunk", location="in the corner",
        combustible=False)

    builder.add_items([bunk, paperbag])

def prison_office(builder):
    builder.set_tile_id(prisonoffice_id)
    builder.set_name("the prison office")
    builder.set_description("in the prison office")
    builder.set_first_visit_message("It looks like the office has been ransacked.")

    coins = Coins(location="on the desk", value=32)
    desk = Furniture("a", "small wooden desk", location="against the wall",
        combustible=False)
    chair = Furniture("a", "chair", location="against the wall",
        combustible=False)

    idcard = Paper("an", "ID badge", location="on the floor", paragraphs=[
            "name: <playername>",
            "occupation: field agent",
            "CID: 5545658868"
        ], header="ID CARD", footer="ID CARD"
    )

    cabinet = LargeContainer("a", "filing cabinet", location="in the corner")
    cabinet.add_item(idcard)
    builder.add_items([desk, chair, cabinet, coins])
