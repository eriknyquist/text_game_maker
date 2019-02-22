import sys
import random

import text_game_maker
from text_game_maker.game_objects.generic import Item
from text_game_maker.utils import utils, redict

class Person(Item):
    """
    Represents a person that the player can interact with
    """

    def __init__(self, prefix="", name="", **kwargs):
        """
        Initialises a Person instance

        :param str name: name of Person, e.g. "John"
        :param str description: location description of Person, e.g.\
            "squatting in the corner"
        :param list items: List of Items held by this person
        """

        super(Person, self).__init__(**kwargs)

        self.edible = True
        self.inanimate = False
        self.alive = True
        self.prefix = prefix
        self.name = name
        self.prep = 'the ' + self.name

        self.speak_count = 0
        self.script = None
        self.script_pos = 0
        self.task_id = 0
        self.responses = redict.ReDict()
        self.default_responses = []

    def get_special_attrs(self):
        ret = {}
        ret['responses'] = self.responses.dump_to_dict()
        return ret

    def set_special_attrs(self, attrs):
        self.responses.load_from_dict(attrs['responses'])
        del attrs['responses']
        return attrs

    def on_look(self, player):
        return "It's %s."  % self.name

    def add_default_responses(self, *responses):
        self.default_responses.extend(responses)

    def add_response(self, patterns, responses):
        self.responses['|'.join(patterns)] = responses

    def add_responses(self, *responses):
        for patterns, responses in responses:
            self.add_response(patterns, responses)

    def get_response(self, text):
        try:
            responses = self.responses[text]
        except KeyError:
            if not self.default_responses:
                return "I don't understand what you're talking about"

            return random.choice(self.default_responses)

        if not responses:
            return text

        return random.choice(responses)

    def die(self, player, msg=None):
        """
        Kill this person, and print a message to inform the player
        of this person's death.

        :param text_game_maker.player.player.Player player: player instance
        :param str msg: message to print informing player of person's death
        """

        p = utils.find_person(player, self.name)

        self.alive = False
        self.name = "%s's corpse" % self.name
        self.prep = self.name
        self.location = "on the ground"
        player.current.add_person(self)

        if msg is None or msg == "":
            msg = '%s has died.' % self.name

        utils.game_print(msg)

    def say(self, msg):
        """
        Speak to the player

        :param msg: message to speak
        :type msg: str
        """

        utils.game_print('%s says:  "%s"' % (self.name, msg))

    def set_script(self, lines):
        self.script = lines

    def on_speak(self, player):
        speech = ' '
        prompt = 'talking to %s (say nothing to exit): >' % self.name

        while speech != '':
            speech = utils.read_line_raw(prompt).strip()
            if speech == '':
                break

            response = self.get_response(speech)
            self.say(response)
