from text_game_maker.game_objects.person import Person, Context
from text_game_maker.utils.responses import STANDARD_GREETINGS
from text_game_maker.utils.utils import serializable_callback
from text_game_maker.materials.materials import Material

from text_game_maker.game_objects.items import (Item, Food, Weapon, Bag,
    SmallBag, SmallTin, Coins, Blueprint, Paper, PaperBag, LargeContainer,
    Furniture, Matches, Flashlight, Battery, Lockpick, StrongLockpick, Lighter
)

# Tile IDs.
# WARNING: changing these names will break any previously created save files
celldoor_id = "cell_door"
prisondoor_id = "prison_main_door"
startingcell_id = "cell_01"
othercell_id = "cell_02"
prisonoffice_id = "prison_office"
entrance_id = "prison_entrance"
hallway_id = "prison_hallway"
alleyway_id = "prison_alleyway"
prisonyard_id = "prison_yard"
pawnshop_id = "pawnshop"

@serializable_callback
def _do_buy(person, player):
    player.buy_item_from(person)

@serializable_callback
def _do_sell(person, player):
    player.sell_item_to(person)

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

    builder.set_smell("It smells like urine and sweat.")
    builder.set_ground_smell("The ground smells like urine and concrete.")
    builder.set_dark(True)
    builder.set_first_visit_message_in_dark(True)

    # Create all the items in the room
    paperclip = Item("a", "paperclip", location="on the floor", combustible=False)
    string = Item("a", "piece of string", location="on the floor")
    lockpick = Lockpick()

    # furniture is special, you can't take it like other items
    bunk = Furniture("a", "narrow bunk", location="in the corner",
        combustible=False)

    # bag and tin are also special, they can contain other items
    rucksack = Bag("a", "rucksack", location="on the bunk")
    tin = SmallTin("a", "small tin", location="on the bunk")

    # Make a blueprint for a lockpick; lockpick takes one string and one paperclip
    lockpick_blueprint = Blueprint([paperclip, string], lockpick)

    # Put something inside the small tin
    tin.add_items([lockpick_blueprint])

    # Put tin inside the rucksack
    rucksack.add_items([tin])

    # Add all the items to the room
    builder.add_items([bunk, string, paperclip, rucksack])
    builder.add_door("a", "cell door", "east", door_id=celldoor_id)

def prison_entrance_hall(builder):
    builder.set_tile_id(entrance_id)
    builder.set_name("the entrance hall")
    builder.set_description("in the prison entrance hall")
    builder.set_first_visit_message("It is not quite so dark in here, and you "
        "can see clearly. There doesn't seem to be anyone around.")

    builder.set_name_from_east("the prison entrance")
    oldman = Person("an", "old man", location="squatting in the corner")
    oldman.add_default_responses("How interesting.", "Oh, really?", "Indeed.",
        "Fascinating, yes.", "Oh, yes? Interesting.", "Mmhmm.")

    oldman.add_responses(
        (["(.* )?(what( is|'?s)? (wrong|happening|going on)).*"],
            ["Huh. You just woke up or somethin? Raiders rolled in, gutted the "
            "place. If I were you, I'd take the freebie and get out of here "
            "before the replacements show up. Probably on their way right "
            "now."]),
        (["(.* )?where.* i .*go.*"], ["Anywhere besides here.", "Away from "
            "the prison, obviously"]),
        (["(.* )?(where (are we|is this)|what is this place).*"], ["A prison. "
            "You couldn't figure that out by yourself?"]),
    )

    greeting_context = Context(STANDARD_GREETINGS)
    raiders_context = Context()
    raiders_context.add_entry_phrases(
        (["(.* )?(what|who).*raiders?.*"], ["Raiders. Bandits. Outlaws. You know?",
            "How can you not know what raiders are?"])
    )

    raiders_context.add_responses(
        (["(.* )?why.*(they|raiders?).*"], ["Hell, how should I know?"]),
        (["(.* )?(tell|talk) (me)?.*about.*(them|raiders?).*"],
            ["They're bad news. Avoid them. That's all you need to know."])
    )

    replacements_context = Context()
    replacements_context.add_entry_phrases(
        (["(.* )?(what|who)?.*replacements?.*"], ["Yeah, replacements to like, "
            "run the prison.", "Replacement prison guards."])
    )

    replacements_context.add_responses(
        (["(.* )?when.*(they|replacements?).*"], ["I don't know, but I wouldn't "
            "recommend waiting around to find out. You'll end up back in one "
            "of those cells."])
    )

    oldman.add_context(greeting_context)
    oldman.add_context(raiders_context)
    oldman.add_context(replacements_context)

    builder.add_item(oldman)

    # Add a door to the east. The door will be locked and will require a
    # lockpick to unlock.
    builder.add_door("a", "heavy iron door", "east", door_id=prisondoor_id)

def prison_hallway(builder):
    builder.set_tile_id(hallway_id)
    builder.set_dark(True)
    builder.set_name("a narrow hallway")
    builder.set_description("in a narrow, low-ceilinged hallway")

def prison_yard(builder):
    builder.set_tile_id(prisonyard_id)
    builder.set_dark(True)
    builder.set_name("the prison yard")
    builder.set_description("in the prison yard")
    puddle = Item("a", "murky puddle", location="on the ground",
        material=Material.MUD)
    bench = Furniture("a", "wooden bench", location="in the corner")
    album = Item("a copy of", "Nickelback's Greatest Hits",
        location="on the bench", value=5)

    builder.add_items([puddle, bench, album])

def other_cell(builder):
    builder.set_tile_id(othercell_id)
    builder.set_name("another cell")
    builder.set_description("in a small cell identical to your own cell.")
    builder.set_dark(True)

    paperbag = PaperBag("a", "paper bag", location="on the bunk")
    paperbag.add_items([Coins(value=7), Matches(), Battery()])

    bunk = Furniture("a", "narrow bunk", location="in the corner",
        combustible=False)

    builder.add_items([bunk, paperbag])

def prison_office(builder):
    builder.set_tile_id(prisonoffice_id)
    builder.set_name("the prison office")
    builder.set_description("in the prison office")
    builder.set_first_visit_message("It looks like the office has been ransacked.")
    builder.set_dark(True)

    flashlight = Flashlight(location="on the desk")
    coins = Coins(location="on the desk", value=32)
    desk = Furniture("a", "small wooden desk", location="against the wall",
        combustible=False)
    chair = Furniture("a", "chair", location="against the wall",
        combustible=False)

    idcard = Paper("a", "business card", paragraphs=[
            "<playername>, Senior Accountant",
            "Branch: 115N",
            "CID: 55458868"
        ], header="Central Bank", footer="Central Bank"
    )

    cabinet = LargeContainer("a", "filing cabinet", location="in the corner")
    cabinet.add_items([idcard, Battery()])
    builder.add_items([desk, chair, cabinet, coins, flashlight])

def prison_alleyway(builder):
    builder.set_tile_id(alleyway_id)
    builder.set_name("a dark alley")
    builder.set_description("in a dimly lit alleyway outside the prison")
    builder.set_first_visit_message("it is raining lightly, and in the "
        "distance you can hear sirens")

    builder.set_smell("It smells like wet concrete and rotting food")

def pawn_shop(builder):
    builder.set_name("a pawn shop")
    builder.set_description("inside the pawn shop")
    builder.set_first_visit_message("a long flourescent bulb flickers faintly "
        "on the ceiling.")
    builder.set_smell("It smells like mould and bleach")

    counter = Furniture("a", "long wooden counter", location="along one side of "
        "the room", combustible=False)

    fork = Item("a", "fork", value=4)
    paperclip = Item("a", "paperclip", value=2)
    string = Item("a", "piece of string", value=1)
    blueprint = Blueprint([fork, string], StrongLockpick(), value=25)

    cashier = Person("a", "cashier", location="behind the counter")
    cashier.add_items([fork, blueprint, Lighter(), Battery(), paperclip, string])

    cashier.set_introduction("Are you buying or selling?")

    cashier.add_responses(
        (["(.* )?buy.*"], [_do_buy]),
        (["(.* )?sell.*"], [_do_sell]),
    )

    cashier.add_shopping_list(
        ("strong lockpick", 10),
        ("Nickelback's Greatest Hits", 200)
    )

    builder.add_items([counter, cashier])

    desk = Furniture("a", "small wooden desk", location="against the wall",
        combustible=False)
