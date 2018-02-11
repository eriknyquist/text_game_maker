
PRINT_SPEED_WORDS = ['print']

PRINT_DELAY_WORDS = ['print delay']

PRINT_WIDTH_WORDS = ['print width']

KILL_WORDS = [
    'quit', 'stop', 'finish', 'end', 'exit'
]

GO_WORDS = [
    'go', 'move', 'walk', 'travel', 'crawl', 'shuffle', 'run', 'skip', 'jump',
    'dance', 'creep', 'sneak', 'tiptoe'
]

TAKE_WORDS = [
    'take', 'pick up', 'steal', 'acquire', 'grab', 'get', 'snatch', 'dock'
]

DROP_WORDS = [
    'drop', 'throw away', 'discard', 'chuck', 'ditch', 'delete', 'undock'
]

EQUIP_WORDS = [
    'equip', 'use', 'whip out', 'take out', 'brandish'
]

UNEQUIP_WORDS = [
    'unequip', 'put away', 'stop using', 'stow'
]

SPEAK_WORDS = [
    'speak with', 'speak to', 'talk to', 'chat to', 'chat with', 'talk with',
    'chat', 'speak', 'talk'
]

SHOW_COMMAND_LIST_WORDS = [
    'show commands', 'show controls', 'show words', 'show wordlist',
    'commands', 'controls', 'wordlist', 'words'
]

INSPECT_WORDS = [
    'look at', 'inspect', 'examine'
]

LOOK_WORDS = [
    'look', 'peep', 'peek', 'show', 'viddy'
]

LOOT_WORDS = [
    'loot', 'search', 'rob', 'pickpocket'
]

INVENTORY_WORDS = [
    'i', 'inventory'
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

class Node(object):
    def __init__(self, char, token=None):
        self.char = char
        self.children = {}
        self.token = token

    def __str__(self):
        return self.char

    def __repr__(self):
        return self.char

class SimpleTextFSM(object):
    def __init__(self):
        self.start = Node('')

    def add_token(self, string, token):
        current = self.start
        for c in string:
            if c not in current.children:
                current.children[c] = Node(c)

            current = current.children[c]
        
        current.token = token

    def _dump(self, node):
        ret = {}
        for c in node.children:
            ret[c] = self._dump(node.children[c])

        return ret

    def dump_tree(self):
        return json.dumps(self._dump(self.start), indent=2)

    def run(self, input_string):
        current = self.start
        i = 0

        for c in input_string:
            try:
                current = current.children[c]
            except KeyError, AttributeError:
                return i, current.token

            i += 1

        return i, current.token
