import pytest

import text_game_maker.item
import text_game_maker.person


@pytest.fixture
def item_knife():
    return text_game_maker.item.Item(
        prefix="a",
        name="knife",
        description="stuck on the floor",
        value=3,
        on_take="call_back_knife"
    )


@pytest.fixture
def item_iphone():
    return text_game_maker.item.Item(
        prefix="an",
        name="iPhone",
        description="with its screen shattered",
        value=30,
        on_take="call_back_iphone"
    )


@pytest.fixture
def person_calvin(item_iphone):
    return text_game_maker.person.Person(
        name="Calvin",
        description="being cool as usual",
        on_speak="call_back_on_speak",
        items={item_iphone.name: item_iphone},
        alive=True,
        coins=100
    )
