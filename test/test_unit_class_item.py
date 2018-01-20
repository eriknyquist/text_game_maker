def test_constructor(item_knife):
    assert item_knife.prefix == "a"
    assert item_knife.name == "knife"
    assert item_knife.description == "stuck on the floor"
    assert item_knife.value == 3
    assert item_knife.on_take == "call_back_knife"


def test_setters(item_iphone):
    item_iphone.set_prefix("a broken")
    item_iphone.set_name("iPhone 4")
    item_iphone.set_description("floating mid air")
    item_iphone.set_value(40)
    item_iphone.set_on_take("call_back_new")

    assert item_iphone.prefix == "a broken"
    assert item_iphone.name == "iPhone 4"
    assert item_iphone.description == "floating mid air"
    assert item_iphone.value == 40
    assert item_iphone.on_take == "call_back_new"
