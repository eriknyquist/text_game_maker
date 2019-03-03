import sys
import random

import text_game_maker
from text_game_maker.game_objects.generic import Item, GameEntity
from text_game_maker.utils import utils
from text_game_maker.utils.redict import ReDict

def _check_get_response(responsedict, text):
    try:
        responses = responsedict[text]
    except KeyError:
        return None

    return random.choice(responses)

def _serialize_redict(d):
    ret = d.dump_to_dict()

    for pattern in ret.keys():
        newvalue = []
        for value in ret[pattern]:
            if callable(value):
                newvalue.append(utils.serialize_callback(value))
            else:
                newvalue.append(value)

        ret[pattern] = newvalue

    return ret

def _deserialize_redict(d):
    for pattern in d.keys():
        newvalue = []
        for val in d[pattern]:
            try:
                callback = utils.deserialize_callback(val)
            except RuntimeError:
                newvalue.append(val)
            else:
                newvalue.append(callback)

        d[pattern] = newvalue

    return ReDict().load_from_dict(d)

class DiscussionContext(GameEntity):
    def __init__(self, lists=None):
        self.entry = ReDict()
        self.responses = ReDict()
        self.chains = []
        self.chain = None
        self.chain_index = 0

        if lists:
            self._build_from_lists(lists)

    def get_special_attrs(self):
        ret = {}
        ret['entry'] = self.entry.dump_to_dict()
        ret['responses'] = self.responses.dump_to_dict()
        ret['chain'] = None
        ret['chains'] = []

        for i in range(len(self.chains)):
            chain = self.chains[i]
            ret['chains'].append([_serialize_redict(d) for d in chain])

            if self.chain and chain is self.chain:
                ret['chain'] = i

        return ret

    def set_special_attrs(self, attrs):
        self.entry.clear()
        self.responses.clear()
        self.chains = []
        self.chain = None

        self.entry.load_from_dict(attrs['entry'])
        self.responses.load_from_dict(attrs['responses'])

        for chain in attrs['chains']:
            self.chains.append([_deserialize_redict(d) for d in chain])

        if attrs['chain']:
            self.chain = self.chains[attrs['chain']]

        del attrs['entry']
        del attrs['responses']
        del attrs['chains']
        del attrs['chain']

    def _build_from_lists(self, lists):
        target_length = 3
        length = len(lists)

        if length < target_length:
            lists.extend([None] * (target_length - length))
        elif length > target_length:
            raise ValueError("Cannot build %s from a list with %d elements "
                "(expecting %d)" % (length, target_length))

        entry, responses, chains = lists
        if entry:
            self.add_entry_phrases(*entry)

        if responses:
            self.add_response_phrases(*responses)

        if chains:
            self.add_chained_phrases(*chains)

    def add_chained_phrases(self, *pattern_response_pairs):
        chain = []
        for patterns, responses in pattern_response_pairs:
            responsedict = ReDict()
            responsedict['|'.join(patterns)] = responses
            chain.append(responsedict)

        self.chains.append(chain)

    def add_entry_phrases(self, *pattern_response_pairs):
        for patterns, responses in pattern_response_pairs:
            self.entry['|'.join(patterns)] = responses

    def add_response_phrases(self, *pattern_response_pairs):
        for patterns, responses in pattern_response_pairs:
            self.responses['|'.join(patterns)] = responses

    def _search_chains(self, text):
        for chain in self.chains:
            if (len(chain) > 0):
                resp = _check_get_response(chain[0], text)
                if resp:
                    return chain, resp

        return None, None

    def _get_chained_response(self, text):
        if not self.chain:
            chain, response = self._search_chains(text)
            if chain:
                self.chain = chain
                self.chain_index = 1
                return response

            return None

        responsedict = self.chain[self.chain_index]
        resp = _check_get_response(responsedict, text)

        if resp:
            if self.chain_index < (len(self.chain) - 1):
                self.chain_index += 1
        elif self.chain_index > 0:
            responsedict = self.chain[self.chain_index - 1]
            resp = _check_get_response(responsedict, text)

        return resp

    def get_response(self, text):
        resp = self._get_chained_response(text)
        if resp:
            return resp

        resp = _check_get_response(self.responses, text)
        if resp:
            return resp

        return _check_get_response(self.entry, text)

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
        self.responses = ReDict()
        self.default_responses = []

        self.context = None
        self.contexts = []

    def get_special_attrs(self):
        ret = {}
        ret['responses'] = _serialize_redict(self.responses)
        ret['context'] = None

        serialized_contexts = []
        for i in range(len(self.contexts)):
            context = self.contexts[i]
            serialized_contexts.append(context.get_special_attrs())

            if self.context and (context is self.context):
                ret['context'] = i

        ret['contexts'] = serialized_contexts
        return ret

    def set_special_attrs(self, attrs):
        self.responses = _deserialize_redict(attrs['responses'])
        self.contexts = []
        self.context = None

        for contextdata in attrs['contexts']:
            context = DiscussionContext()
            context.set_special_attrs(contextdata)
            self.contexts.append(context)

        if attrs['context']:
            self.context = self.contexts[attrs['context']]

        del attrs['responses']
        del attrs['contexts']
        del attrs['context']
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

    def add_response_phrase(self, patterns, responses):
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

    def add_context(self, context):
        self.contexts.append(context)

    def add_response_phrases(self, *pattern_response_pairs):
        """
        Set multiple pattern/response pairs at once

        :param responses: one or more response pairs, where each pair is a \
            tuple containing arguments for a single ``add_response`` call, \
            e.g. ``add_responses((['cat.*'], ['meow']), (['dog.*], ['woof']))``
        """
        for patterns, responses in pattern_response_pairs:
            self.add_response_phrase(patterns, responses)

    def _get_default_response(self):
        if self.default_responses:
            return random.choice(self.default_responses)

        return "I don't understand what you're talking about"

    def _attempt_context_entry(self, text):
        for context in self.contexts:
            response = _check_get_response(context.entry, text)
            if response:
                self.context = context
                return response

        return None

    def get_response(self, text):
        response = None

        # If currently in a context, try to get a response from the context
        if self.context:
            response = self.context.get_response(text)

        # If no contextual response is available, try to get a response from
        # the dict of contextless responses
        if not response:
            response = _check_get_response(self.responses, text)
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
