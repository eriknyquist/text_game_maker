import json
from text_game_maker.utils import utils
from text_game_maker.builder import map_builder
from text_game_maker.parser import commands
from text_game_maker.event.event import Event

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

def _do_debug(player, word, remaining):
    map_builder._debug_next()

class Command(object):
    """
    Container class for data needed to execute a particular game command
    """

    def __init__(self, word_list, callback, desc, usage_fmt, hidden):
        """
        :param list word_list: list of action words that can trigger this\
            parser command.
        :param callback: callback function to be invoked when the player types\
            something beginning with one of the action words. Callback should\
            be of the form ``callback(player, word, remaining)``, where\
            ``player`` is the ``text_game_maker.player.player.Player``\
            instance, ``word`` is the action word typed by the player as a\
            string, and ``remaining`` is the remaining text following the\
            action word as a string.
        :param str desc: text that will be shown when player types "help"\
            followed by one of the action words.
        :param str usage_fmt: format string that will be used to show a usage\
            example for each action word. The format string should contain a\
            single string format character, which will be replaced with the
            action word e.g.``"%s <item>"`` where ``%s`` will be replaced with\
            an action word.
        :param bool hidden: if True, command can still be triggered normally\
            by player input but will be excluded from "help" queries and parser\
            suggestions.
        """
        self.word_list = word_list
        self.callback = callback
        self.desc = desc
        self.usage_fmt = usage_fmt
        self.hidden = hidden
        self.event = Event()

        if self.desc:
            self.desc = self.desc[0].upper() + self.desc[1:]

    def help_text(self):
        """
        Get the help text with usage examples

        :return: generated help text and usage examples
        :rtype: str
        """
        if (not self.desc) or (not self.usage_fmt):
            return None

        ret = '\n' + self.desc + ':\n\n'
        for w in self.word_list:
            ret += ('    "' + self.usage_fmt + '"\n') % w

        return ret

class CharacterTrieNode(object):
    """
    A single node in a CharacterTrie
    """
    def __init__(self, char, token=None, text=None):
        """
        :param str char: character for this node.
        :param token: optional arbitrary object to store at this node.
        :param str text: optional string to store at this node, currently used\
            to hold the full matching text in the last node of a command. Allows
            for easy/quick iterating of all words in the trie.
        """
        self.char = char
        self.children = {}
        self.parent = None
        self.token = token
        self.text = text

    def __str__(self):
        return self.char

    def __repr__(self):
        return self.char

class CharacterTrie(object):
    """
    Simple trie structure where each node is a single character. Used to hold
    all action words for quick retrieval of the command object for a particular
    action word.
    """
    def __init__(self):
        self.start = CharacterTrieNode('')
        self.current = self.start
        self.searchfilter = lambda x: True

    def set_search_filter(self, callback):
        """
        Set function to filter token objects when iterating through the trie

        :param callback: callback function of the form ``callback(token)``,\
            where ``token`` is the token attribute from a Node in the trie. If\
            callback returns True, then this token object will be included in\
            the objects returned by iteration. Otherwise, this token object\
            will be exluded from the objects returned by iteration.
        """
        if callback:
            self.searchfilter = callback

    def _extend_trie(self, string, token):
        current = self.start
        for c in string:
            if c not in current.children:
                current.children[c] = CharacterTrieNode(c)

            current = current.children[c]

        current.token = token
        current.text = string

    def add_token(self, string, token):
        """
        Add an action word to the parser

        :param str string: action word
        :param token: object to set as token attribute of the last node of\
            action word
        """
        self._extend_trie(string, token)
        self._extend_trie(string + ' ', token)

    def _dump_json(self, node):
        ret = {}
        for c in node.children:
            ret[c] = self._dump_json(node.children[c])

        return ret

    def dump_json(self):
        """
        Dump the whole trie as JSON-encoded text

        :return: JSON-encoded trie structure
        :rtype: str
        """
        return json.dumps(self._dump_json(self.start), indent=2)

    def iterate(self):
        """
        Iterate over all nodes in the trie that have non-None token attributes
        :return: iterator for all trie nodes with non-None tokens
        """
        stack = [self.start]

        while stack:
            node = stack.pop(0)
            if node.token and self.searchfilter(node.token):
                yield node.token

            for c in node.children:
                stack.append(node.children[c])

    def _dump_children_text(self):
        ret = []
        stack = [self.current]

        while stack:
            node = stack.pop(0)
            for c in node.children:
                child = node.children[c]

                if ((child.text not in [None, ""]) and (c != ' ')
                        and (self.searchfilter(child.token))):
                    ret.append(child.text)

                stack.append(child)

        return ret

    def get_children(self):
        """
        Return the text of all nodes below the node reached by the last ``run``
        call. Used to generate action word suggestions when an action word is
        partially or incorrectly typed.

        :return: list of action words from all children nodes
        :rtype: [str]
        """
        ret = []

        if ((self.current.text not in [None, ""])
                and (self.searchfilter(self.current.token))):
            ret.append(self.current.text)

        ret.extend(self._dump_children_text())
        return ret

    def run(self, input_string):
        self.current = self.start
        i = 0

        for c in input_string:
            try:
                self.current = self.current.children[c]
            except (KeyError, AttributeError):
                return i, self.current.token

            i += 1

        return i, self.current.token

class CommandParser(CharacterTrie):
    """
    Thin wrapper around a CharacterTrie that adds some default commands
    """
    def __init__(self):
        super(CommandParser, self).__init__()
        self.set_search_filter(lambda x: not x.hidden)

        default_commands = [
            [["debug next command"], _do_debug, None, None, True],

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
                "%s on|off"],

            [PRINT_WIDTH_WORDS, map_builder._do_set_print_width,
                "set the maximum line width for game output", "%s <width>"],

            [KILL_WORDS, map_builder._do_quit, "guit the game", "%s"],

            [GO_WORDS, map_builder._do_move,
                "move the player (north/south/east/west)", "%s <direction>"],

            [CRAFT_WORDS, map_builder._do_craft,
                "Craft an item", "%s <item>"],

            [INVENTORY_WORDS, map_builder._do_inventory_listing,
            "show player's inventory", "%s"]
        ]

        for arglist in default_commands:
            if utils.is_disabled_command(*arglist[0]):
                continue

            self.add_command(*arglist)

        commands.add_commands(self)

    def add_event_handler(self, word, callback):
        """
        Add an event handler to run whenever a command is used, in addition to
        the regular handler for that command.

        :param str word: action word associated with the command to add the\
            event handler to.
        :param callback: callback function to be invoked when the player types\
            something beginning with one of the action words. Callback should\
            be of the form ``callback(player, word, remaining)``, where\
            ``player`` is the ``text_game_maker.player.player.Player``\
            instance, ``word`` is the action word typed by the player as a\
            string, and ``remaining`` is the remaining text following the\
            action word as a string.
        """
        stripped = word.strip()
        i, cmd = self.run(stripped)
        if (i < len(stripped)) or (cmd is None):
            raise ValueError("no parser commands matching '%s'" % stripped)

        cmd.event.add_handler(callback)

    def clear_event_handler(self, word, callback):
        """
        Remove a previously added event handler for a command

        :param str word: action word associated with the command to remove the\
            event handler from.
        :param callback: callback function for event handler to remove
        """
        stripped = word.strip()
        i, cmd = self.run(stripped)
        if (i < len(stripped)) or (cmd is None):
            raise ValueError("no parser commands matching '%s'" % stripped)

        cmd.event.clear_handler(callback)

    def add_command(self, word_set, callback, help_text=None, usage_fmt=None,
            hidden=False):
        """
        Add a command to the parser.

        :param [str] word_set: list of action words that can trigger command
        :param callback: callback function to be invoked when the player types\
            something beginning with one of the action words. Callback should\
            be of the form ``callback(player, word, remaining)``, where\
            ``player`` is the ``text_game_maker.player.player.Player``\
            instance, ``word`` is the action word typed by the player as a\
            string, and ``remaining`` is the remaining text following the\
            action word as a string.
        :param str help_text: text that will be shown when player types "help"\
            followed by one of the action words.
        :param str usage_fmt: format string that will be used to show a usage\
            example for each action word. The format string should contain a\
            single string format character, which will be replaced with the
            action word e.g.``"%s <item>"`` where ``%s`` will be replaced with\
            an action word.
        :param bool hidden: if True, command can still be triggered normally\
            by player input but will be excluded from "help" queries and parser\
            suggestions.
        """
        cmd = Command(word_set, callback, help_text, usage_fmt, hidden)
        for word in word_set:
            self.add_token(word, cmd)
