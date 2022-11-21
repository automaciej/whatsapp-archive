#!/usr/bin/python3

"""Reads a WhatsApp conversation export file and writes a HTML file."""

import argparse
import datetime
import dateutil.parser
import itertools
import jinja2
import logging
import os.path
import re

# Format of the standard WhatsApp export line. This is likely to change in the
# future and so this application will need to be updated.
DATE_RE = '(?P<date>[\d/-]+)'
TIME_RE = '(?P<time>[\d:]+( [AP]M)?)'
DATETIME_RE = '\[?' + DATE_RE + ',? ' + TIME_RE + '\]?'
SEPARATOR_RE = '( - |: | )'
NAME_RE = '(?P<name>[^:]+)'
WHATSAPP_RE = (DATETIME_RE +
               SEPARATOR_RE +
               NAME_RE +
               ': '
               '(?P<body>.*$)')

FIRSTLINE_RE = (DATETIME_RE +
               SEPARATOR_RE +
               '(?P<body>.*$)')


class Error(Exception):
    """Something bad happened."""


def ParseLine(line):
    """Parses a single line of WhatsApp export file."""
    m = re.match(WHATSAPP_RE, line)
    if m:
        d = dateutil.parser.parse("%s %s" % (m.group('date'),
            m.group('time')), dayfirst=True)
        return d, m.group('name'), m.group('body')
    # Maybe it's the first line which doesn't contain a person's name.
    m = re.match(FIRSTLINE_RE, line)
    if m:
        d = dateutil.parser.parse("%s %s" % (m.group('date'),
            m.group('time')), dayfirst=True)
        return d, "nobody", m.group('body')
    return None


def IdentifyMessages(lines, os=os.getcwd()):
    """Input text can contain multi-line messages. If there's a line that
    doesn't start with a date and a name, that's probably a continuation of the
    previous message and should be appended to it.
    """
    messages = []
    msg_date = None
    msg_user = None
    msg_body = None
    for line in lines:
        m = ParseLine(line)
        if m is not None:
            if msg_date is not None:
                # We have a new message, so there will be no more lines for the
                # one we've seen previously -- it's complete. Let's add it to
                # the list.
                if "(archivo adjunto)" in msg_body or "(attached file)" in msg_body:
                    messages.append((msg_date, msg_user, msg_body, (os + "\\" + msg_body.split("(")[0][1:-1]).replace("\\", '/')))
                else:
                    messages.append((msg_date, msg_user, msg_body, 0))
            msg_date, msg_user, msg_body = m
        else:
            if msg_date is None:
                raise Error("Can't parse the first line: " + repr(line) +
                        ', regexes are FIRSTLINE_RE=' + repr(FIRSTLINE_RE) +
                        ' and WHATSAPP_RE=' + repr(WHATSAPP_RE))
            msg_body += '\n' + line.strip()
    # The last message remains. Let's add it, if it exists.
    if msg_date is not None:
        if "(archivo adjunto)" in msg_body:
            messages.append((msg_date, msg_user, msg_body, msg_body.split("(")[0][1:-1], os))
        else:
            messages.append((msg_date, msg_user, msg_body, 0, os))
    return messages


def TemplateData(messages, input_filename):
    """Create a struct suitable for procesing in a template.
    Returns:
        A dictionary of values.
    """
    by_user = []
    file_basename = os.path.basename(input_filename)
    for user, msgs_of_user in itertools.groupby(messages, lambda x: x[1]):
        by_user.append((user, list(msgs_of_user)))
    return dict(by_user=by_user, input_basename=file_basename,
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
            ol.messages li {
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
        </style>

    </head>
    <body>
        <h1>{{ input_basename }}</h1>
        <ol class="users">
        {% for user, messages in by_user %}
            <li>
            <span class="username">{{ user }}</span>
            <span class="date">{{ messages[0][0] }}</span>
            <ol class="messages">
            {% for message in messages %}
                {% if message[3] != 0 %}
                    {% if "IMG" in message[3] %}
                        <a href='{{ message[3] }}' target="_blank"><img src='{{ message[3] }}' width="400"></img></a>
                    {% elif "opus" in message[3] %}
                        <li> <A HREF="{{ message[3] }}" target="_blank"> ESCUCHAR AUDIO </A> </li>
                    {% endif %}
                {% else %}
                    <li>{{ message[2] | e }}</li>
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
