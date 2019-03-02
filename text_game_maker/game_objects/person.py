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

        self.context = None
        self.context_index = 0
        self.contexts = []

    def get_special_attrs(self):
        ret = {}
        responses = self.responses.dump_to_dict()

        for pattern in responses.keys():
            newvalue = []
            for value in responses[pattern]:
                if callable(value):
                    newvalue.append(utils.serialize_callback(value))
                else:
                    newvalue.append(value)

            responses[pattern] = newvalue

        ret['responses'] = responses
        return ret

    def set_special_attrs(self, attrs):
        responses = attrs['responses']

        for pattern in responses.keys():
            newvalue = []
            for val in responses[pattern]:
                try:
                    callback = utils.deserialize_callback(val)
                except RuntimeError:
                    newvalue.append(val)
                else:
                    newvalue.append(callback)

            responses[pattern] = newvalue

        self.responses.load_from_dict(responses)
        del attrs['responses']
        return attrs

    def on_look(self, player):
        return "It's %s."  % self.name

    def add_default_responses(self, *responses):
        """
        Set responses to reply with when the player types something does not
        match any of the added patterns when speaking to this person

        :param responses: one or more responses to pick randomly from. \
            Responses may be either a string of text to speak, or a callback \
            of the form ``callback(person, player)``, where ``person`` is the \
            Person object the player is speaking to, and ``player`` is the \
            Player object
        """
        self.default_responses.extend(responses)

    def add_response(self, patterns, responses):
        """
        Set responses to reply with when player types a specific pattern
        when talking to this person

        :param list patterns: list of regular expressions that will be used to \
            check player input
        :param list responses: list of responses to pick randomly from if the \
            player says something that matches one of the patterns in \
            ``patterns``. Responses may be either a string of text to speak, \
            or a callback of the form ``callback(person, player)``, where \
            ``person`` is the Person object the player is speaking to, and \
            ``player`` is the Player object
        """
        self.responses['|'.join(patterns)] = responses

    def add_context(self, *pattern_response_pairs):
        context = []
        for patterns, responses in pattern_response_pairs:
            responsedict = redict.ReDict()
            responsedict['|'.join(patterns)] = responses
            context.append(responsedict)

        self.contexts.append(context)

    def add_responses(self, *responses):
        """
        Set multiple pattern/response pairs at once

        :param responses: one or more response pairs, where each pair is a \
            tuple containing arguments for a single ``add_response`` call, \
            e.g. ``add_responses((['cat.*'], ['meow']), (['dog.*], ['woof']))``
        """
        for patterns, responses in responses:
            self.add_response(patterns, responses)

    def _get_default_response(self):
        if self.default_responses:
            return random.choice(self.default_responses)

        return "I don't understand what you're talking about"

    def _check_get_response(self, responsedict, text):
        try:
            responses = responsedict[text]
        except KeyError:
            return None

        return random.choice(responses)

    def _attempt_context_entry(self, text):
        for context in self.contexts:
            responsedict = context[0]
            response = self._check_get_response(responsedict, text)
            if response:
                self.context = context
                self.context_index = 1
                return response

        return None

    def get_response(self, text):
        response = None

        # If currently in a context, try to get a response from the context
        if self.context:
            for responsedict in self.context:
                response = self._check_get_response(responsedict, text)
                if response:
                    break

        # If no contextual response is available, try to get a response from
        # the dict of contextless responses
        if not response:
            response = self._check_get_response(self.responses, text)
            if response:
                # If we are currently in a context but only able to get a
                # matching response from the contextless dict, set the current
                # context to None
                if self.context:
                    self.context = None
            else:
                # No contextless responses available, attempt context entry
                response = self._attempt_context_entry(text)
                if not response:
                    response = self._get_default_response()


        if not response:
            return text

        return response

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
            if callable(response):
                response(self, player)
            else:
                self.say(response)
