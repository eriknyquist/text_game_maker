.. |projectname| replace:: text_game_maker

Text Adventure Game Maker
-------------------------

|projectname| is a framework for building simple text-based games. Here is a
simple game made with |projectname|:

.. code:: python

    import text_game_maker
    from text_game_maker.item import Item
    from text_game_maker.person import Person
    from text_game_maker.map_builder import MapBuilder

    # callback function for locked room: each time player attempts to enter
    # the locked room, this callback function will be called
    def room_enter_callback(player, source, dest):
        if player.has_equipped('brass key'):
            # if 'brass key' is equipped, delete from player's inventory ...
            player.delete_equipped()

            # ... and unlock the destination tile
            dest.set_unlocked()

        return True

    builder = MapBuilder()

    # First room, player will start here
    builder.set_name('a dark cellar')
    builder.set_description('in a dark, moist cellar with no windows')
    builder.add_item(Item("a", "brass key", "on the floor", 8))

    # New room to the west
    builder.move_west()
    builder.set_name('a well-lit room')
    builder.set_description('a bright, dry room with many windows')

    # This room is locked-- need the brass key to get in
    builder.set_locked()

    # Add enter callback so tile can be unlocked. Callback will
    # be invoked when player attempts to enter this tile.
    builder.set_on_enter(room_enter_callback)

    # Start reading player input and run the game
    builder.run_game()

Features overview
=================

* Write simple python code to build a 2D grid-based "world" that a player
  can navigate through using north/south/east/west commands, e.g. "go west"

* Add items that a player can collect, and other game characters that a player
  can interact with. You can also add custom code to control what happens
  when a player interacts with an item or another game character.

* Built-in parser for player input, with variants of common words & phrases for
  controlling the player, e.g. "take key", "get key", "pick up key"

* Commands can be chained in a single line using a comma, e.g.
  "pick up apple, equip apple, speak to alan"

* Names of items, game characters or directions entered by the player can
  be very flexible, to save players from typing the full names all the time.
  For example, to add an item called "metal key" to the player's inventory,
  the player could enter any of (but not limited to): "take metal key",
  "take key", "pick up key", "get key". Even "get m" or "get k" will work, as
  long as there are no other items in the area that it would clash with.

  Similarly, a direction to move the player west could be any of (but not
  limited to): "w", "west", "go west", "go w", "move west", "walk west"

Documentation
=============

`doc/build/html/index.html <http://htmlpreview.github.io/?https://github.com/eriknyquist/text_game_maker/blob/master/doc/build/html/index.html>`_
