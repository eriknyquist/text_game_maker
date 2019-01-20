import commands
import example_map_rooms as rooms

import text_game_maker
from text_game_maker.crafting import crafting
from text_game_maker.utils import utils, runner
from text_game_maker.player.player import serializable_callback

@serializable_callback
def scheduler_test(player, turns):
    utils.game_print("Scheduler: %d turns" % player.turns)
    player.schedule_task(scheduler_test, turns + 1)

# Called when the game starts
def on_game_run(player):
    # read name from player
    name = utils.read_line("What is your name?: ")

    # captialize with name.title() and set as player name
    player.set_name(name.title())
    player.schedule_task(scheduler_test, 5)

class ExampleMapRunner(runner.MapRunner):
    def build_parser(self, parser):
        return commands.build_parser(parser)

    def build_map(self, builder):
        rooms.prison_starting_cell(builder)
        builder.move_east()
        rooms.prison_hallway_1(builder)

        # Set the input prompt
        builder.set_input_prompt(" > ")

        # Set on_game_run callback to get player's name
        builder.set_on_game_run(on_game_run)
