import random

def _randmsg(choices, *args):
    choice = random.choice(choices)
    return choice.format(*args)

def badword_message():
    return _randmsg([
        "I refuse to respond to such language.",
        "Does your mother know that you speak like that?",
        "Wash your mouth out and try again.",
        "Where did you learn to talk like that?",
        "Never have I heard such language!",
        "I'll thank you to watch your language."
    ])

def suicide_message():
    return _randmsg([
        "You kill yourself.",
        "You hold your breath for a very long time and suffocate.",
        "You strangle yourself to death with your socks.",
        "You lie down peacefully on the ground for several days until "
        "starvation and thirst bring you to a slow and painful death",
        "Dropping to your knees, you smash your face and head into the "
        "hard ground repeatedly until your brain no longer works. You are dead.",
        "You squat down low, poised like a cat. Turning your eyes towards the sky, "
        "you straighten your legs and spring suddenly upwards, rising several feet "
        "into the air. With great effort, you twist and roll your entire body in the "
        "air so that you are now upside-down with the top of your head facing the "
        "ground. You land squarely on your head with a loud crack, as your body "
        "crumples like an accordion and your spine snaps in several places. You are very dead."
    ])
 
def nonsensical_action_message(nonsensical_action):
    return _randmsg([
        "How can you {0}?",
        "Unsure how to {0}, you cry.",
        "You want to {0}. Oh, how you yearn for it! But you cannot figure out "
        "how to {0}.",
        "{0}? How do you plan on doing that?",
        "You try very hard to {0}, to no avail.",
        "All of us back here think it's pretty funny that you tried to {0}.",
        "Remember that time you tried to {0}? How we laughed at you..."
    ], nonsensical_action)

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
        "Fitting the {0} inside the {1} is impossible."
    ], item_name, container_name)
