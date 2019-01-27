import json
import text_game_maker
from text_game_maker.builder import map_builder

PRINT_SPEED_WORDS = ['print speed']

PRINT_DELAY_WORDS = ['print delay']

PRINT_WIDTH_WORDS = ['print width']

SOUND_WORDS = ['sound', 'audio']

KILL_WORDS = [
    'quit', 'stop', 'finish', 'end', 'exit'
]

GO_WORDS = [
    'go', 'walk', 'travel', 'crawl', 'shuffle', 'run', 'skip',
    'creep', 'sneak', 'tiptoe'
]

CRAFT_WORDS = [
    'craft', 'make', 'create', 'build'
]

SHOW_COMMAND_LIST_WORDS = [
    'show commands', 'show controls', 'show words', 'show wordlist',
    'commands', 'controls', 'wordlist', 'words'
]

HELP_WORDS = [
    '?', 'help'
]

SAVE_WORDS = [
    'save'
]

LOAD_WORDS = [
    'load'
]

INVENTORY_WORDS = [
    'i', 'inventory', 'show inventory', 'show pockets', 'pockets'
]

class Command(object):
    """
    Container class for data needed to execute a particular game command
    """

    def __init__(self, word_list, callback, desc, phrase_fmt):
        self.word_list = word_list
        self.callback = callback
        self.desc = desc
        self.phrase_fmt = phrase_fmt

        if self.desc:
            self.desc = self.desc[0].upper() + self.desc[1:]

    def help_text(self):
        if (not self.desc) or (not self.phrase_fmt):
            return None

        ret = '\n' + self.desc + ':\n\n'
        for w in self.word_list:
            ret += ('    "' + self.phrase_fmt + '"\n') % w

        return ret

class Node(object):
    def __init__(self, char, token=None, text=None):
        self.char = char
        self.children = {}
        self.parent = None
        self.token = token
        self.text = text

    def __str__(self):
        return self.char

    def __repr__(self):
        return self.char

class SimpleTextFSM(object):
    def __init__(self):
        self.start = Node('')
        self.current = self.start

    def _extend_fsm(self, string, token):
        current = self.start
        for c in string:
            if c not in current.children:
                current.children[c] = Node(c)

            current = current.children[c]

        current.token = token
        current.text = string

    def add_token(self, string, token):
        self._extend_fsm(string, token)
        self._extend_fsm(string + ' ', token)

    def _dump_json(self, node):
        ret = {}
        for c in node.children:
            ret[c] = self._dump_json(node.children[c])

        return ret

    def dump_json(self):
        return json.dumps(self._dump_json(self.start), indent=2)

    def iterate(self, node=None):
        if node is None:
            node = self.start

        if node.token:
            yield node.token

        for c in node.children:
            for token in self.iterate(node.children[c]):
                yield token

    def _dump_text(self, node):
        ret = []
        for c in node.children:
            child = node.children[c]

            if child.text and child.text != "" and c != ' ':
                ret.append(child.text)

            ret.extend(self._dump_text(child))

        return ret

    def get_children(self):
        ret = []

        if self.current.text and self.current.text != "":
            ret.append(self.current.text)

        ret.extend(self._dump_text(self.current))
        return ret

    def run(self, input_string):
        self.current = self.start
        i = 0

        for c in input_string:
            try:
                self.current = self.current.children[c]
            except KeyError, AttributeError:
                return i, self.current.token

            i += 1

        return i, self.current.token

class CommandParser(SimpleTextFSM):
    def __init__(self, *args, **kwargs):
        super(CommandParser, self).__init__()

        default_commands = [
            [HELP_WORDS, map_builder._do_help, "show basic help information"],

            [SHOW_COMMAND_LIST_WORDS, map_builder._do_show_command_list,
                "show all game commands", "%s"],

            [SAVE_WORDS, map_builder._do_save,
                "save the current game state to a file", "%s"],

            [LOAD_WORDS, map_builder._do_load,
                "load a previously saved game state file", "%s"],

            [PRINT_SPEED_WORDS, map_builder._do_set_print_speed,
                "set printing speed", "%s fast/slow"],

            [PRINT_DELAY_WORDS, map_builder._do_set_print_delay, "set the "
                "per-character print delay when slow printing is enabled",
                "%s <seconds>"],

            [SOUND_WORDS, map_builder._do_set_audio, "turn audio on or off",
                "%s [on|off]"],

            [PRINT_WIDTH_WORDS, map_builder._do_set_print_width,
                "set the maximum line width for game output", "%s <width>"],

            [KILL_WORDS, map_builder._do_quit, "guit the game", "%s"],

            [GO_WORDS, map_builder._do_move,
                "move the player (north/south/east/west)", "%s <direction>"],

            [CRAFT_WORDS, map_builder._do_craft,
                "Craft an item", "%s <item name>"],

            [INVENTORY_WORDS, map_builder._do_inventory_listing,
            "show player's inventory", "%s"]
        ]

        for arglist in default_commands:
            self.add_command(*arglist)

    def add_command(self, word_set, callback, help_text=None, fmt=None):
        cmd = Command(word_set, callback, help_text, fmt)
        for word in word_set:
            self.add_token(word, cmd)

