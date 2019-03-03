STANDARD_GREETINGS = [
    [(
        ["hey.*|yo.?|hello.*|hi.?|greetings.*|howdy.*"],
        ["Hello.", "Nice to meet you.", "Howdy."]
    )],

    [(
        ["how('?s it (going|hanging)| are you| do you do| are things).*",
            "what'?s up\??.*"],
        ["Yes, quite well. Yourself?", "Very well, thank you. And you?",
            "I'm good. What about you?"]
    ),
    (
        ["((i'?m|i am) )?((pretty|very) )?(good|awesome|great|ok|alright).*"],
        ["That's nice to hear.", "Good, I'm glad.", "Good.", "That's good."]
    ),
    (
        ["((i'?m|i am) )?(not (so )?(good|great)|bad|terrible|awful).*"],
        ["Oh, that's a shame.", "Oh, dear.", "Sorry to hear that.",
            "That's not good."]
    )]
]
