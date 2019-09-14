import os
import sys
from text_game_maker.utils.runner import run_map_from_filename

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("\n\ntext_game_maker map runner utility")
        print("\nUsage:\n")
        print("  python -m text_game_maker.runner <file with MapRunner class>\n")

        sys.exit(1)

    run_map_from_filename(os.path.abspath(sys.argv[1]))
