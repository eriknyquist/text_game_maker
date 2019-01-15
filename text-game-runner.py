import sys
import os
import importlib
import inspect

from text_game_maker.builder.map_builder import MapBuilder
from text_game_maker.parser.parser import CommandParser
from text_game_maker.utils.runner import MapRunner

def get_runner_from_filename(filename):
    dname, fname = os.path.split(filename)
    if fname == '':
        if dname == '':
            raise ValueError('Please provide a valid filename')

        fname = dname
        dname = None

    modname = os.path.splitext(fname)[0]

    if dname:
        sys.path.insert(0, os.path.abspath(dname))

    try:
        module = importlib.import_module(modname)
    except ImportError:
        raise ImportError("Can't import file %s" % filename)

    if dname:
        sys.path.pop(0)

    members = inspect.getmembers(module, inspect.isclass)
    for m in members:
        cls = m[1]
        if issubclass(cls, MapRunner):
            return cls

    return None

def main():
    if len(sys.argv) != 2:
        print("Usage: %s <map runner file>" % sys.argv[0])
        return 1

    runnerclass = get_runner_from_filename(sys.argv[1])
    if not runnerclass:
        print('Unable to find a MapRunner class in %s' % sys.argv[1])
        return 1

    runner = runnerclass()
    parser = CommandParser()

    runner.build_parser(parser)
    builder = MapBuilder(parser)
    runner.build_map(builder)

    builder.run_game()
    return 0

if __name__ == "__main__":
    try:
        ret = main()
    except KeyboardInterrupt:
        print('Bye!')
    else:
        sys.exit(ret)
