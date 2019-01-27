import commands
import example_map_rooms as rooms

import text_game_maker
from text_game_maker.crafting import crafting
from text_game_maker.tile import tile
from text_game_maker.utils import utils, runner
from text_game_maker.player.player import serializable_callback

@serializable_callback
def lighter_equip_hint(player, turns):
    if (player.current.tile_id != rooms.startingcell_id) or player.can_see():
        return

    utils._wrap_print("Hint: say things like 'look in pockets', 'pockets',"
        " 'inventory', or just 'i' to show your inventory")
    utils._wrap_print("Hint: say things like 'use lighter' or 'equip lighter' "
        "to use the lighter as a light source")

# Called when the game starts
def on_game_run(player):
    # read name from player
    name = utils.read_line("What is your name?: ")

    # captialize with name.title() and set as player name
    player.set_name(name.title())
    player.schedule_task(lighter_equip_hint, 10)

class ExampleMapRunner(runner.MapRunner):
    def build_parser(self, parser):
        return commands.build_parser(parser)

    def build_map(self, builder):
        rooms.prison_starting_cell(builder)
        builder.move_east()
        rooms.prison_hallway_1(builder)
        builder.move_south()
        rooms.other_cell(builder)
        builder.move_north()
        builder.move_north()
        rooms.prison_office(builder)
        builder.move_south()

        # Set the input prompt
        builder.set_input_prompt(" > ")

        # Set on_game_run callback to get player's name
        builder.set_on_game_run(on_game_run)
