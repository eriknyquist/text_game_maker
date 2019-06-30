import random

def _randmsg(choices, *args):
    choice = random.choice(choices)
    return choice.format(*args)

def attack_corpse_message(target_name, item_name):
    return _randmsg([
        "You strike {0} with your {1}.",
        "You attempt to fight {0} with your {1}. Even the {1} is embarrassed.",
        "You attack {0} with your {1}. {0}, naturally, makes no attempt to "
            "fend you off.",
        "Despite the fact that {0} is completely helpless, and indeed poses no "
            "immediate danger, you attack {0} ferociously with your {1}, which "
            "I suppose makes you feel good about yourself or something."
    ], target_name, item_name)

def attack_with_weapon_message(target_name, item_name):
    return _randmsg([
        "You attack {0} with your {1}, and your attack is successful, wounding "
            "{0}.",
        "You strike {0} with your {1}, hitting your mark and injuring {0}.",
        "Clutching your {1}, you strike {0} with great force and precision, "
            "who stumbles and cries out in pain.",
        "Brandishing your {1}, you attack {0}, who fails to evade you and "
            "received the full force of your attack."
    ], target_name, item_name)

def attack_with_nonweapon_message(target_name, item_name):
    return _randmsg([
        "You strike {0} with your {1}, but it doesn't seem terribly effective.",
        "You attack {0} with your {1}, but {0} appears to absorb your blows "
            "without much consequence.",
        "Stabbing wildly with your {1}, you assault {0}, who seems rather "
            "annoyed but not as wounded as you had hoped.",
        "Brandishing your {1}, you attack {0} with great speed and precision, "
            "causing {0} to exclaim in mild discomfort."
    ], target_name, item_name)

def attacked_with_weapon_message(target_name, item_name):
    return _randmsg([
        "{0} attacks you visciously with {1}, causing you to stumble.",
        "{0} lunges at you with {1} in hand, attacking and wounding you.",
        "{0}, grasping {1} with both hands, strikes you and injures you.",
        "{0} assaults you, striking you with {1} and injuring you."
    ], target_name, item_name)

def attacked_with_nonweapon_message(target_name, item_name):
    return _randmsg([
        "{0} attacks you, striking you with {1}, but this does not hurt "
            "you.",
        "Desperately, {0} assaults you with a {1}, which you manage to endure "
            "without lasting discomfort.",
        "{0} attacks you ferociously with a {1}, but this is not very "
            "effective and you emerge unscathed.",
        "{0} strikes you with {1}, which stings a bit but doesn't quite injure "
            "you as {0} probably hoped."
    ], target_name, item_name)

def attack_not_returned_message(target_name):
    return _randmsg([
        "{0} has no weapon to fight back with, and cowers under your blows."
    ], target_name)

def attack_inanimate_object_message(target_name, weapon_name):
    return _randmsg([
        "You attack the {0}, heroically brandishing your {1}. The {0} accepts "
            "your blows gratefully, unmoving, mocking you.",
        "You strike the {0} with your {1}. Nothing happens.",
        "With great fervour, you set about the {0} with your {1}. The {0}, "
            "to your significant annoyance, remains unperturbed and does not "
            "fight back.",
        "You attack the {0} with your {1}. This is pointless, and frankly "
            "stupid, but also rather entertaining to watch.",
        "You attack the {0} with your {1}, and the {0} is defeated with ease, "
            "offerring no resistance whatsoever. Good job. Who's a formidable "
            "warrior? You are!",
        "You approach the {0}, {1} in hand. The {0} transforms into a laser "
            "unicorn and burns your face off (nope, just kidding, it's a {0}. "
            "You're fine)."
    ], target_name, weapon_name)

def bad_taste_message():
    return _randmsg([
        "It doesn't taste great.",
        "You have tasted better.",
        "It's not very good.",
        "It does not taste good."
    ])

def eat_living_person_message(name):
    return _randmsg([
        "{0} doesn't appreciate your advances, and bites back.",
        "You have a chew on {0}. {0} finds this unpleasant and kicks you in the"
            " groin.",
        "You try to eat {0}, but {0} is a bit big and moves around a lot. "
            "Eventually, {0} is no longer entertained and sucker-punches you.",
        "You attempt to eat {0}, but {0} does not want to co-operate and "
            "responds rather violently.",
        "Foolishly, you try to take bite out of {0}, regretting it immediately "
            "as {0} kicks you hard in the shins.",
        "You try to eat {0}. This was dumb. {0} attacks you, landing several "
            "punches on your face."
    ], name)

def dark_stumble_message():
    return _randmsg([
        "You stumble about blindly in the darkness, going nowhere.",
        "You can't see where you're going. It is too dark.",
        "You try to feel your way along in the dark, but it's hopeless. You "
        "have no idea where you're going."
    ])

def dark_search_message():
    return _randmsg([
        "You grasp out into the darkness, finding nothing to grab",
        "You can't see anything right now, it is too dark.",
        "You stretch out your hands and feel around in the darkness, searching,"
        " to no avail. You won't be able to find anything without some light."
    ])

def dontknow_message(ambiguous_action):
    return _randmsg([
        "Don't know how to {0}.",
        "Not sure how to {0}.",
        "If I knew how to {0}, I'd do it for you. But I don't. So I can't.",
        "I asked everyone if they know how to {0}. Nobody knows.",
        "I'd love to {0}, but I don't know how",
        "Look, I don't know how to {0}, alright? We got a bunch of people "
        "back here working on it for ya, and I'll let you know if there are any"
        " breakthroughs, but right now we got nothing. OK? Sorry.",
        "I'm afraid I don't know how to {0}. I'll get someone working on that "
        "right away."
    ], ambiguous_action)

def badword_message():
    return _randmsg([
        "I refuse to respond to such language.",
        "Does your mother know that you speak like that?",
        "Wash your mouth out and try again.",
        "Where did you learn to talk like that?",
        "Never have I heard such language!",
        "I'll thank you to watch your language.",
        "We'll resume the game when you've regained your manners, you "
        "shit-mouthed fuck."
    ])

def suicide_message():
    return _randmsg([
        "You punch yourself in the face, very hard, serveral times, until you "
        "manage to knock youself out. Several minutes later, you awaken. You "
        "repeat this whole routine quite a few times, until finally you do not "
        "awaken. You have punched yourself to death.",
        "You hold your breath for a very long time and suffocate.",
        "You strangle yourself to death with your socks.",
        "You lie down peacefully on the ground for several days until "
        "starvation and thirst bring you to a slow and painful death",
        "Dropping to your knees, you smash your face and head into the "
        "ground repeatedly until your brain no longer works. You are dead.",
        "You squat down low, poised like a cat. Turning your eyes towards the sky, "
        "you straighten your legs and spring suddenly upwards, rising several feet "
        "into the air. With great effort, you twist and roll your entire body in the "
        "air so that you are now upside-down with the top of your head facing the "
        "ground. You land squarely on your head with a loud crack, as your body "
        "crumples like an accordion and your spine snaps in several places. You are very dead."
    ])

def gross_action_message(gross_action):
    return _randmsg([
        "You {0}. How lovely.",
        "You force us all to watch while you {0}.",
        "{0}? Really?",
        "You {0}. It looks disgusting.",
        "You {0}, like a filthy animal.",
        "For no apparent reason, you {0}. Yuck.",
        "OK, we'll all look away while you {0}.",
        "You {0}. Nearby, somewhere, a bird stops singing.",
        "Despite knowing that all your dead relatives may be watching, "
        "you {0}.",
        "With a very stupid expression on your face, you {0}."
    ], gross_action)

def sleep_message(sleepword):
    return _randmsg([
        "You {0} for several hours.",
        "You curl up on the ground and {0}. Several hours later, you awake.",
        "For some unknown reason, and despite being a fictional character who "
        "does not need sleep and who lives inside a game that does not require"
        " you to sleep, you {0}.",
        "For what we're sure must be good reasons, you {0} instead of actually"
        " doing something.",
        "Sure, you go ahead and {0}. We'll just set up the next bit of the game"
        " while you rest."
    ], sleepword)

def nonsensical_action_message(nonsensical_action):
    return _randmsg([
        "How can you {0}?",
        "Unsure how to {0}, you cry.",
        "You want to {0}. Oh, how you yearn for it! But you cannot figure out "
        "how to {0}.",
        "{0}? How do you plan on doing that?",
        "You try very hard to {0}, to no avail.",
        "All of us back here think it's pretty funny that you tried to {0}.",
        "Remember that time you tried to {0}? How we laughed at you...",
        "I told everyone that you tried to {0}. They all think you're stupid.",
        "You try to {0}. It looks pretty funny."
    ], nonsensical_action)

def burn_combustible_message(item_name):
    return _randmsg([
        "You set the {0} alight and watch it burn until it is nothing but a "
        "smouldering pile of ashes.",
        "You burn the {0}. The flames consume and destroy the {0}.",
        "You set the {0} on fire, and it burns until there is nothing left.",
        "You set fire to the {0}. Predictably, it burns until only ashes remain."
        "You set fire to the {0}. It burns away to nothing.",
        "You set a flame to the {0}, and watch as it slowly burns. When the "
        "flames die there is nothing left"
    ], item_name)

def burn_noncombustible_message(item_name):
    return _randmsg([
        "You try to burn the {0}, but it doesn't really catch.",
        "You try your best to set the {0} on fire, but it will not burn.",
        "Despite your best efforts, the {0} cannot be set alight.",
        "You try burning the {0}, but it will not take the flame.",
        "You try to burn the {0}. You can't.",
        "You hold a flame up to the {0} for quite a while. The flame will not "
        "transfer to the {0}.",
    ], item_name)

def no_inventory_item_message(item_name):
    return _randmsg([
        "No {0} in your inventory.",
        "You are not carrying anything that could be described as '{0}'",
        "'{0}' does not describe anything in your inventory.",
        "We all looked really hard but we couldn't find anything called '{0}' "
        "in your inventory.",
        "Nothing called '{0}' in your inventory.",
        "There is nothing in your inventory called '{0}'.",
    ], item_name)

def no_item_message(item_name):
    return _randmsg([
        "There is no {0} here.",
        "The {0} you're talking about doesn't seem to be anywhere around here.",
        "No {0} can be found here.",
        "No {0} around here.",
        "I asked everyone if they've seen something called '{0}'. Nobody has "
        "seen it.",
        "I looked really hard but I can't find any {0}."
    ], item_name)

def strange_action_message(strange_action):
    return _randmsg([
        "You {0}. It looks funny.",
        "I guess we'll just stop the whole game here while you {0}.",
        "Apparently, you {0}.",
        "You {0}, for some reason.",
        "Uh... OK, sure, you {0}.",
    ], strange_action)

def pointless_action_message(action):
    return _randmsg([
        "Why would you want to {0}?",
        "There is no reason to {0}.",
        "This would be pointless.",
        "You would not gain anything from this.",
        "This is not a useful thing to do."
    ], action)

def container_too_small_message(item_name, container_name):
    return _randmsg([
        "{0} will not fit inside {1}.",
        "Try as you might, you cannot make {0} fit inside {1}.",
        "{0} is too large to fit inside {1}.",
        "Exhausted after many attempts, you reluctantly consider the "
        "possibility that {0} will not fit inside {1}.",
        "{0}, alas, will never fit inside {1}.",
        "Despite your most earnest efforts, {0} remains mostly not inside {1}.",
        "Fitting {0} inside {1} is impossible."
    ], item_name, container_name)
