.. |projectname| replace:: text_game_maker

Text Adventure Game Maker
-------------------------

|projectname| is a framework for building simple text-based games.

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
