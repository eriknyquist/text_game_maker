import sys
import os
import importlib
import inspect

from text_game_maker.builder.map_builder import MapBuilder
from text_game_maker.parser.parser import CommandParser

class MapRunnerError(Exception):
    pass

class MapRunner(object):
    """
    Extend this class and implement the two methods below to run maps with the
    text-game-runner.py script
    """
    def build_parser(self, parser):
        """
        Implement this method to add custom commands to the game parser

        :param text_game_maker.parser.parser.CommandParser parser: command\
            parser
        """
        pass

    def build_map(self, builder):
        """
        Implement this method to build a map using functions from
        text_game_maker.builder.map_builder

        :param text_game_maker.builder.map_builder.MapBuilder builder: map\
            builder instance
        """
        raise NotImplementedError('Must implement this method')

def get_runner_from_filename(filename):
    """
    Import the given file, look for any classes that are subclasses of
    text_game_maker.utils.runner.MapRunner, and return the class object of the
    first one found (if any)

    :param str filename: file to read
    :return: MapRunner subclass object found (None if no MapRunner subclasses\
        are found
    """
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

def run_map_from_class(classobj):
    """
    Create an instance of the given map runner class, and run it

    :param classobj: mapp runner class object
    """
    runner = classobj()
    parser = CommandParser()

    runner.build_parser(parser)
    builder = MapBuilder(parser)
    runner.build_map(builder)

    try:
        builder.run_game()
    except KeyboardInterrupt:
        return

def run_map_from_filename(filename):
    """
    Import a file, look for any classes that are subclasses of
    text_game_maker.utils.runner.MapRunner, and run the first one found (if any)

    :param str filename: file to read
    """
    runnerclass = get_runner_from_filename(filename)
    if not runnerclass:
        raise MapRunnerError("Unable to find a MapRunner class in %s"
            % filename)

    run_map_from_class(runnerclass)
