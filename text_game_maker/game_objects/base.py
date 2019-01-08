import sys

import text_game_maker
from text_game_maker.messages import messages

class GameEntity(object):
    """
    Base class for anything that the player can interact with in the
    game, like usable items, food, people, etc

    :ivar bool inanimate: defines whether this item is an inanimate object
    :ivar bool combustible: defines whether this item can be destroyed by fire
    :ivar bool scenery: defines whether this item is scenery; an immovable prop\
        in the scene that should be mentioned before smaller interactive items\
        when describing a room, e.g. furniture, architectural features of the\
        room
    :ivar bool edible: defines whether this item is edible
    :ivar bool alive: defines whether this item is currently alive
    :ivar int energy: defines hjow much energy player gains by consuming this\
        item
    :ivar int damage: defines how much health player loses if damaged by this\
        item

    :ivar int value: defines how much money player will make by selling this\
        item
    :ivar str name: name that this item will be referred to as in the game\
        (e.g. "metal key")
    :ivar str prefix: preceding word required when mentioning item, e.g. "a"\
        for "a metal key", and "an" for "an apple"
    :ivar list home: list that this Item instance lives inside; required for\
        the deleting/moving items within the game world
    :ivar bool is_container: defines whether this item can contain other items
    :ivar int capacity: number of items this item can contain (if container)
    :ivar list items: items contained inside this item (if container)
    :ivar int size: size of this item; containers cannot contain items with a\
        larger size than themselves
    :ivar str verb: singluar verb e.g. "the key is on the floor", or plural\
        e.g. "the coins are on the floor"
    """

    def __init__(self):
        self.inanimate = True
        self.combustible = True
        self.scenery = False
        self.edible = False
        self.alive = False
        self.energy = 0
        self.damage = 0
        self.value = 0
        self.prefix = "a"
        self.name = None
        self.prep = None
        self.home = None
        self.is_container = False
        self.capacity = 0
        self.items = []
        self.size = 1
        self.verb = "is"

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
            if self.is_container:
                items = text_game_maker.get_all_contained_items(self,
                    lambda x: not x.combustible)

                for item in items:
                    if item.combustible:
                        item.delete()
                    else:
                        item.location = self.location
                        player.current.add_item(item)

            msg = messages.burn_combustible_message(self.name)
            self.delete()
        else:
            msg = messages.burn_noncombustible_message(self.name)

        text_game_maker.game_print(msg)

    def on_read(self, player):
        msg = 'read the %s' % self.name
        text_game_maker._wrap_print(messages.nonsensical_action_message(msg))

    def on_speak(self, player):
        text_game_maker.game_print("%s says nothing." % self.prep)

    def on_take(self, player):
        return True

    def on_look(self, player):
        text_game_maker.game_print("It's a %s" % self.name)

    def on_look_under(self, player):
        text_game_maker.game_print("There is not much to see under the %s"
            % self.name)

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
