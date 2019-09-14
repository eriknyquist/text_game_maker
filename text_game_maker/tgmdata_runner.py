import os
import sys
from text_game_maker.utils.runner import MapRunner, run_map_from_class

def main():
    if len(sys.argv) != 2:
        print("\n\ntext_game_maker .tgmdata file runner utility; quickly test "
              "a .tgmdata file without writing any code.")
        print("\nUsage:\n")
        print("  python -m text_game_maker.tgmdata_runner <.tgmdata file>\n")

        sys.exit(1)

    class TgmdataRunner(MapRunner):
        def build_map(self, builder):
            builder.load_map_data(sys.argv[1])

            # Set the input prompt
            builder.set_input_prompt("")

    run_map_from_class(TgmdataRunner)

if __name__ == "__main__":
    main()
