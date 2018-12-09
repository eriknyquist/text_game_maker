import sys
import messages

import text_game_maker

class GameEntity(object):
    """
    Base class for anything that the player can interact with in the
    game, like usable items, food, people, etc
    """

    def __init__(self):
        # Things are inanimate by default
        self.inanimate = True

        # Most things are....
        self.combustible = True

        # Things are not edible by default
        self.edible = False

        # Things are not alive by default
        self.alive = False

        # How much energy player gains by consuming this object
        self.energy = 0

        # How much health player loses if damaged by this object
        self.damage = 0

        # How much money player gets for selling this item
        self.value = 0

        # Name of this object
        self.name = None

        # Name of the object + any preceding word required when referring to
        # this object as a definite article, if applicable; e.g., for an
        # inanimate object, like "hammer" this will nearly always be
        # "the hammer", as in "the hammer fell on the floor". For a person, like
        # "John", this will be the same string as the name, just "John", as in
        # "John fell on the floor"
        self.prep = None

        # Ref. to the location list that this Item instance lives inside;
        # required for the delete() method
        self.home = None

        # Items contained inside this item (if item is a container)
        self.items = []

        # Size of object (for putting inside containers)
        self.size = 1

        # Singluar verb e.g. "the key is on the floor", or plural e.g.
        # "the coins are on the floor"
        self.verb = "is"

    def is_container(self):
        return False

    def add_item(self, item):
        item.move(self.items)

    def add_items(self, items):
        for item in items:
            item.move(self.items)

    def add_to_player_inventory(self, player):
        return player.inventory.add_item(self)

    def delete(self):
        if self.home:
            del self.home[self.home.index(self)]
            self.home = None

    def move(self, location):
        location.append(self)
        self.delete()
        self.home = location

    def on_burn(self, player):
        if self.home is player.inventory.items:
            text_game_maker.game_print("The %s is in your inventory. You "
                "shouldn't burn things in your inventory because your bag "
                "would catch fire." % self.name)
            return

        if self.combustible:
            msg = messages.burn_combustible_message(self.name)
            self.delete()
        else:
            msg = messages.burn_noncombustible_message(self.name)

        text_game_maker.game_print(msg)

    def on_speak(self, player):
        return "%s says nothing." % self.prep

    def on_take(self, player):
        return True

    def on_look(self, player):
        return "It's a %s" % self.name

    def on_eat(self, player, word):
        if self.alive:
            msg = "%s is still alive. You cannot eat living things." % self.name
        elif self.edible:
            msg = "You %s %s and gain %d energy point" % (word, self.prep,
                self.energy)

            if (self.energy == 0) or (self.energy > 1):
                msg += "s"

            player.increment_energy(self.energy)
            self.delete()

        else:
            msg = ("You try your best to %s %s, but you fail, and injure "
                "yourself. You have lost %d health points." % (word, self.prep,
                self.damage))

            if player.health <= self.damage:
                text_game_maker._wrap_print(msg + " You are dead.")
                player.death()
                sys.exit()

            player.decrement_health(self.damage)

        return msg
