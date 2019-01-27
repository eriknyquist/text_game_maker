import sys
import copy

import text_game_maker
from text_game_maker.game_objects.base import GameEntity
from text_game_maker.utils import utils

class Person(GameEntity):
    """
    Represents a person that the player can interact with
    """

    def __init__(self, name, location, items=[], alive=True):
        """
        Initialises a Person instance

        :param str name: name of Person, e.g. "John"
        :param str description: location description of Person, e.g.\
            "squatting in the corner"
        :param bool alive: Initial living state of person .If True, person will\
            be alive. If false, person will be dead
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

        for item in items:
            self.add_item(item)

    def on_look(self, player):
        return "It's %s."  % self.name

    def __str__(self):
        return self.name

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
