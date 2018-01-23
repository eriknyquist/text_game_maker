import text_game_maker

def _default_on_look(item, player):
    return "%s %s." % (item.prefix, item.name)

class Item(object):
    """
    Base class for collectable item
    """

    def __init__(self, prefix, name, location=None, value=None,
            on_take=None, on_look=None):
        """
        Initialises an Item instance

        :param str prefix: Generally either "a" or "an"
        :param str name: Item name, e.g. "apple"
        :param str location: Item location, e.g. "on the floor"
        :param int value: Item value in coins
        :param on_take: on_take callback function (see \
            text_game_maker.item.Item.set_on_take description for more\
            details)
        :param on_look: on_look callback function (see \
            text_game_maker.item.Item.set_on_look description for more\
            details)
        """

        self.value = value
        self.name = name
        self.prefix = prefix
        self.location = location
        self.on_take = on_take

        if on_look:
            self.on_look = on_look
        else:
            self.on_look = _default_on_look

    def set_prefix(self, prefix):
        """
        Set item prefix word (usually 'an' or 'a')
        """

        self.prefix = prefix

    def set_name(self, name):
        """
        Set the name of this item

        :param str name: object name
        """

        self.name = name

    def set_location(self, desc):
        """
        Set the location description of the item, e.g. "on the floor". Items
        with the same location description will automatically be grouped when
        described to the player, e.g."an apple, a key and a knife are on the
        floor"

        :param str desc: item location description
        """

        self.location = desc

    def set_value(self, value):
        """
        Set the value of this item in coins

        :param int value: item value in coins
        """

        self.value = value

    def set_on_look(self, callback):
        """
        Set callback function to be invoked when player looks at/inspects this
        item. Callback should accept one parameter, and return a string:

            def callback(item, player)
                return '%s %s.' % (item.prefix, item.name)

            Callback parameters:

            * *item* (text_game_maker.item.Item): item being looked at
            * *player* (text_game_maker.player.Player): player instance
            * *Return value* (str): text to be printed to player

        :param callback: callback function
        """

        text_game_maker._verify_callback(callback)
        self.on_look = on_look

    def set_on_take(self, callback):
        """
        Set callback function to be invoked when player attempts to add this
        item to their inventory. Callback should accept one parameter:

            def callback(player)
                pass

            Callback parameters:

            * *player* (text_game_maker.player.Player): player instance

        :param callback: callback function
        """

        text_game_maker._verify_callback(callback)
        self.on_take = callback

    def __str__(self):
        return '%s %s' % (self.prefix, self.name)
