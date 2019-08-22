import os
from text_game_maker.example_map import example_map_rooms as rooms
from text_game_maker.example_map import room_ids

from text_game_maker.crafting import crafting
from text_game_maker.tile import tile
from text_game_maker.utils import utils, runner

# Called when the game starts
def on_game_run(player):
    # read name from player
    player.read_player_name_and_set()

class ExampleMapRunner(runner.MapRunner):
    def build_map(self, builder):
        script_dir = os.path.dirname(os.path.realpath(__file__))
        mapdata_path = os.path.join(script_dir, 'example_map.tgmdata')
        builder.load_map_data(mapdata_path)

        rooms.prison_starting_cell(builder)
        rooms.prison_entrance_hall(builder)
        rooms.prison_hallway(builder)
        rooms.prison_yard(builder)
        rooms.other_cell(builder)
        rooms.prison_office(builder)
        rooms.prison_alleyway(builder)
        rooms.pawn_shop(builder)
        rooms.main_street_upper(builder)
        rooms.main_street_lower(builder)
        rooms.central_bank(builder)
        rooms.central_bank_hallway(builder)
        rooms.central_bank_vault(builder)
        rooms.central_bank_employee_lounge(builder)
        rooms.central_bank_managers_office(builder)

        # Set the input prompt
        builder.set_input_prompt("")

        # Set on_game_run callback to get player's name
        # and initialize some game-specific events/scheduled tasks
        builder.set_on_game_run(on_game_run)
