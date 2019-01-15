.. |projectname| replace:: text_game_maker

Text Adventure Game Maker
-------------------------

.. contents:: Contents

|projectname| is a framework for building simple text-based games.

Getting started
===============

Clone from github
#################

::

    git clone https://github.com/eriknyquist/text_game_maker
    cd text_game_maker

Install
#######

::

    python setup.py install

Run the example map
###################

::

    python scripts/test-game-runner.py example-map/example_map.py

Writing maps
============

#. Write a class that extends the text_game_maker.utils.runner.MapRunner class
   and implements the ``build_map`` (and optionally ``build_parser``) methods.
   See ``example-map/example_map.py`` and the
   `API documentation <https://text-game-maker.readthedocs.io>`_ for reference.

#. Run ``scripts/text-game-runner.py`` with the name of the ``.py`` file
   containing your MapRunner class, e.g.:

   ::

       python scripts/text-game-runner.py mymaprunner.py

   ``text-game-runner.py`` will import the file and run the first instance it
   finds of a class which is a subclass of
   text_game_maker.utils.runner.MapRunner

Documentation
=============

`text-game-maker.readthedocs.io <https://text-game-maker.readthedocs.io>`_
