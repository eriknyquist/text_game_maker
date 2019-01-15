from text_game_maker.parser.parser import CommandParser

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
