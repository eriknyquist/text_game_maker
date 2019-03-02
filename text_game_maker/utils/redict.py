import regex as re

class ReDict(dict):
    """
    Special dictionary which expects values to be *set* with regular expressions
    (REs) as keys, and expects values to be retreived using input text for an
    RE as keys. The value corresponding to the regular expression which matches
    the input text will be returned. In the case where the input text matches
    multiple REs, one of the matching values will be returned, but precisely
    which one is undefined.

    Example usage:

	>>> d = ReDict()
	>>> d['hello( world(!)*)?'] = 1
	>>> d['regex|dict key'] = 2
	>>> d['hello']
	1
	>>> d['hello world!!!!']
	1
	>>> d['regex']
	2
	>>> d['dict key']
	2
    """
    def __init__(self, *args, **kwargs):
        super(ReDict, self).__init__(*args, **kwargs)
        self.groupid = 1
        self.compiled = None
        self.patterns = {}

    def regex(self):
        ret = []
        for groupname in self.patterns:
            pattern, _ = self.patterns[groupname]
            ret.append('(?P<%s>^%s$)' % (groupname, pattern))

        return '|'.join(ret)

    def compile(self):
        self.compiled = re.compile(self.regex(), flags=re.IGNORECASE)

    def dump_to_dict(self):
        ret = {}
        for pattern, value in self.iteritems():
            ret[pattern] = value

        return ret

    def load_from_dict(self, data):
        self.groupid = 1
        self.compiled = None
        self.patterns = {}

        for pattern in data:
            self.__setitem__(pattern, data[pattern])

    def _do_match(self, text):
        if self.compiled is None:
            self.compile()

        m = self.compiled.match(text)
        if not m:
            raise KeyError("No patterns matching '%s' in dict")

        if not m.lastgroup:
            raise KeyError("No patterns matching '%s' in dict")

        return m

    def __setitem__(self, pattern, value):
        if not pattern:
            return

        self.patterns["g%d" % self.groupid] = (pattern, value)
        self.groupid += 1

        if self.compiled is not None:
            self.compiled = None

    def __getitem__(self, text):
        m = self._do_match(text)
        return self.patterns[m.lastgroup][1]

    def __contains__(self, text):
        try:
            _ = self.__getitem__(text)
        except KeyError:
            return False

        return True

    def pop(self, text):
        m = self._do_match(text)
        ret = self.patterns[m.lastgroup][1]
        del self.patterns[m.lastgroup]

        if self.compiled is not None:
            self.compiled = None

        return ret

    def items(self):
        return [self.patterns[groupname] for groupname in self.patterns]

    def iteritems(self):
        for groupname in self.patterns:
            yield self.patterns[groupname]

    def __str__(self):
        return str(self.dump_to_dict())

    def __repr__(self):
        return repr(self.dump_to_dict())

    def clear(self):
        self.groupid = 1
        self.compiled = None
        self.patterns.clear()

    def copy(self):
        new = ReDict()
        for pattern, value in self.iteritems():
            new[pattern] = value

        return new

    def update(self, other):
        for pattern, value in other.iteritems():
            self.__setitem__(pattern, value)

    def keys(self):
        return [pattern for pattern, _ in self.iteritems()]

    def values(self):
        return [value for _, value in self.iteritems()]
