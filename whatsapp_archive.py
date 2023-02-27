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

from typing import Optional

# Format of the standard WhatsApp export line. This is likely to continue to
# change in the future and so this application will need to be updated.
# The biggest challenge is that every language seems to have its own set of
# rules for dates, and it's not trivial to match them all correctly.
TIME_RE = '(?P<time>[\d:]+( [AP]M)?)'
SEPARATOR_RE = '( - |: | )'
NAME_RE = '(?P<name>[^:]+)'
DTSEP_RE = ' ?[,à]? ?'


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
    return '\[?' + _MakeDatePattern() + DTSEP_RE + TIME_RE + '\]?'


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
        return d, 'nobody', m.group('body')
    return None


FILE_RE = u'(?P<path>(AUD|PTT|STK|IMG|VID|DOC)-(\d){8}-WA\d+\.(m4a|jpg|mp4|pdf|webp|gif|opus|mp3|aac|wav|mpeg|3gp|avi|wmm|jpeg|png|tiff|ico))'


def IsMediaMessage(msg_body: str) -> bool:
    """Guesses whether the current message is a media message or not.

    Since media files seem to be named consistently, we don't need to match the
    text in the parentheses. We just match that there's something in
    parentheses.
    """
    m = re.match(u'\u200e?' + FILE_RE + ' \([a-z ]+\)', msg_body, re.U)
    return m is not None



def MediaMessageToPath(msg_body: str) -> Optional[str]:
    m = re.match(u'\u200e?' + FILE_RE, msg_body, re.U)
    if m:
        return m.group('path')


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
    msg_media = None
    for line in lines:
        m = ParseLine(matchers, line)
        if m is not None:
            if msg_date is not None:
                # We have a new message, so there will be no more lines for the
                # one we've seen previously -- it's complete. Let's add it to
                # the list.
                if IsMediaMessage(msg_body):
                    msg_media = MediaMessageToPath(msg_body)
                messages.append((msg_date, msg_user, msg_body, msg_media))
                msg_date, msg_user, msg_body, msg_media = None, None, None, None
            msg_date, msg_user, msg_body = m
        else:
            if msg_date is None:
                raise Error("Can't parse the first line: " + repr(line) +
                        ', regexes are first_line = ' + repr(matchers.firstline) +
                        ' and line =' + repr(matchers.line))
            msg_body += '\n' + line.strip()
            if IsMediaMessage(line.strip()):
                msg_media = MediaMessageToPath(line.strip())
    # The last message remains. Let's add it, if it exists.
    if msg_date is not None:
        if IsMediaMessage(msg_body):
            msg_media = MediaMessageToPath(msg_body)
        messages.append((msg_date, msg_user, msg_body, msg_media))
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
                font-family: Arial, Helvetica, sans-serif;
                font-size: 10px;
                background-color: rgb(255, 255, 255);
                display: flex;
                width: 100%;
                flex-direction: column;
            }
            @media screen and (min-width: 600px) {
                body, ol.users {
                flex-direction: column;
                width: 600px;
                }
            }
                    ol.users {
                list-style-type: none;
                list-style-position: inside;
                margin: 1em;
                padding: 0;
                background-color: rgb(250, 240, 227);
                border-radius: 7px;
            }
            ol.messages {
                list-style-type: none;
                list-style-position: inside;
                margin: 1em;
                padding-left: 1.5em;
            }
            ol.messages li.text-msg {
                margin-left: 1em;
                font-size: 12px;
                background-color: rgb(220,248,200);
                margin: 1em;
                margin-left: 0em;
                margin-bottom: 0em;
                margin-top: 0.3em;
                padding: 0.8em;
                border-width:1px;
                border-style: solid;
                border-color:rgb(225, 245, 212);
                border-radius: 7px;
                background: #dcf8c8;
                box-shadow:  5px 5px 5px #b0c6a0,
                            0px -0px 7px #fffff0;
            }
            span.username {
                color: rgb(26, 26, 26);
                font-size: 14px;
                font-weight: bolder;

            }
            span.date {
                color: rgb(20, 20, 20);
                font-style: Oblique;
                font-size: 10px;
            }

            ol.img {
                display: block;
                margin-left: auto;
                margin-right: auto;
                width: 50%;
                border-width:1px;
                border-style: solid;
                border-color:rgb(225, 245, 212);
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
            {% for _, _, body, media in messages %}
                {% if media is not none %}
                    {% if "IMG" in media or "jpeg" in media or "png" in media or "tiff" in media or "ico" in media or "gif" in media %}
                        <a href='{{ media }}' target="_blank"><img src='{{ media }}' width="400"></img></a>
                    {% elif "opus" in media or "m4a" in media or "mp3" in media or "AAC" in media or "WAV" in media %}
                        <audio controls>
                            <source src="{{ media }}" type="audio/x-m4a">
                        </audio>
                    {% elif "mp4" in media or ".MPEG" in media or ".3GP" in media or ".AVI" in media or ".WMM" in media %}
                       <video controls>
                         <source src="{{ media }}" type="video/mp4"/>
                       </video>
                    {% else %}
                        unsupported media {{ media | e }}
                    {% endif %}
                {% else %}
                    <li class="text-msg">{{ body | e }}</li>
                {% endif %}
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
