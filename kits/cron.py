import re
from vine.five import string_t
import datetime

DAYNAMES = 'sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat'
WEEKDAYS = dict(zip(DAYNAMES, range(7)))


def weekday(name):
    """Return the position of a weekday: 0 - 7, where 0 is Sunday.

    Example:
        # >>> weekday('sunday'), weekday('sun'), weekday('mon')
        (0, 0, 1)
    """
    abbreviation = name[0:3].lower()
    try:
        return WEEKDAYS[abbreviation]
    except KeyError:
        # Show original day name in exception, instead of abbr.
        raise KeyError(name)


class ParseException(Exception):
    """Raised by :class:`crontab_parser` when the input can't be parsed."""


class crontab_parser(object):
    """Parser for Crontab expressions.

    Any expression of the form 'groups'
    (see BNF grammar below) is accepted and expanded to a set of numbers.
    These numbers represent the units of time that the Crontab needs to
    run on:

    .. code-block:: bnf

        digit   :: '0'..'9'
        dow     :: 'a'..'z'
        number  :: digit+ | dow+
        steps   :: number
        range   :: number ( '-' number ) ?
        numspec :: '*' | range
        expr    :: numspec ( '/' steps ) ?
        groups  :: expr ( ',' expr ) *

    The parser is a general purpose one, useful for parsing hours, minutes and
    day of week expressions.  Example usage:

    .. code-block:: pycon

        # >>> minutes = crontab_parser(60).parse('*/15')
        [0, 15, 30, 45]
        # >>> hours = crontab_parser(24).parse('*/4')
        [0, 4, 8, 12, 16, 20]
        # >>> day_of_week = crontab_parser(7).parse('*')
        [0, 1, 2, 3, 4, 5, 6]

    It can also parse day of month and month of year expressions if initialized
    with a minimum of 1.  Example usage:

    .. code-block:: pycon

        # >>> days_of_month = crontab_parser(31, 1).parse('*/3')
        [1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31]
        # >>> months_of_year = crontab_parser(12, 1).parse('*/2')
        [1, 3, 5, 7, 9, 11]
        # >>> months_of_year = crontab_parser(12, 1).parse('2-12/2')
        [2, 4, 6, 8, 10, 12]

    The maximum possible expanded value returned is found by the formula:

        :math:`max_ + min_ - 1`
    """

    ParseException = ParseException

    _range = r'(\w+?)-(\w+)'
    _steps = r'/(\w+)?'
    _star = r'\*'

    def __init__(self, max_=60, min_=0):
        self.max_ = max_
        self.min_ = min_
        self.pats = (
            (re.compile(self._range + self._steps), self._range_steps),
            (re.compile(self._range), self._expand_range),
            (re.compile(self._star + self._steps), self._star_steps),
            (re.compile('^' + self._star + '$'), self._expand_star),
        )

    def parse(self, spec):
        acc = set()
        for part in spec.split(','):
            if not part:
                raise self.ParseException('empty part')
            acc |= set(self._parse_part(part))
        return acc

    def _parse_part(self, part):
        for regex, handler in self.pats:
            m = regex.match(part)
            if m:
                return handler(m.groups())
        return self._expand_range((part,))

    def _expand_range(self, toks):
        fr = self._expand_number(toks[0])
        if len(toks) > 1:
            to = self._expand_number(toks[1])
            if to < fr:  # Wrap around max_ if necessary
                return (list(range(fr, self.min_ + self.max_)) +
                        list(range(self.min_, to + 1)))
            return list(range(fr, to + 1))
        return [fr]

    def _range_steps(self, toks):
        if len(toks) != 3 or not toks[2]:
            raise self.ParseException('empty filter')
        return self._expand_range(toks[:2])[::int(toks[2])]

    def _star_steps(self, toks):
        if not toks or not toks[0]:
            raise self.ParseException('empty filter')
        return self._expand_star()[::int(toks[0])]

    def _expand_star(self, *args):
        return list(range(self.min_, self.max_ + self.min_))

    def _expand_number(self, s):
        if isinstance(s, string_t) and s[0] == '-':
            raise self.ParseException('negative numbers not supported')
        try:
            i = int(s)
        except ValueError:
            try:
                i = weekday(s)
            except KeyError:
                raise ValueError('Invalid weekday literal {0!r}.'.format(s))

        max_val = self.min_ + self.max_ - 1
        if i > max_val:
            raise ValueError(
                'Invalid end range: {0} > {1}.'.format(i, max_val))
        if i < self.min_:
            raise ValueError(
                'Invalid beginning range: {0} < {1}.'.format(i, self.min_))

        return i


class crontab:
    def __init__(self, cron_str):
        format_cs = crontab.parse(cron_str)
        self.minute = format_cs[0]
        self.hour = format_cs[1]
        self.day = format_cs[2]
        self.month = format_cs[3]
        self.weekday = format_cs[4]

    @staticmethod
    def parse(cron_str):
        s = re.sub(r'\s+', ' ', cron_str.strip(), flags=re.I)
        format_cs = s.split(" ")
        minute = crontab_parser(60).parse(format_cs[0])
        hour = crontab_parser(24).parse(format_cs[1])
        day = crontab_parser(31, 1).parse(format_cs[2])
        month = crontab_parser(12, 1).parse(format_cs[3])
        weekday = crontab_parser(7, 1).parse(format_cs[4])
        return (minute, hour, day, month, weekday)

    def is_due_now(self):
        now_ts = datetime.datetime.now()
        return self.is_due(now_ts)

    def is_due(self, dt):
        if dt.month in self.month \
                and dt.isoweekday() in self.weekday \
                and dt.day in self.day \
                and dt.hour in self.hour \
                and dt.minute in self.minute:
            return True
        return False


if __name__ == '__main__':
    # print(crontab_parser(7).parse('8'))
    # print(crontab.parse(" *  *    asd  */1  *  ")[3])
    a = crontab("*/2 * * * *")
    print(a.is_due_now())
