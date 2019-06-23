from text_game_maker.utils import utils

class Event(object):
    """
    Class to represent a generic event that handlers can be registered for
    """
    def __init__(self):
        self._handlers = []

    def clear_handlers(self):
        """
        Clear any registered handlers for event.

        :return: Event instance
        :rtype: text_game_maker.event.event.Event
        """
        self._handlers = []
        return self

    def add_handler(self, handler):
        """
        Registers a handler to run when this event is generated.

        :param handler: handler to add. Handler should be of the form:\
            ``handler(*event_args)`` where ``event_args`` is all of the\
            arguments for the event
        :return: Event instance
        :rtype: text_game_maker.event.event.Event
        """
        self._handlers.append(handler)
        return self

    def clear_handler(self, handler):
        """
        Unregisters a handler.

        :param handler: the handler that was previously registered
        :return: Event instance
        :rtype: text_game_maker.event.event.Event
        """
        try:
            self._handlers.remove(handler)
        except ValueError:
            pass

        return self

    def generate(self, *event_args):
        """
        Generate an event. Runs all registered handlers.

        :param event_args: arguments to pass to event handlers
        :return: Event instance
        :rtype: text_game_maker.event.event.Event
        """
        for handler in self._handlers:
            handler(*event_args)

        return self

    def serialize(self):
        return [utils.serialize_callback(cb) for cb in self._handlers]

    def deserialize(self, attrs):
        self._handlers = [utils.deserialize_callback(name) for name in attrs]
