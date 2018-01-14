import sys
import copy
import text_game_maker

class Person(object):
    """
    Represents a person that the player can interact with
    """

    def __init__(self, name, description, on_speak=None, alive=True, coins=50,
            items={}):
        """
        Initialises a Person instance

        :param str name: name of Person, e.g. "John"
        :param str description: description of Person, e.g. "squatting in the\
            corner"
        :param on_speak: on_speak callback (see \
            text_game_maker.person.Person.set_on_speak description for more details)
        :param bool alive: Initial living state of person .If True, person will\
            be alive. If false, person will be dead
        :param int coins: Number of coins this person has
        :param dict items: Items held by this person, where each dict item is\
            of the form {Item.name: Item}
        """

        self.name = name
        self.description = description
        self.on_speak = on_speak
        self.alive = alive
        self.coins = coins
        self.items = items

    def __str__(self):
        return '%s is %s' % (self.name, self.description)

    def die(self, msg=None):
        """
        Kill this person, and print a message to inform the player
        of this person's death.

        :param msg: message to print informing player of person's death
        :type msg: str
        """

        self.alive = False
        self.name = "%s's corpse" % self.name
        self.description = "on the floor"

        if msg is None or msg == "":
            msg = '\n%s has died.' % self.name

        text_game_maker.game_print(msg)

    def set_on_speak(self, callback):
        """
        Set a function to be invoked whenever the player talks to this person.
        The provided function should accept two arguments:

            def callback(person, player):
                pass

            * *person* (text_game_maker.person.Person): Person instance
            * *player* (text_game_maker.player.Player): Player instance
            * *Return value* (str): the text to be spoken in response to the
              player

        :param callback: Callback function to be invoked whenever player\
            speaks to this person
        """

        self.on_speak = callback

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

        lines = msg.splitlines()
        lines[-1] += '"'

        sys.stdout.write('\n%s: "' % self.name)
        sys.stdout.flush()
        text_game_maker.game_print(lines[0])

        for line in lines[1:]:
            sys.stdout.write(' ' * (len(self.name) + 2))
            sys.stdout.flush()
            text_game_maker.game_print(line)

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
        if text_game_maker.ask_yes_no("\n[sell %s for %d coins? (yes/no)] : "
                % (equipped.name, cost)):
            # Transfer money
            player.coins += cost
            self.coins -= cost

            # Transfer item
            equipped_copy = copy.deepcopy(equipped)
            self.items[equipped_copy.name] = equipped_copy

            player.delete_equipped()
            text_game_maker.game_print("\nSale completed.")
            return equipped_copy

        text_game_maker.game_print("\nSale cancelled")
        return None
