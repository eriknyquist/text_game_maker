
class Item(object):
    """
    Base class for collectable item
    """

    def __init__(self, prefix, name, description=None, value=None,
            on_take=None):
        """
        Initialises an Item instance

        :param str prefix: Generally either "a" or "an"
        :param str name: Item name, e.g. "apple"
        :param str description: Item description, e.g. "on the floor"
        :param int value: Item value in coins
        :param on_take: callback function to invoke when player attempts to\
            add this item to their inventory
        """

        self.value = value
        self.name = name
        self.prefix = prefix
        self.description = description
        self.on_take = on_take

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

    def set_on_take(self, callback):
        """
        Set callback function to be invoked when player attempts to add this
        item to their inventory. Callback should accept one argument:

            def callback(player)
                pass

        * *player* (text_game_maker.player.Player): player instance

        :param callback: callback function
        """

        self.on_take = on_take

    def __str__(self):
        return '%s %s is %s' % (self.prefix, self.name, self.description)

