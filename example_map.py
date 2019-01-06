import commands
import example_map_rooms as rooms

import text_game_maker
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

    rooms.prison_starting_cell(builder)
    builder.move_east()
    rooms.prison_hallway_1(builder)

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
