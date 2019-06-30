import random

from text_game_maker.example_map import hints
from text_game_maker.example_map import room_ids
from text_game_maker.game_objects.person import Person, Context
from text_game_maker.utils.responses import STANDARD_GREETINGS
from text_game_maker.utils.utils import serializable_callback
from text_game_maker.materials.materials import Material

from text_game_maker.game_objects.items import (Item, Food, Weapon, Bag,
    SmallBag, SmallTin, Coins, Blueprint, Paper, PaperBag, LargeContainer,
    Furniture, BoxOfMatches, Flashlight, Battery, Lockpick, StrongLockpick,
    Lighter, Machete
)

class config(object):
    idnumber = random.randrange(100000, 500000)
    vaultcode = random.randrange(10000000, 50000000)

@serializable_callback
def _do_buy(person, player):
    player.buy_item_from(person)

@serializable_callback
def _do_sell(person, player):
    player.sell_item_to(person)

def on_use_event(player, word, remaining):
    # As soon as player equips light source, set up hint to trigger in 10 moves
    # if they haven't acquired the rucksack yet
    if player.equipped and player.equipped.is_light_source:
        # Remove event so it doesn't trigger anymore
        player.parser.clear_event_handler('use', on_use_event)

        player.schedule_task(hints.rucksack_hint_callback, 10)

def on_take_event(player, word, remaining):
    # As soon as player gets the rucksack, set up hint to trigger in 10 moves
    # if they haven't gotten the lockpick blueprint yet
    if player.inventory is not None:
        # Remove event so it doesn't trigger anymore
        player.parser.clear_event_handler('take', on_take_event)

        player.schedule_task(hints.small_tin_hint_callback, 10)

def new_game_event_handler(player):
    player.schedule_task(hints.light_source_decay_callback, 1)
    player.schedule_task(hints.lighter_equip_hint, 5)

    player.parser.add_event_handler("use", on_use_event)
    player.parser.add_event_handler("take", on_take_event)

def prison_starting_cell(builder):
    # Start building the map; create the first tile/room
    builder.start_map()
    builder.set_tile_id(room_ids.startingcell_id)
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
    builder.add_door("a", "cell door", "east", door_id=room_ids.celldoor_id)

    builder.add_new_game_start_event_handler(new_game_event_handler)

def prison_entrance_hall(builder):
    builder.set_tile_id(room_ids.entrance_id)
    builder.set_name("the entrance hall")
    builder.set_description("in the prison entrance hall")
    builder.set_first_visit_message("It is not quite so dark in here, and you "
        "can see clearly. There doesn't seem to be anyone around.")

    builder.set_name_from_east("the prison entrance")
    oldman = Person("an", "old man", location="squatting in the corner")
    oldman.add_default_responses("How interesting.", "Oh, really?", "Indeed.",
        "Fascinating, yes.", "Oh, yes? Interesting.", "Mmhmm.")

    oldman.add_responses(
        (["(.* )?(what( is|'?s)? (wrong|happening|goin(g)? on)).*"],
            ["Huh. You just woke up or somethin? Raiders rolled in, gutted the "
            "place. If I were you, I'd take the freebie and get out of here "
            "before the replacements show up. Probably on their way right "
            "now."]),
        (["(.* )?where.* i .*go.*"], ["Anywhere besides here.", "Away from "
            "the prison, obviously"]),
        (["(.* )?(where (are we|is this)|what( is|'?s) this place).*"], ["A prison. "
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

    oldman.add_item(Machete())

    builder.add_person(oldman)

    # Add a door to the east. The door will be locked and will require a
    # lockpick to unlock.
    builder.add_door("a", "heavy iron door", "east",
                     door_id=room_ids.prisondoor_id)

def prison_hallway(builder):
    builder.set_tile_id(room_ids.hallway_id)
    builder.set_dark(True)
    builder.set_name("a narrow hallway")
    builder.set_description("in a narrow, low-ceilinged hallway")

def prison_yard(builder):
    builder.set_tile_id(room_ids.prisonyard_id)
    builder.set_dark(True)
    builder.set_name("the prison yard")
    builder.set_description("in the prison yard")
    puddle = Furniture("a", "murky puddle", location="on the ground",
        material=Material.MUD)
    bench = Furniture("a", "wooden bench", location="in the corner")
    album = Item("a", "Nickelback's Greatest Hits CD",
        location="on the bench", value=5)

    builder.add_items([puddle, bench, album])

def other_cell(builder):
    builder.set_tile_id(room_ids.othercell_id)
    builder.set_name("another cell")
    builder.set_description("in a small cell identical to your own cell.")
    builder.set_dark(True)

    paperbag = PaperBag("a", "paper bag", location="on the bunk")
    paperbag.add_items([Coins(value=7), BoxOfMatches(), Battery()])

    bunk = Furniture("a", "narrow bunk", location="in the corner",
        combustible=False)

    builder.add_items([bunk, paperbag])

def prison_office(builder):
    builder.set_tile_id(room_ids.prisonoffice_id)
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

    idcard = Paper("an", "ID badge", paragraphs=[
            "<playername>, Branch Manager",
            "Branch: 115N",
            "CID: %d" % config.idnumber
        ], header="Central Bank", footer="Central Bank"
    )

    cabinet = LargeContainer("a", "filing cabinet", location="in the corner")
    cabinet.add_items([idcard, Battery()])
    builder.add_items([desk, chair, cabinet, coins, flashlight])

def prison_alleyway(builder):
    builder.set_tile_id(room_ids.alleyway_id)
    builder.set_name("a dark alley")
    builder.set_description("in a dimly lit alleyway outside the prison")
    builder.set_first_visit_message("it is raining lightly, and in the "
        "distance you can hear sirens")

    builder.set_smell("It smells like wet concrete and rotting food")

def pawn_shop(builder):
    builder.set_tile_id(room_ids.pawnshop_id)
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

def main_street_upper(builder):
    builder.set_tile_id(room_ids.mainstreet_upper_id)
    builder.set_name("upper main street")
    builder.set_description("on upper main street")
    builder.set_smell("It smells like sewage")

def main_street_lower(builder):
    builder.set_tile_id(room_ids.mainstreet_lower_id)
    builder.set_name("lower main street")
    builder.set_description("on lower main street")
    builder.set_smell("It smells like sewage")
    builder.add_door("a", "large wooden door", "south",
                     door_id=room_ids.bankdoor_id)

def central_bank(builder):
    builder.set_tile_id(room_ids.bank_entrance_id)
    builder.set_name("the central bank entrance hall")
    builder.set_description("in the central bank entrance hall")
    builder.set_first_visit_message("your footsteps echo sharply around the "
            "high ceilings as your feet strike the higly polished marble floor")
    builder.set_smell("It smells like pine and lemon")

def central_bank_hallway(builder):
    builder.set_tile_id(room_ids.bank_hallway_id)
    builder.set_name("a hallway")
    builder.set_description("in a bright, clean hallway")
    builder.set_smell("It smells like pine and lemon")

    builder.add_keypad_door("a", "wooden door with a keypad and a sign reading "
            "'MANAGER'", "east", config.idnumber,\
            door_id=room_ids.bank_officedoor_id,
            prompt="Enter employee CID to unlock the door")
    builder.add_keypad_door("a", "large metal door with a keypad", "south",
            config.vaultcode, door_id=room_ids.bank_vaultdoor_id)

def central_bank_vault(builder):
    builder.set_tile_id(room_ids.bank_vault_id)
    builder.set_name("the bank vault")
    builder.set_description("in the bank vault")
    builder.set_first_visit_message("rows of lockboxes line the walls, and "
            "the ceiling and floor are solid steel. It looks like the vault has"
            " also been looted, and there's not much left in here.")
    builder.set_smell("It smells like steel")

    coins = Coins(value=582, location="on the table")
    table = Furniture("a", "square metal table", location="in the centre of "
            "the room")

    builder.add_items([coins, table])

def central_bank_employee_lounge(builder):
    builder.set_tile_id(room_ids.bank_lounge_id)
    builder.set_name("the employee lounge")
    builder.set_description("in the employee lounge")
    builder.set_first_visit_message("it looks like somebody left this room in a "
        "hurry")
    builder.set_smell("It smells like coffee and bananas")

    banana = Food("a", "banana", location="on the ground", energy=15)
    mug = Item("a", "mug", location="on the ground")
    sandwich = Food("a", "sandwich", location="on the table", energy=15)
    battery = Battery(location="on the table")
    table = Furniture("a", "round wooden table", location="in the centre of the room")
    chair = Furniture("a", "chair", location="in the centre of the room")

    builder.add_items([banana, mug, sandwich, table, chair])

def central_bank_managers_office(builder):
    builder.set_tile_id(room_ids.bank_office_id)
    builder.set_name("the managers office")
    builder.set_description("in the managers office")
    builder.set_first_visit_message("this room also looks like it has been "
            "ransacked")
    builder.set_smell("It smell like pine and lemon")

    postit = Paper("a", "post-it note", paragraphs=[
            "code 4 vault: %d" % config.vaultcode
        ], location="stuck to the wall"
    )

    desk = Furniture("a", "wide mahogany desk", location="against the wall",
        combustible=False)
    chair = Furniture("a", "worn leather chair", location="against the wall",
        combustible=False)
    cabinet = LargeContainer("a", "filing cabinet", location="in the corner")

    builder.add_items([desk, chair, cabinet, postit])
