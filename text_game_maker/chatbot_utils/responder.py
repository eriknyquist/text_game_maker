from text_game_maker.chatbot_utils.redict import ReDict

class NoResponse(object):
    pass

def _check_get_response(responsedict, text):
    try:
        response = responsedict[text]
    except KeyError:
        return NoResponse, None

    return response, responsedict.groups()

def _check_pattern_response_pair(pair):
    regex = None
    if len(pair) != 2:
        raise ValueError("Pattern response pair must contain two items")

    patterns, response = pair
    if isinstance(patterns, list):
        regex = "|".join(patterns)
    elif isinstance(patterns, str):
        regex = patterns
    else:
        raise ValueError("First item in pattern response pair must be "
            "a list or a string")

    return regex, response

def _attempt_context_entry(contexts, text):
    for context in contexts:
        response, groups = _check_get_response(context.entry, text)
        if response != NoResponse:
            return context, response, groups

    return None, NoResponse, None

class Context(object):
    """
    Class representing a "discussion" context, allowing for a Responder that
    responds with contextual awareness
    """
    def __init__(self, lists=None):
        self.entry = ReDict()
        self.responses = ReDict()
        self.chains = []
        self.chain = None
        self.chain_index = 0
        self.contexts = []

        if lists:
            self._build_from_lists(lists)

    def compile(self):
        """
        Compile all regular expressions contained in this context so they are
        ready for immediate matching
        """
        if self.entry:
            self.entry.compile()

        if self.responses:
            self.responses.compile()

        if self.chains:
            for chain in self.chains:
                for responsedict in chain:
                    responsedict.compile()

        return self

    def add_chained_phrases(self, *pattern_response_pairs):
        """
        Add multiple chained pattern/response pairs. A chain defines a sequence
        of pattern/response pairs that are expected in the order that they occur
        in the passed arguments to this method. Whenever a Responder is inside a
        context and input matching the first pattern/response pair in a chain is
        seen, the Responder will continually expect the next pattern in the
        current chain until another chain or another context is entered. When
        the last pattern in the chain is reached, Responders will continue
        expecting this pattern until another chain or context is entered.

        :param pattern_response_pairs: one or more pattern/response pairs, \
            where a pattern/response pair is a tuple of the form \
            ``(regexs, value)``, where ``regexs`` is a regular expression or \
            list of regular expressions and ``value`` is an arbitrary object
        """
        chain = []
        for pair in pattern_response_pairs:
            pattern, response = _check_pattern_response_pair(pair)
            responsedict = ReDict()
            responsedict[pattern] = response
            chain.append(responsedict)

        self.chains.append(chain)
        return self

    def add_entry_phrase(self, patterns, response):
        """
        Add a pattern/response pair to be used as an entry point for
        this context. If input matching matching one of the patterns passed here
        is seen, Responders will return the corresponding response object and
        enter the context.

        :param patterns: regular expression or list of regular expressions. If \
            the input passed to ``get_response`` matches one of these \
            patterns, then the object passed here as ``response`` will be \
            returned.
        :param object response: object to return from ``get_response`` if the \
            passed input matches one of the regular expressions passed here as
            ``response``.
        """
        pattern, response = _check_pattern_response_pair((patterns, response))
        self.entry[pattern] = response
        return self

    def add_entry_phrases(self, *pattern_response_pairs):
        """
        Add one or more pattern/response pairs to be used as entry points for
        this context. If input matching matching one of the patterns passed here
        is seen, Responders will return the corresponding response object and
        enter the context.

        :param pattern_response_pairs: one or more pattern/response pairs, \
            where a pattern/response pair is a tuple of the form \
            ``(regexs, value)``, where ``regexs`` is a regular expression or \
            list of regular expressions and ``value`` is an arbitrary object
        """
        for pair in pattern_response_pairs:
            self.add_entry_phrase(*pair)

        return self

    def add_response(self, patterns, response):
        """
        Add a pattern/response pair that will be only be recognized
        when a Responder is in this context

        :param patterns: regular expression or list of regular \
            expressions. If the input passed to ``get_response`` matches one \
            of these patterns, then the object passed here as ``response`` \
            will be returned.
        :param object response: object to return from ``get_response`` if the \
            passed input matches one of the regular expressions passed here as
            ``response``.
        """
        pattern, response = _check_pattern_response_pair((patterns, response))
        self.responses[pattern] = response
        return self

    def add_responses(self, *pattern_response_pairs):
        """
        Add one more more pattern/response pairs that will be only be recognized
        when a Responder is in this context

        :param pattern_response_pairs: one or more pattern/response pairs, \
            where a pattern/response pair is a tuple of the form \
            ``(regexs, value)``, where ``regexs`` is a regular expression or \
            list of regular expressions and ``value`` is an arbitrary object
        """
        for pair in pattern_response_pairs:
            self.add_response(*pair)

        return self

    def add_context(self, context):
        """
        Add context that can only be entered when already in this context

        :param text_game_maker.chatbot_utils.responder.Context context: context instance to add
        """
        if not isinstance(context, Context):
            raise ValueError("add_context argument must be a Context instance")

        self.contexts.append(context)
        return self

    def add_contexts(self, *contexts):
        """
        Add one or more context instances to this context

        :param text_game_maker.chatbot_utils.responder.Context contexts: context instances to add
        """
        for context in contexts:
            self.add_context(context)

        return self

    def _search_chains(self, text):
        for chain in self.chains:
            if (len(chain) > 0):
                resp, groups = _check_get_response(chain[0], text)
                if resp != NoResponse:
                    return chain, resp, groups

        return None, NoResponse, None

    def _get_chained_response(self, text):
        if not self.chain:
            chain, response, groups  = self._search_chains(text)
            if chain:
                self.chain = chain
                self.chain_index = 1
                return response, groups

            return NoResponse, None

        responsedict = self.chain[self.chain_index]
        resp, groups = _check_get_response(responsedict, text)

        if resp != NoResponse:
            if self.chain_index < (len(self.chain) - 1):
                self.chain_index += 1
        elif self.chain_index > 0:
            responsedict = self.chain[self.chain_index - 1]
            resp, groups = _check_get_response(responsedict, text)

        return resp, groups

    def get_response(self, text):
        """
        Find a response object associated with a pattern in this context that
        matches 'text', and return it (if any). If no matching patterns can be
        found, 'text' itself will be returned.

        :param str text: input text to check for matching patterns against
        :return: tuple of the form ``(response, groups)``. ``response`` is the \
            response object associated with the matching regular expression, \
            if any, otherwise 'text'. ``groups`` is a tuple of subgroups from \
            the regular expression match (as returned by \
            re.MatchObject.groups), if any, otherwise None.
        """
        resp, groups = self._get_chained_response(text)
        if resp != NoResponse:
            return resp, groups

        resp, groups = _check_get_response(self.responses, text)
        if resp == NoResponse:
            resp, groups = _check_get_response(self.entry, text)

        # If we got a response from anything other than a chain, make
        # sure we exit any current chains by setting self.chain = False
        if resp != NoResponse:
            self.chain = None

        return resp, groups

class Responder(object):
    """
    Represents a high-level responder object which can be used to register
    pattern/response pairs, and can accept input text to retrieve matching
    response objects
    """

    def __init__(self):
        self.responses = ReDict()
        self.default_response = NoResponse

        self.context = None
        self.contexts = []

    def compile(self):
        """
        Compile all regular expressions contained in this responder (including
        contexts), so they are ready for matching immediately
        """
        if self.responses:
            self.responses.compile()

        if self.contexts:
            for context in self.contexts:
                context.compile()

        return self

    def add_default_response(self, response):
        """
        Set response to return when no other matching responses can be found

        :param response: object to return as default response
        """
        self.default_response = response
        return self

    def add_response(self, patterns, response):
        """
        Add a pattern/response pair that will always be recognized by a
        Responder, regardless of context

        :param list patterns: list of regular expressions. If the input passed \
            to ``get_response`` matches one of these patterns, then the object \
            passed here as ``response`` will be returned.
        :param object response: object to return from ``get_response`` if the \
            passed input matches one of the regular expressions passed here as
            ``response``.
        """
        pattern, response = _check_pattern_response_pair((patterns, response))
        self.responses[pattern] = response
        return self

    def add_responses(self, *pattern_response_pairs):
        """
        Add one or moe pattern/response pairs that will always be recognized
        by a Responder, regardless of context

        :param pattern_response_pairs: one or more pattern/response pairs, \
            where a pattern/response pair is a tuple of the form \
            ``(regexs, value)``, where ``regexs`` is a regular expression or \
            list of regular expressions and ``value`` is an arbitrary object
        """
        for pair in pattern_response_pairs:
            self.add_response(*pair)

        return self

    def add_context(self, context):
        """
        Add context instance to this responder

        :param text_game_maker.chatbot_utils.responder.Context context: context instance to add
        """
        if not isinstance(context, Context):
            raise ValueError("add_context argument must be a Context instance")

        self.contexts.append(context)
        return self

    def add_contexts(self, *contexts):
        """
        Add one or more context instances to this responder

        :param text_game_maker.chatbot_utils.responder.Context contexts: context instances to add
        """
        for context in contexts:
            self.add_context(context)

        return self

    def get_response(self, text):
        """
        Find a response object associated with a pattern that matches 'text',
        and return it (if any). If no matching patterns can be found, 'text'
        itself will be returned.

        :param str text: input text to check for matching patterns against
        :return: tuple of the form ``(response, groups)``. ``response`` is the \
            response object associated with the matching regular expression, \
            if any, otherwise 'text'. ``groups`` is a tuple of subgroups from \
            the regular expression match (as returned by \
            re.MatchObject.groups), if any, otherwise None.
        """
        response = NoResponse
        groups = None

        # If currently in a context, try to get a response from the context
        if self.context:
            response, groups = self.context.get_response(text)
            if response == NoResponse:
                # Try entering subcontexts contained in current context, if any
                context, response, groups = _attempt_context_entry(
                    self.context.contexts, text)

                if context:
                    self.context = context

        # If no contextual response is available, try to get a response from
        # the dict of contextless responses
        if response == NoResponse:
            response, groups = _check_get_response(self.responses, text)
            if response != NoResponse:
                # If we are currently in a context but only able to get a
                # matching response from the contextless dict, set the current
                # context to None
                if self.context:
                    self.context = None
            else:
                # No contextless responses available, attempt context entry
                context, response, groups = _attempt_context_entry(
                    self.contexts, text)

                if context:
                    self.context = context
                else:
                    response = self.default_response
                    groups = None

        return response, groups
