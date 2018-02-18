
PRINT_SPEED_WORDS = ['print speed']

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
    'equip', 'use', 'whip out', 'brandish'
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

    def dump_tree(self):
        return json.dumps(self._dump(self.start), indent=2)

    def _dump_text(self, node):
        ret = []
        for c in node.children:
            child = node.children[c]
            if not child.text or child.text == "":
                ret.extend(self._dump_text(child))
            else:
                ret.append(child.text)

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
