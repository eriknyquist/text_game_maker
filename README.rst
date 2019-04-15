.. |projectname| replace:: text_game_maker

Text Adventure Game Maker
-------------------------

.. contents:: Contents

|projectname| is a framework for building simple text-based games. Supports
Python 2 and 3 on Linux and Windows (tested on Debian and Windows 10).

Features
========

* Builder API pattern that implements a 2D tile-based grid system for building
  maps and creating game objects with a few lines of Python.

* Flexible object model for defining game objects and NPCs. Many useful game
  objects and behaviours are pre-defined so you can start making a game straight
  away, but these classes are easy to extend if you need to implement your own
  custom game objects.

* NPCs that you can actually speak to, like a chatbot. ``text_game_maker``
  NPCs allow you to define custom responses and contexts for discussions using
  regular expressions, so you can build an NPC which responds with some
  contextual awareness like a chatbot.

* Arbitrary saving/loading of game states. All game objects can be serialized
  to, or loaded from, JSON data.

* Flexible and extensible parser. The parser that handles game input already
  has a lot of useful commands and behaviours built-in. However, any of the
  built-in commands can be disabled if necessary, and the parser provides
  methods that allow new commands to be defined.

* Configurable input/output streams. ``text_game_maker`` allows custom handlers
  to be set for handling user input, and for displaying game output. By default,
  ``text_game_maker`` will use a ``prompt-toolkit`` session that interacts with
  ``stdin`` and  ``stdout`` of the process it is running in. Defining custom
  input/output handlers allows you to run your game, for example, as a slack bot
  instead (see ``scripts/text-game-slackbot-runner.py``).

* ``text_game_maker`` has a music system that allows polyphonic music (not
  fancy, just simple tones that sound like an old Nokia ringtone, but with full
  polyphony) to be written as simple text files that can be loaded and played
  during the game (see `PTTTL <https://github.com/eriknyquist/ptttl>`_).
  ``pygame`` is used for playback of the raw audio samples.
  
* Much more... check out the `API documentation! <https://text-game-maker.readthedocs.io>`_

Getting started
===============

Install
#######

::

    pip install text_game_maker

Run the example map
###################

::

    python -m text_game_maker.example

Writing maps
============

#. Write a class that extends the text_game_maker.utils.runner.MapRunner class
   and implements the ``build_map`` (and optionally ``build_parser``) methods.
   See ``example-map/example_map.py`` and the
   `API documentation <https://text-game-maker.readthedocs.io>`_ for reference.

#. Run ``text_game_maker.runner`` with the name of the ``.py`` file containing
   your MapRunner class, e.g.:

   ::

       python -m text_game_maker.runner mymaprunner.py

   In this example, ``text_game_maker.runner`` will import the
   ``mymaprunner.py`` file and run the first instance it finds of a class
   which is a subclass of text_game_maker.utils.runner.MapRunner

To run a MapRunner class as a slackbot to play your game over slack, the
procedure is the same, except use the ``text_game_maker.slackbot_runner``
script, e.g.:

::

    python -m text_game_maker.slackbot_runner mymaprunner.py

Note that when using the slackbot runner you must have already created a
bot user in your slack workspace, and the API token for the bot user must be
available in an environment variable named ``SLACK_BOT_TOKEN``.

API Documentation
=================

`text-game-maker.readthedocs.io <https://text-game-maker.readthedocs.io>`_
