import random

def no_inventory_item_message(item_name):
    msgs = [
        "No {0} in your inventory.",
        "You are not carrying anything that could be described as '{0}'",
        "'{0}' does not describe anything in your inventory.",
        ""
    ]

    index = random.randrange(len(msgs))
    return msgs[index].format(item_name)

def no_item_message(item_name):
    msgs = [
        "There is no {0} here.",
        "The {0} you're talking about doesn't seem to be anywhere around here.",
        "No {0} can be found here.",
        "No {0} around here."
    ]

    index = random.randrange(len(msgs))
    return msgs[index].format(item_name)

def container_too_small_message(item_name, container_name):
    msgs = [
        "The {0} will not fit inside the {1}.",
        "Try as you might, you cannot make the {0} fit inside the {1}.",
        "The {0} is too large to fit inside the {1}.",
        "Exhausted after many attempts, you reluctantly consider the "
        "possibility that the {0} will not fit inside the {1}.",
        "The {0}, alas, will never fit inside the {1}.",
        "Despite your most earnest efforts, the {0} remains mostly not inside "
        "the {1}."
    ]

    index = random.randrange(len(msgs))
    return msgs[index].format(item_name, container_name)

