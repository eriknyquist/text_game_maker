from text_game_maker.game_objects.generic import Item
from text_game_maker.game_objects.base import GameEntity

class Living(object):
    """
    Base class to represent a living thing with a health metric
    """

    def __init__(self):
        self.max_health = 100
        self.health = self.max_health

    def _dec_clamp(self, curr, val, min_val):
        if curr == min_val:
            return 0

        if curr - val < min_val:
            return min_val + curr

        return val

    def _inc_clamp(self, curr, val, max_val):
        if  curr == max_val:
            return 0

        if curr + val > max_val:
            return max_val - curr

        return val

    def increment_health(self, val=1):
        """
        Increment health

        :param int val: number to increment health by
        """
        inc = self._inc_clamp(self.health, val, self.max_health)
        if inc > 0:
            self.health += inc

        return inc

    def decrement_health(self, val=1):
        """
        Decrement health

        :param int val: number to decrement health by
        """
        dec = self._dec_clamp(self.health, val, 0)
        if dec > 0:
            self.health -= dec

        return dec

    def is_dead(self):
        """
        Check if health has been depleted

        :return: True if health has been depleted, False otherwise
        :rtype: bool
        """
        return self.health == 0

class LivingGameEntity(Living, GameEntity):
    def __init__(self):
        GameEntity.__init__(self)
        Living.__init__(self)

class LivingItem(Living, Item):
    def __init__(self, prefix="", name="", **kwargs):
        Item.__init__(self, prefix, name, **kwargs)
        Living.__init__(self)
