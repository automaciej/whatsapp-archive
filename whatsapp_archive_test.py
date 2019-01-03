#!/usr/bin/python3

import unittest

import datetime
import re
import whatsapp_archive

INPUT_1 = ["13/01/18, 01:23 - Fake Name: line1\n", "line2\n"]
INPUT_2 = ["13/01/18, 01:23 - Fake Name: line1\n", "line2\n",
        "13/01/18, 01:24 - Name Two: single line\n"]
INPUT_3 = ["13/01/18, 01:23 - Fake Name: line1\n", "line2\n",
        "13/01/18, 01:24 - Fake Name: line3\n",
        "13/01/18, 01:25 - Name Two: single line\n"]
INPUT_4 = ["14/04/18, 22:08 - Nesta conversa, (…)\n",
           "14/04/18, 22:08 - Alguém: Olá!\n"]
# Format from a different locale setting.
INPUT_5 = ["19-02-18 17:02 - Los mensajes y llamadas en este chat ahora están "
           "protegidos con cifrado de extremo a extremo. Toca para más "
           "información.\n",
           "19-02-18 17:02 - human1: Hola\n",
           "19-02-18 17:14 - human2: como estás?\n"]

# Based on https://github.com/automatthias/whatsapp-archive/issues/1
# 12-hour format.
INPUT_6 = ["2016-06-27, 8:04:08 AM: Neil: Hi\n",]

class IdentifyMessagesTest(unittest.TestCase):

    def testInputMultiline(self):
        self.assertEqual(whatsapp_archive.IdentifyMessages(INPUT_1), [
            (datetime.datetime(2018, 1, 13, 1, 23), 'Fake Name', 'line1\nline2'),
        ])

    def testInputTwoMultiline(self):
        self.assertEqual(whatsapp_archive.IdentifyMessages(INPUT_2), [
            (datetime.datetime(2018, 1, 13, 1, 23), 'Fake Name', 'line1\nline2'),
            (datetime.datetime(2018, 1, 13, 1, 24), 'Name Two', 'single line'),
        ])

    def testTemplateData(self):
        messages = whatsapp_archive.IdentifyMessages(INPUT_3)
        template_data = whatsapp_archive.TemplateData(messages, "fake_filename")
        self.assertEqual(template_data, {
            'by_user': [
                ('Fake Name', [
                    (datetime.datetime(2018, 1, 13, 1, 23), 'Fake Name', 'line1\nline2'),
                    (datetime.datetime(2018, 1, 13, 1, 24), 'Fake Name', 'line3')
                ]),
                ('Name Two', [
                    (datetime.datetime(2018, 1, 13, 1, 25), 'Name Two', 'single line')
                ])
            ],
            'input_basename': 'fake_filename',
            'input_full_path': 'fake_filename'})

    def testFirstLineNoColon(self):
        messages = whatsapp_archive.IdentifyMessages(INPUT_4)
        template_data = whatsapp_archive.TemplateData(messages, "fake_filename")
        self.assertEqual(template_data, {
            'by_user': [
                ('nobody', [
                    (datetime.datetime(2018, 4, 14, 22, 8), 'nobody', 'Nesta conversa, (…)'),
                ]),
                ('Alguém', [
                    (datetime.datetime(2018, 4, 14, 22, 8), 'Alguém', 'Olá!'),
                ]),
              ],
              'input_basename': 'fake_filename',
              'input_full_path': 'fake_filename'})

    def testDifferentFormat(self):
        self.maxDiff = None
        messages = whatsapp_archive.IdentifyMessages(INPUT_5)
        template_data = whatsapp_archive.TemplateData(messages, "fake_filename")
        self.assertEqual(template_data, {
            'by_user': [
                ('nobody', [
                    (datetime.datetime(2018, 2, 19, 17, 2),
                        'nobody', 'Los mensajes y llamadas en este chat ahora '
                        'están protegidos con cifrado de extremo a extremo. '
                        'Toca para más información.'),
                ]),
                ('human1', [
                    (datetime.datetime(2018, 2, 19, 17, 2), 'human1', 'Hola'),
                ]),
                ('human2', [
                    (datetime.datetime(2018, 2, 19, 17, 14), 'human2', 'como estás?'),
                ]),
              ],
              'input_basename': 'fake_filename',
              'input_full_path': 'fake_filename'})

    def testNeil(self):
        self.maxDiff = None
        messages = whatsapp_archive.IdentifyMessages(INPUT_6)
        template_data = whatsapp_archive.TemplateData(messages, "fake_filename")
        self.assertEqual(template_data, {
            'by_user': [
                ('Neil', [
                    (datetime.datetime(2016, 6, 27, 8, 4, 8),
                        'Neil', 'Hi'),
                ]),
              ],
              'input_basename': 'fake_filename',
              'input_full_path': 'fake_filename'})

    def testEwoutTime(self):
        INPUT = """[02-12-18 22:55:45]"""
        result = re.match(whatsapp_archive.DATETIME_RE, INPUT)
        self.assertIsNotNone(result)
        self.assertEqual(('02-12-18', '22:55:45', None), result.groups())

    def testEwoutName(self):
        INPUT = """[02-12-18 22:55:45] Ewout:"""
        pattern = (whatsapp_archive.DATETIME_RE + whatsapp_archive.SEPARATOR_RE
                + whatsapp_archive.NAME_RE)
        result = re.match(pattern, INPUT)
        self.assertIsNotNone(result)
        self.assertEqual(('02-12-18', '22:55:45', None, ' ', 'Ewout'), result.groups())

    def testEwout1(self):
        INPUT = ["""[02-12-18 22:55:45] Ewout: Test\n""",]
        self.maxDiff = None
        messages = whatsapp_archive.IdentifyMessages(INPUT)
        self.assertEqual(
                [(datetime.datetime(2018, 12, 2, 22, 55, 45), 'Ewout', 'Test')],
                messages)

    def testEwout2(self):
        INPUT = ["[02-12-18 22:55:45] Ewout: Test\n",
                 "[02-12-18 22:56:00] Ewout: Does this work?\n",
                 "[02-12-18 22:56:20] Ewout: Sending a message to myself\n",
        ]
        self.maxDiff = None
        messages = whatsapp_archive.IdentifyMessages(INPUT)
        self.assertEqual([
            (datetime.datetime(2018, 12, 2, 22, 55, 45), 'Ewout', 'Test'),
            (datetime.datetime(2018, 12, 2, 22, 56), 'Ewout', 'Does this work?'),
            (datetime.datetime(2018, 12, 2, 22, 56, 20), 'Ewout', 'Sending a message to myself'),
        ], messages)


if __name__ == '__main__':
    unittest.main()
