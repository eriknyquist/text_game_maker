import sys
import copy

import text_game_maker
from text_game_maker import map_builder

def _default_on_look(person, player):
    return "It's %s."  % person.name

class Person(object):
    """
    Represents a person that the player can interact with
    """

    def __init__(self, name, location, on_speak=None, on_look=None,
            items={}, alive=True, coins=50):
        """
        Initialises a Person instance

        :param str name: name of Person, e.g. "John"
        :param str description: location description of Person, e.g.\
            "squatting in the corner"
        :param on_speak: on_speak callback (see \
            text_game_maker.person.Person.set_on_speak description for more\
            details)
        :param on_look: on_look callback (see \
            text_game_maker.person.Person.set_on_look description for more\
            details)
        :param bool alive: Initial living state of person .If True, person will\
            be alive. If false, person will be dead
        :param int coins: Number of coins this person has
        :param dict items: Items held by this person, where each dict item is\
            of the form {Item.name: Item}
        """

        self.name = name
        self.location = location
        self.alive = alive
        self.coins = coins
        self.items = items
        self.on_speak = on_speak

        if on_look:
            self.on_look = on_look
        else:
            self.on_look = _default_on_look

    def __str__(self):
        return self.name

    def die(self, player, msg=None):
        """
        Kill this person, and print a message to inform the player
        of this person's death.

        :param text_game_maker.player.Player player: player instance
        :param str msg: message to print informing player of person's death
        """

        p, loc, i = map_builder._find_closest_match_person_index(player,
            self.name)
        del player.current.people[loc][i]

        if not player.current.people[loc]:
            del player.current.people[loc]

        self.alive = False
        self.name = "%s's corpse" % self.name
        self.location = "on the floor"
        player.current.add_person(self)

        if msg is None or msg == "":
            msg = '%s has died.' % self.name

        text_game_maker.game_print(msg)

    def add_item(self, item):
        """
        Add an item to this person's inventory

        :param text_game_maker.item.Item item: item to add
        """

        self.items[item.name] = item

    def set_on_speak(self, callback):
        """
        Set a function to be invoked whenever the player talks to this person.
        The provided function should accept two parameters, and return a string:

            def callback(person, player):
                pass

            Callback parameters:

            * *person* (text_game_maker.person.Person): Person instance
            * *player* (text_game_maker.player.Player): Player instance
            * *Return value* (str): the text to be spoken in response to the
              player

        :param callback: Callback function to be invoked whenever player\
            speaks to this person
        """

        text_game_maker._verify_callback(callback)
        self.on_speak = callback

    def set_on_look(self, callback):
        """
        Set callback function to be invoked when player looks at/inspects this
        person. Callback should accept two parameters, and return a string:

            def callback(person, player)
                return 'It's %s!' % person.name

            Callback parameters:

            * *person* (text_game_maker.person.Person): person being looked at
            * *player* (text_game_maker.player.Player): player instance
            * *Return value* (str): text to be printed to player

        :param callback: callback function
        """

        text_game_maker._verify_callback(callback)
        self.on_look = on_look

    def is_alive(self):
        """
        Test if this person is alive

        :return: True if this person is alive, otherwise false
        :rtype: bool
        """

        return self.alive

    def say(self, msg):
        """
        Speak to the player

        :param msg: message to speak
        :type msg: str
        """

        text_game_maker.game_print('%s says:  "%s"' % (self.name, msg))

    def buy_equipped_item(self, player):
        """
        Ask player to buy equipped item. Expects player to have something
        equipped (so check before uing this method).

        If player's equipped item costs more coins than this person has, the
        person will automatically ask if the player will accept the lower
        amount, and can still buy the item if the player says yes.

        :param player: player object
        :type player: text_game_maker.player.Player

        :return: Returns the item if sale was successful, None otherwise
        :rtype: text_game_maker.item.Item
        """

        equipped = player.inventory_items['equipped']
        cost = equipped.value
        msg = "Ah, I see you have %s %s." % (equipped.prefix, equipped.name)

        if self.coins >= cost:
            msg += " I would like to buy it for %d coins." % cost
        else:
            msg += (" I would like to buy it from you,\n"
                    "but I only have %d coins. Will you accept that price\n"
                    "instead?" % self.coins)
            cost = self.coins

        self.say(msg)

        ret = text_game_maker.ask_yes_no("sell %s for %d coins?"
            % (equipped.name, cost))

        if ret < 0:
            return None
        elif ret:
            # Transfer money
            player.coins += cost
            self.coins -= cost

            # Transfer item
            equipped_copy = copy.deepcopy(equipped)
            self.items[equipped_copy.name] = equipped_copy

            player.delete_equipped()
            text_game_maker.game_print("Sale completed.")
            return equipped_copy

        text_game_maker.game_print("Sale cancelled")
        return None
