import sys
import copy

import text_game_maker
from text_game_maker import map_builder
from text_game_maker.base import GameEntity

class Person(GameEntity):
    """
    Represents a person that the player can interact with
    """

    def __init__(self, name, location, items=[], alive=True, coins=50):
        """
        Initialises a Person instance

        :param str name: name of Person, e.g. "John"
        :param str description: location description of Person, e.g.\
            "squatting in the corner"
        :param bool alive: Initial living state of person .If True, person will\
            be alive. If false, person will be dead
        :param int coins: Number of coins this person has
        :param list items: List of Items held by this person
        """

        super(Person, self).__init__()

        self.inanimate = False
        self.edible = True
        self.energy = 100

        self.name = name
        self.prep = name

        self.location = location
        self.alive = alive
        self.coins = coins
        self.items = items

    def on_look(self, player):
        return "It's %s."  % self.name

    def __str__(self):
        return self.name

    def die(self, player, msg=None):
        """
        Kill this person, and print a message to inform the player
        of this person's death.

        :param text_game_maker.player.Player player: player instance
        :param str msg: message to print informing player of person's death
        """

        p = map_builder._find_best_match_person_index(player, self.name)
        p.delete()

        self.alive = False
        self.name = "%s's corpse" % self.name
        self.prep = self.name
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

        self.items.append(item)

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

        equipped = player.inventory['equipped'][0]
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
            self.items.append(equipped)
            equipped.delete()
            equipped.home = self.items
            text_game_maker.game_print("Sale completed.")
            return equipped

        text_game_maker.game_print("Sale cancelled")
        return None
