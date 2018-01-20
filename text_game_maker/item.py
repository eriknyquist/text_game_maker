
class Item(object):
    """
    Base class for collectable item
    """

    def __init__(self, prefix, name, description=None, value=None,
            on_take=None, on_look=None):
        """
        Initialises an Item instance

        :param str prefix: Generally either "a" or "an"
        :param str name: Item name, e.g. "apple"
        :param str description: Item description, e.g. "on the floor"
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
        self.description = description
        self.on_take = on_take

        if on_look:
            self.on_look = on_look
        else:
            self.on_look = self._default_on_look

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

    def set_description(self, desc):
        """
        Set the description of the item's location/sitation in the world,
        e.g. "on the floor"

        :param str desc: item description
        """

        self.description = desc

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

        self.on_take = callback

    def _default_on_look(self, item, player):
        return "%s %s." % (self.prefix, self.name)

    def __str__(self):
        return '%s %s is %s' % (self.prefix, self.name, self.description)
