import re

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

        # This *must* be lower than 100
        self.groups_per_regex = 75

        self.flags = re.IGNORECASE
        self.groupid = 1
        self.compiled = None
        self.patterns = {}
        self.subgroups = None

    def groups(self):
        """
        Return tuple of all subgroups from the last regex match performed
        when fetching an item, as returned by re.MatchObject.groups()

        :return: tuple of subgroups from last match
        :rtype: tuple
        """
        return self.subgroups

    def _block_to_regexs(self, block):
        total_len = len(block)
        override_slice = None
        num_regexs = 1
        start = 0
        ret = []
        end = 0
        i = 0

        while True:
            slice_size = int(total_len / num_regexs)

            while start < total_len:
                start = i * slice_size                   # Slice start index
                end = min(total_len, start + slice_size) # Slice end index
                blockslice = block[start:end]
                regex = '|'.join(blockslice)

                try:
                    compiled = re.compile(regex, flags=self.flags)
                except AssertionError:
                    # Raises AssertionError for too many named groups
                    if (num_regexs == total_len) or (len(block) == 1):
                        raise AssertionError("Too many groups in regex '%s'"
                            % regex)

                    num_regexs *= 2
                    i = 0
                    ret = []
                    break

                i += 1
                ret.append(compiled)

            if ret:
                break

        return ret

    def compile(self):
        """
        Compile all regular expressions in the dictionary
        """
        i = 0
        ret = []
        block = []
        self.compiled = []

        for groupname in self.patterns:
            pattern, _ = self.patterns[groupname]
            block.append('(?P<%s>^%s$)' % (groupname, pattern))
            i += 1

            if i == self.groups_per_regex:
                self.compiled.extend(self._block_to_regexs(block))
                i = 0
                block = []

        if block:
            self.compiled.extend(self._block_to_regexs(block))

    def dump_to_dict(self):
        """
        Dump all pattern/value pairs to a regular dict, where the regular
        expressions are the keys

        :return: dict of pattern/value pairs
        :rtype: dict
        """
        ret = {}
        for pattern, value in self.iteritems():
            ret[pattern] = value

        return ret

    def load_from_dict(self, data):
        """
        Load pattern/value pairs from a regular dict. This overwrites any
        existing pattern/value pairs

        :param dict data: pattern/value pairs to load
        """
        self.groupid = 1
        self.compiled = None
        self.patterns = {}

        for pattern in data:
            self.__setitem__(pattern, data[pattern])

        return self

    def _do_match(self, text):
        if not self.compiled:
            self.compile()

        ret = None
        m = None
        for compiled in self.compiled:
            m = compiled.match(text)
            if m and m.lastgroup:
                ret = m
                break

        if not ret:
            raise KeyError("No patterns matching '%s' in dict" % text)

        return ret


    def __setitem__(self, pattern, value):
        if not pattern:
            return

        self.patterns["g%d" % self.groupid] = (pattern, value)
        self.groupid += 1

        if self.compiled is not None:
            self.compiled = None

    def __getitem__(self, text):
        m = self._do_match(text)
        self.subgroups = m.groups()[m.lastindex:]
        return self.patterns[m.lastgroup][1]

    def __contains__(self, text):
        try:
            _ = self.__getitem__(text)
        except KeyError:
            return False

        return True

    def pop(self, text):
        """
        Return and delete the first value associated with a pattern matching
        'text'

        :param str text: text to match against
        :return: value associated with pattern matching 'text' (if any)
        """
        m = self._do_match(text)
        ret = self.patterns[m.lastgroup][1]
        del self.patterns[m.lastgroup]

        if self.compiled is not None:
            self.compiled = None

        return ret

    def items(self):
        """
        Return all values stored in this dict

        :return: list of values
        :rtype: list
        """
        return [self.patterns[groupname] for groupname in self.patterns]

    def values(self):
        """
        Return all values stored in this dict

        :return: list of values
        :rtype: list
        """
        return [value for _, value in self.iteritems()]

    def keys(self):
        """
        Return all keys stored in this dict

        :return: list of keys
        :rtype: list
        """
        return [pattern for pattern, _ in self.iteritems()]

    def iteritems(self):
        """
        Returns a generator to get all key/value pairs stored in this dict

        :return: generator to get pattern/value pairs
        """
        for groupname in self.patterns:
            yield self.patterns[groupname]

    def __str__(self):
        return str(self.dump_to_dict())

    def __repr__(self):
        return repr(self.dump_to_dict())

    def __len__(self):
        return len(self.patterns)

    def clear(self):
        """
        Clear all key/value pairs stored in this dict
        """
        self.groupid = 1
        self.compiled = None
        self.patterns.clear()

    def copy(self):
        """
        Create a new ReDict instance and copy all items in this dict into the
        new instance

        :return: new ReDict instance containing copied data
        :rtype: ReDict
        """
        new = ReDict()
        for pattern, value in self.iteritems():
            new[pattern] = value

        return new

    def update(self, other):
        """
        Add items from 'other' into this dict

        :param ReDict other: dict containing items to copy
        """
        for pattern, value in other.iteritems():
            self.__setitem__(pattern, value)
