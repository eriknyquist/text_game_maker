import random

def _randmsg(choices, *args):
    choice = random.choice(choices)
    return choice.format(*args)

def burn_combustible_message(item_name):
    return _randmsg([
        "You set the {0} alight and watch it burn until it is nothing but a "
        "smouldering pile of ashes.",
        "You burn the {0}. The flames consume and destroy the {0}.",
        "You set the {0} on fire, and it burns until there is nothing left.",
        "You set fire to the {0}. Predictably, it burns until only ashes remain."
    ], item_name)

def burn_noncombustible_message(item_name):
    return _randmsg([
        "You try to burn the {0}, but it doesn't really catch.",
        "You try your best to set the {0} on fire, but it will not burn.",
        "Despite your best efforts, the {0} cannot be set alight.",
        "You try burning the {0}, but it will not take the flame.",
        "You try to burn the {0}. You can't."
    ], item_name)

def no_inventory_item_message(item_name):
    return _randmsg([
        "No {0} in your inventory.",
        "You are not carrying anything that could be described as '{0}'",
        "'{0}' does not describe anything in your inventory.",
        ""
    ], item_name)

def no_item_message(item_name):
    return _randmsg([
        "There is no {0} here.",
        "The {0} you're talking about doesn't seem to be anywhere around here.",
        "No {0} can be found here.",
        "No {0} around here."
    ], item_name)

def container_too_small_message(item_name, container_name):
    return _randmsg([
        "The {0} will not fit inside the {1}.",
        "Try as you might, you cannot make the {0} fit inside the {1}.",
        "The {0} is too large to fit inside the {1}.",
        "Exhausted after many attempts, you reluctantly consider the "
        "possibility that the {0} will not fit inside the {1}.",
        "The {0}, alas, will never fit inside the {1}.",
        "Despite your most earnest efforts, the {0} remains mostly not inside "
        "the {1}.",
        "Fitting the {0} inside the {1] is impossible."
    ], item_name, container_name)
