#!/usr/bin/python3

"""Reads a WhatsApp conversation export file and writes a HTML file."""

import argparse
import collections
import dateutil.parser
import itertools
import jinja2
import logging
import os.path
import re

# Format of the standard WhatsApp export line. This is likely to continue to
# change in the future and so this application will need to be updated.
# The biggest challenge is that every language seems to have its own set of
# rules for dates, and it's not trivial to match them all correctly.
TIME_RE = '(?P<time>[\d:]+( [AP]M)?)'
SEPARATOR_RE = '( - |: | )'
NAME_RE = '(?P<name>[^:]+)'


class Error(Exception):
    """Something bad happened."""


Matchers = collections.namedtuple(
    'Matchers',
    'date time datetime name firstline line')


def _MakeDatePattern():
    patterns = []
    d = '[\d]+'
    separators = ['-', '\.', '/']
    for sep in separators:
        patterns.append(f'{d}{sep}{d}{sep}{d}')
    return '(?P<date>' + '|'.join(patterns) + ')'


def _MakeDateTimePattern():
    return '\[?' + _MakeDatePattern() + ',? ' + TIME_RE + '\]?'


def _MakeLinePattern():
    return (
        _MakeDateTimePattern() +
        SEPARATOR_RE +
        NAME_RE +
        ': ' +
        '(?P<body>.*$)')


def _MakeFirstLinePattern():
    return (_MakeDateTimePattern() + SEPARATOR_RE + '(?P<body>.*$)')


def _MakeMatchers() -> Matchers:
    return Matchers(
        date = _MakeDatePattern(),
        time = TIME_RE,
        datetime = _MakeDateTimePattern(),
        name = NAME_RE,
        firstline = _MakeFirstLinePattern(),
        line = _MakeLinePattern(),
    )


def ParseLine(matchers: Matchers, line: str):
    """Parses a single line of WhatsApp export file."""
    m = re.match(matchers.line, line)
    if m:
        d = dateutil.parser.parse("%s %s" % (m.group('date'),
            m.group('time')), dayfirst=True)
        return d, m.group('name'), m.group('body')
    # Maybe it's the first line which doesn't contain a person's name.
    m = re.match(matchers.firstline, line)
    if m:
        d = dateutil.parser.parse("%s %s" % (m.group('date'),
            m.group('time')), dayfirst=True)
        return d, "nobody", m.group('body')
    return None


def IdentifyMessages(lines):
    """Input text can contain multi-line messages. If there's a line that
    doesn't start with a date and a name, that's probably a continuation of the
    previous message and should be appended to it.
    """
    matchers = _MakeMatchers()
    messages = []
    msg_date = None
    msg_user = None
    msg_body = None
    for line in lines:
        m = ParseLine(matchers, line)
        if m is not None:
            if msg_date is not None:
                # We have a new message, so there will be no more lines for the
                # one we've seen previously -- it's complete. Let's add it to
                # the list.
                messages.append((msg_date, msg_user, msg_body))
            msg_date, msg_user, msg_body = m
        else:
            if msg_date is None:
                raise Error("Can't parse the first line: " + repr(line) +
                        ', regexes are first_line = ' + repr(matchers.firstline) +
                        ' and line =' + repr(matchers.line))
            msg_body += '\n' + line.strip()
    # The last message remains. Let's add it, if it exists.
    if msg_date is not None:
        messages.append((msg_date, msg_user, msg_body))
    return messages


def TemplateData(messages, input_filename):
    """Create a struct suitable for procesing in a template.
    Returns:
        A dictionary of values.
    """
    by_user = []
    file_basename = os.path.basename(input_filename)
    for user, msgs_of_user in itertools.groupby(messages, lambda x: x[1]):
        msgs_as_list = list(msgs_of_user)
        by_user.append((user, msgs_as_list[0][0].date(), msgs_as_list))
    dates = []
    prev_date = None
    for _, first_msg_date, _ in by_user:
        if first_msg_date != prev_date:
            dates.append(first_msg_date)
        prev_date = first_msg_date
    by_month = []
    # Item format:
    # ((year, month), [(day_of_month, datetime_object)])
    for month, days in itertools.groupby(dates, lambda x: (x.year, x.month)):
        by_month.append((month, [(d.day, d) for d in days]))
    return dict(by_user=by_user, dates=by_month, input_basename=file_basename,
            input_full_path=input_filename)


def FormatHTML(data):
    tmpl = """<!DOCTYPE html>
    <html>
    <head>
        <title>WhatsApp archive {{ input_basename }}</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: sans-serif;
                font-size: 10px;
            }
            ol.users {
                list-style-type: none;
                list-style-position: inside;
                margin: 0;
                padding: 0;
            }
            ol.messages {
                list-style-type: none;
                list-style-position: inside;
                margin: 0;
                padding: 0;
            }
            ol.messages li {
                margin-left: 1em;
                font-size: 12px;
            }
            span.username {
                color: gray;
            }
            span.date {
                color: gray;
            }
            ol.date-index {
                list-style: none;
            }
        </style>
    </head>
    <body>
        <h1>{{ input_basename }}</h1>
        <ol class="date-index">
        {% for month, days in dates %}
              <li> {{ month[0] }}-{{ month[1] }}
              {% for day, date_ in days %}
              <a href="#{{ date_ }}">{{ day }}</a>
              {% endfor %}
              </li>
        {% endfor %}
        </ol>
        <ol class="users">
        {% for user, first_msg_date, messages in by_user %}
            <li>
            <a id="{{first_msg_date}}">
                <span class="username">{{ user }}</span>
            </a>
            <span class="date">{{ messages[0][0] }}</span>
            <ol class="messages">
            {% for message in messages %}
                <li>{{ message[2] | e }}</li>
            {% endfor %}
            </ol>
            </li>
        {% endfor %}
        </ol>
    </body>
    </html>
    """
    return jinja2.Environment().from_string(tmpl).render(**data)


def main():
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description='Produce a browsable history '
            'of a WhatsApp conversation')
    parser.add_argument('-i', dest='input_file', required=True)
    parser.add_argument('-o', dest='output_file', required=True)
    args = parser.parse_args()
    with open(args.input_file, 'rt', encoding='utf-8-sig') as fd:
        messages = IdentifyMessages(fd.readlines())
    template_data = TemplateData(messages, args.input_file)
    HTML = FormatHTML(template_data)
    with open(args.output_file, 'w', encoding='utf-8') as fd:
        fd.write(HTML)


if __name__ == '__main__':
    main()
