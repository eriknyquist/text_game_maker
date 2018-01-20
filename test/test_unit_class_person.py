def test_constructor(person_calvin, item_iphone):
    assert person_calvin.name == "Calvin"
    assert person_calvin.description == "being cool as usual"
    assert person_calvin.on_speak == "call_back_on_speak"
    assert person_calvin.items == {item_iphone.name: item_iphone}
    assert person_calvin.alive
    assert person_calvin.coins == 100


def test_setters(person_calvin):
    new_call_back = "new_call_back_on_speak"
    person_calvin.set_on_speak(new_call_back)
    assert person_calvin.on_speak == new_call_back


def test_method_die(person_calvin, capsys):
    message = "Calvin is in heaven."
    person_calvin.die(message)
    out, err = capsys.readouterr()
    assert not person_calvin.alive
    assert not person_calvin.is_alive()
    assert person_calvin.name == "Calvin's corpse"
    assert person_calvin.description == "on the floor"
    assert out == message + '\n'


def test_method_add_item(person_calvin, item_iphone, item_knife):
    person_calvin.add_item(item_knife)
    assert person_calvin.items == {
        item_iphone.name: item_iphone,
        item_knife.name: item_knife
    }


def test_method_say(person_calvin, capsys):
    message = "yada yada"
    person_calvin.say(message)
    out, err = capsys.readouterr()
    assert out == '\nCalvin: "{}"\n'.format(message)

    message = "one\ntwo\nthree"
    message_spaced = "one\n        two\n        three"
    person_calvin.say(message)
    out, err = capsys.readouterr()
    assert out == '\nCalvin: "{}"\n'.format(message_spaced)


def test_buy_equipped_item(person_calvin):
    # TODO
    assert True
