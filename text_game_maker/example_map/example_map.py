from text_game_maker.example_map import example_map_rooms as rooms

from text_game_maker.crafting import crafting
from text_game_maker.tile import tile
from text_game_maker.utils import utils, runner

# Called when the game starts
def on_game_run(player):
    # read name from player
    player.read_player_name_and_set()

class ExampleMapRunner(runner.MapRunner):
    def build_map(self, builder):
        rooms.prison_starting_cell(builder)

        builder.move_east()
        rooms.prison_entrance_hall(builder)

        builder.move_south()
        rooms.prison_hallway(builder)

        builder.move_south()
        rooms.other_cell(builder)

        builder.move_north()
        builder.move_west()
        rooms.prison_yard(builder)

        builder.move_east()
        builder.move_north(2)
        rooms.prison_office(builder)

        builder.move_south()
        builder.move_east()
        rooms.prison_alleyway(builder)

        builder.move_east()
        rooms.main_street_upper(builder)

        builder.move_east()
        rooms.pawn_shop(builder)

        builder.move_west()
        builder.move_south()
        rooms.main_street_lower(builder)

        builder.move_south()
        rooms.central_bank(builder)

        builder.move_east()
        rooms.central_bank_employee_lounge(builder)

        builder.move_west()
        builder.move_south()
        rooms.central_bank_hallway(builder)

        builder.move_east()
        rooms.central_bank_managers_office(builder)

        builder.move_west()
        builder.move_south()
        rooms.central_bank_vault(builder)

        # Set the input prompt
        builder.set_input_prompt("")

        # Set on_game_run callback to get player's name
        # and initialize some game-specific events/scheduled tasks
        builder.set_on_game_run(on_game_run)
