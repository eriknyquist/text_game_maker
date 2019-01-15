import sys

from text_game_maker.utils.runner import run_map_from_filename

def main():
    if len(sys.argv) != 2:
        print("Usage: %s <map runner file>" % sys.argv[0])
        return 1

    run_map_from_filename(sys.argv[1])
    return 0

if __name__ == "__main__":
    try:
        ret = main()
    except KeyboardInterrupt:
        print('Bye!')
    else:
        sys.exit(ret)
