import sys
import random

from text_game_maker.game_objects.items import Coins
from text_game_maker.game_objects.living import LivingItem
from text_game_maker.game_objects.generic import Item, GameEntity, ItemSize

from text_game_maker.utils import utils
from text_game_maker.tile import tile
from text_game_maker.chatbot_utils.redict import ReDict
from text_game_maker.chatbot_utils import responder
from text_game_maker.messages import messages

MAX_PLAYER_WAIT_COUNT = 5

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

class Context(GameEntity, responder.Context):
    """
    See text_game_maker.chatbot_utils.responder.Context
    """
    def __init__(self, *args, **kwargs):
        responder.Context.__init__(self, *args, **kwargs)
        GameEntity.__init__(self)

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

    def set_special_attrs(self, attrs, version):
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
        return attrs

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
            self.add_responses(*responses)

        if chains:
            self.add_chained_phrases(*chains)

class Responder(GameEntity, responder.Responder):
    """
    See text_game_maker.chatbot_utils.responder.Responder
    """
    def __init__(self, *args, **kwargs):
        responder.Responder.__init__(self, *args, **kwargs)
        GameEntity.__init__(self)

    def get_special_attrs(self):
        ret = {}
        ret['responses'] = _serialize_redict(self.responses)
        ret['context'] = None
        ret['no_default_response'] = False

        if self.default_response == responder.NoResponse:
            ret['no_default_response'] = True
            ret['default_response'] = None

        serialized_contexts = []
        for i in range(len(self.contexts)):
            context = self.contexts[i]
            serialized_contexts.append(context.get_special_attrs())

            if self.context and (context is self.context):
                ret['context'] = i

        ret['contexts'] = serialized_contexts
        return ret

    def set_special_attrs(self, attrs, version):
        self.responses = _deserialize_redict(attrs['responses'])
        self.contexts = []
        self.context = None

        if attrs['no_default_response']:
            self.default_response = responder.NoResponse
            del attrs['default_response']

        del attrs['no_default_response']

        for contextdata in attrs['contexts']:
            context = Context()
            context.set_special_attrs(contextdata, version)
            self.contexts.append(context)

        if attrs['context']:
            self.context = self.contexts[attrs['context']]

        del attrs['responses']
        del attrs['contexts']
        del attrs['context']
        return attrs

class Person(LivingItem):
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

        super(Person, self).__init__(prefix, name, **kwargs)

        self.edible = True
        self.inanimate = False
        self.alive = True
        self.prefix = prefix
        self.name = name
        self.size = ItemSize.LARGE
        self.introduction = None
        self.shopping_list = {}
        self.speak_count = 0
        self.script = None
        self.following = False
        self.looking = False
        self.wait_count = 0
        self.tile_id = None
        self.script_pos = 0
        self.task_id = 0
        self.original_location = None
        self.responses = Responder()

        if self.prefix in ['', None]:
            self.prep = self.name
        else:
            self.prep = 'the ' + self.name

    def get_special_attrs(self):
        attrs = {}
        attrs['tile_id'] = self.tile_id
        return attrs

    def set_special_attrs(self, attrs, version):
        self.tile_id = attrs['tile_id']
        del attrs['tile_id']
        return attrs

    def find_item_class(self, classobj):
        """
        Find an item held by this person which is an instance of a specific
        class

        :param classobj: class to look for an instance of
        :return: instance of classobj if found, otherwise None
        """
        for item in self.items:
            if isinstance(item, classobj):
                return item

        return None

    def add_coins(self, value=1):
        """
        Give person some coins

        :param int value: number of coins to add
        """
        coins = self.find_item_class(Coins)
        if not coins:
            coins = Coins(value=value)
            self.add_item(coins)
            return

        coins.value += value

    def on_look(self, player):
        return "It's %s."  % self.name

    def add_shopping_list(self, *item_value_pairs):
        """
        Add the names of items this person is willing to buy from the player if
        the player asks, and the price person is willing to pay for them

        :param item_value_pairs: one or more tuples of the form \
            ``(item_name, value)``, where ``item_name`` is the item name as a \
            string, and ``value`` is an integer representing the price in coins
        """
        for name, value in item_value_pairs:
            self.shopping_list[name] = value

    def clear_shopping_list(self):
        """
        Clear this persons current shopping list
        """
        self.shopping_list.clear()

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
        self.responses.add_default_response(responses)

    def add_response(self, patterns, response):
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
        self.responses.add_response(patterns, response)

    def add_context(self, context):
        """
        Add a discussion context to this person. See
        text_game_maker.chatbot_utils.responder.Context.add_context
        """
        self.responses.add_context(context)

    def add_contexts(self, *contexts):
        """
        Add multiple discussion contexts to this person. See
        text_game_maker.chatbot_utils.responder.Context.add_contexts
        """
        self.responses.add_contexts(*contexts)

    def add_responses(self, *pattern_response_pairs):
        """
        Set multiple pattern/response pairs at once

        :param responses: one or more response pairs, where each pair is a \
            tuple containing arguments for a single ``add_response`` call, \
            e.g. ``add_responses((['cat.*'], ['meow']), (['dog.*], ['woof']))``
        """
        self.responses.add_responses(*pattern_response_pairs)

    def get_response(self, text):
        """
        Get the response this person should speak back to the player, for a
        given input string typed by the player

        :param str text: input string to respond to
        :return: tuple of the form (response, groups) where ``response`` is \
            the response text as a string, and ``groups`` is a tuple of \
            subgroups from the regular expression match (as returned by \
            re.MatchObject.groups), if any, otherwise None.
        """
        response, groups = self.responses.get_response(text)
        if (type(response) == list) or (type(response) == tuple):
            return random.choice(response), groups

        return response, groups

    def die(self, player, msg=None):
        """
        Kill this person, and print a message to inform the player
        of this person's death.

        :param text_game_maker.player.player.Player player: player instance
        :param str msg: message to print informing player of person's death
        """
        if msg is None or msg == "":
            msg = '%s has died.' % self.name

        self.alive = False
        self.name = "%s's corpse" % self.prep
        self.prep = self.name
        self.location = "on the ground"
        player.current.add_person(self)

        utils.game_print(msg)

    def set_introduction(self, msg):
        """
        Set some text for the person to say unprompted, immediately, when the
        player initates a conversation

        :param str msg: text to speak
        """
        self.introduction = msg

    def say(self, msg):
        """
        Speak to the player

        :param msg: message to speak
        :type msg: str
        """

        utils.game_print('%s says:  "%s"' % (self.name, msg))

    def _find_highest_damage_item(self):
        if not self.items:
            return None

        highest = self.items[0]
        for item in self.items[1:]:
            if item.damage > highest.damage:
                highest = item

        return highest

    def _do_attack_player(self, player):
        msg = ""
        # See if we have an item to attack with
        found_item = self._find_highest_damage_item()
        if found_item is None:
            return False

        if found_item.damage > 0:
            msg = messages.attacked_with_weapon_message(self.prep,
                                                           str(found_item))
        else:
            msg = messages.attacked_with_nonweapon_message(self.prep,
                                                              str(found_item))

        utils.game_print(msg)

        player.decrement_health(found_item.damage)

        if player.is_dead():
            utils.game_print("You have been defeated by %s. You are dead."
                             % self.prep)
            player.death()

        return True

    def _do_attacked_by_player(self, player, item):
        if self.is_dead():
            utils.game_print(messages.attack_corpse_message(self.prep, item.name))
            return False

        if item.damage > 0:
            msg = messages.attack_with_weapon_message(self.prep, item.name)
        else:
            msg = messages.attack_with_nonweapon_message(self.prep, item.name)

        utils.game_print(msg)

        self.decrement_health(item.damage)

        if self.is_dead():
            self.die(player)
            return False

        return True

    def _stop_following_player(self, player):
        self.location = self.original_location
        self.looking = False
        self.following = False
        self_tile = tile.get_tile_by_id(self.tile_id)
        self_tile.add_person(self)

    def _start_following_player(self, player):
        self.following = True
        self.original_location = self.location
        self.location = "standing next to you"
        self_tile = tile.get_tile_by_id(self.tile_id)
        self_tile.add_person(self)
        player.schedule_task(self._follow_attack_player, 2)

    def _follow_attack_player(self, player, turns):
        if not self.alive:
            self._stop_following_player(player)
            return

        self_tile = tile.get_tile_by_id(self.tile_id)

        # Waiting for player to emerge
        if self.looking:
            if self_tile is player.current:
                # Player emerged
                self.looking = False
                self.wait_count = 0
                self._do_attack_player(player)

            else:
                if not player.current.is_connected_to(self_tile):
                    # Player exited to a non-adjacent tile
                    self._stop_following_player(player)
                    return

                if self.wait_count >= MAX_PLAYER_WAIT_COUNT:
                    utils.game_print("%s gets bored of waiting, and forgets "
                        "about you." % self.prep)
                    self._stop_following_player(player)
                    return

                self.wait_count += 1
                utils.game_print("%s is still waiting for you to emerge from "
                    "darkness." % self.prep)

        elif self_tile != player.current:
            # Player moved to a different tile
            if not player.current.is_connected_to(self_tile):
                # Player moved to a non-adjacent tile
                utils.game_print("%s is unable to follow you." % self.prep)
                self._stop_following_player(player)
                return

            if player.can_see():
                # We can still see the player, follow them
                player.current.add_person(self)
                utils.game_print("%s follows you." % self.prep)
            else:
                # Can't see player, wait outside
                utils.game_print("%s does not follow you into the darkness,"
                    " but stands waiting for you to emerge" % self.prep)
                self.looking = True

            if not self.looking:
                self._do_attack_player(player)

        player.schedule_task(self._follow_attack_player, 1)

    def on_attack(self, player, item):

        if not self._do_attacked_by_player(player, item):
            return

        # If already following player, the callback will handle attacking the
        # player so no need to attack here
        if self.following:
            return

        if not self._do_attack_player(player):
            utils.game_print(messages.attack_not_returned_message(self.prep))
            return

        # Start following player, if not already following
        self._start_following_player(player)

    def on_eat(self, player, word):
        if self.alive:
            utils.game_print(messages.eat_living_person_message(self.prep))
            player.injure(10)
            return

        super(Person, self).on_eat(player, word)

    def on_speak(self, player):
        if self.following:
            utils.game_print("%s is not interested in talking right now."
                % self.prep)
            return False

        speech = ' '
        prompt = 'talking to %s (say nothing to exit):' % self.name

        if self.introduction:
            self.say(self.introduction)

        while speech != '':
            speech = utils.read_line_raw(prompt).strip()
            if speech == '':
                break

            response, _ = self.get_response(speech)
            if response == responder.NoResponse:
                self.say("my man")
            elif callable(response):
                response(self, player)
            else:
                self.say(response)

            utils.flush_waiting_prints()
