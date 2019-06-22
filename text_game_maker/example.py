import os
import text_game_maker
from text_game_maker.utils.runner import run_map_from_filename
directory = os.path.dirname(text_game_maker.__file__)

if __name__ == "__main__":
    run_map_from_filename(os.path.join(directory, 'example_map/example_map.py'))
