#!/usr/bin/python3

import unittest
import parameterized

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
            (datetime.datetime(2018, 1, 13, 1, 23), 'Fake Name', 'line1\nline2', None),
        ])

    def testInputTwoMultiline(self):
        self.assertEqual(whatsapp_archive.IdentifyMessages(INPUT_2), [
            (datetime.datetime(2018, 1, 13, 1, 23), 'Fake Name', 'line1\nline2', None),
            (datetime.datetime(2018, 1, 13, 1, 24), 'Name Two', 'single line', None),
        ])

    def testTemplateData(self):
        self.maxDiff = None
        messages = whatsapp_archive.IdentifyMessages(INPUT_3)
        template_data = whatsapp_archive.TemplateData(messages, "fake_filename")
        self.assertEqual(template_data, {
            'by_user': [
                ('Fake Name', datetime.date(2018, 1, 13),
                 [
                     (datetime.datetime(2018, 1, 13, 1, 23), 'Fake Name', 'line1\nline2', None),
                     (datetime.datetime(2018, 1, 13, 1, 24), 'Fake Name', 'line3', None)
                 ]),
                ('Name Two', datetime.date(2018, 1, 13),
                 [
                     (datetime.datetime(2018, 1, 13, 1, 25), 'Name Two', 'single line', None)
                 ]),
            ],
            'dates': [((2018, 1), [(13, datetime.date(2018, 1, 13))])],
            'input_basename': 'fake_filename',
            'input_full_path': 'fake_filename'})

    def testFirstLineNoColon(self):
        self.maxDiff = None
        messages = whatsapp_archive.IdentifyMessages(INPUT_4)
        template_data = whatsapp_archive.TemplateData(messages, "fake_filename")
        self.assertEqual(template_data, {
            'by_user': [
                ('nobody', datetime.date(2018, 4, 14), [
                    (datetime.datetime(2018, 4, 14, 22, 8), 'nobody', 'Nesta conversa, (…)', None),
                ]),
                ('Alguém', datetime.date(2018, 4, 14), [
                    (datetime.datetime(2018, 4, 14, 22, 8), 'Alguém', 'Olá!', None),
                ]),
              ],
            'dates': [((2018, 4), [(14, datetime.date(2018, 4, 14))])],
            'input_basename': 'fake_filename',
            'input_full_path': 'fake_filename'})

    def testDifferentFormat(self):
        self.maxDiff = None
        messages = whatsapp_archive.IdentifyMessages(INPUT_5)
        template_data = whatsapp_archive.TemplateData(messages, "fake_filename")
        self.assertEqual(template_data, {
            'by_user': [
                ('nobody', datetime.date(2018, 2, 19), [
                    (datetime.datetime(2018, 2, 19, 17, 2),
                        'nobody', 'Los mensajes y llamadas en este chat ahora '
                        'están protegidos con cifrado de extremo a extremo. '
                        'Toca para más información.', None),
                ]),
                ('human1', datetime.date(2018, 2, 19), [
                    (datetime.datetime(2018, 2, 19, 17, 2), 'human1', 'Hola',
                     None),
                ]),
                ('human2', datetime.date(2018, 2, 19), [
                    (datetime.datetime(2018, 2, 19, 17, 14), 'human2',
                     'como estás?', None),
                ]),
              ],
            'dates': [((2018, 2), [(19, datetime.date(2018, 2, 19))])],
            'input_basename': 'fake_filename',
            'input_full_path': 'fake_filename'})

    def testNeil(self):
        self.maxDiff = None
        messages = whatsapp_archive.IdentifyMessages(INPUT_6)
        template_data = whatsapp_archive.TemplateData(messages, "fake_filename")
        self.assertEqual(template_data, {
            'by_user': [
                ('Neil', datetime.date(2016, 6, 27), [
                    (datetime.datetime(2016, 6, 27, 8, 4, 8),
                        'Neil', 'Hi', None),
                ]),
              ],
            'dates': [((2016, 6), [(27, datetime.date(2016, 6, 27))])],
            'input_basename': 'fake_filename',
            'input_full_path': 'fake_filename'})

    def testEwoutTime(self):
        INPUT = """[02-12-18 22:55:45]"""
        matchers = whatsapp_archive._MakeMatchers()
        result = re.match(matchers.datetime, INPUT)
        self.assertIsNotNone(result)
        self.assertEqual(('02-12-18', '22:55:45', None), result.groups())

    def testEwoutName(self):
        INPUT = """[02-12-18 22:55:45] Ewout:"""
        matchers = whatsapp_archive._MakeMatchers()
        pattern = (matchers.datetime + whatsapp_archive.SEPARATOR_RE
                + whatsapp_archive.NAME_RE)
        result = re.match(pattern, INPUT)
        self.assertIsNotNone(result)
        self.assertEqual(('02-12-18', '22:55:45', None, ' ', 'Ewout'),
                         result.groups(),
                         f'{pattern}: {INPUT} -> {result!r}')

    def testEwout1(self):
        INPUT = ["""[02-12-18 22:55:45] Ewout: Test\n""",]
        self.maxDiff = None
        messages = whatsapp_archive.IdentifyMessages(INPUT)
        self.assertEqual(
                [(datetime.datetime(2018, 12, 2, 22, 55, 45), 'Ewout', 'Test', None)],
                messages)

    def testEwout2(self):
        INPUT = ["[02-12-18 22:55:45] Ewout: Test\n",
                 "[02-12-18 22:56:00] Ewout: Does this work?\n",
                 "[02-12-18 22:56:20] Ewout: Sending a message to myself\n",
        ]
        self.maxDiff = None
        messages = whatsapp_archive.IdentifyMessages(INPUT)
        self.assertEqual([
            (datetime.datetime(2018, 12, 2, 22, 55, 45), 'Ewout', 'Test', None),
            (datetime.datetime(2018, 12, 2, 22, 56), 'Ewout', 'Does this work?', None),
            (datetime.datetime(2018, 12, 2, 22, 56, 20), 'Ewout', 'Sending a message to myself', None),
        ], messages)

    @parameterized.parameterized.expand([
        ('', False),
        ('hissing cat', False),  # https://xkcd.com/1179/
        ('02-12-18', True),
        ('13/01/18', True),
    ])
    def testMatchDate(self, date_string, should_match):
        pattern = whatsapp_archive._MakeDatePattern()
        if should_match:
            f = self.assertIsNotNone
        else:
            f = self.assertIsNone
        result = re.match(pattern, date_string)
        f(result,
          f'{pattern}: {date_string!r} -> {result!r}')

    def testRussian(self):
        """Addressing #issue7.

        https://github.com/automaciej/whatsapp-archive/issues/7
        """
        INPUT = [
            "12.02.19, 14:22 - Сообщения в данной группе теперь защищены "
            "сквозным шифрованием. Подробнее.\n",
            "17.02.19, 12:28 - +7 982 111-11-11: Пётр, ждём! Развязки\n",
        ]
        self.maxDiff = None
        messages = whatsapp_archive.IdentifyMessages(INPUT)
        self.assertEqual([
            (datetime.datetime(2019, 2, 12, 14, 22), 'nobody',
             'Сообщения в данной группе теперь защищены сквозным '
             'шифрованием. Подробнее.', None),
            (datetime.datetime(2019, 2, 17, 12, 28), '+7 982 111-11-11',
             'Пётр, ждём! Развязки', None),
        ], messages)


    def testIsMediaMessageAudio(self):
        self.assertTrue(whatsapp_archive.IsMediaMessage('AUD-20221225-WA0005.m4a (arquivo anexado)'))

    def testIsMediaMessageAudioWithLRM(self):
        self.assertTrue(whatsapp_archive.IsMediaMessage('\u200eAUD-20221225-WA0005.m4a (arquivo anexado)'))

    def testIsMediaMessageImage(self):
        self.assertTrue(whatsapp_archive.IsMediaMessage('\u200eIMG-20221224-WA0017.jpg (arquivo anexado)'))

    def testIsMediaMessageVideo(self):
        self.assertTrue(whatsapp_archive.IsMediaMessage('\u200eVID-20221225-WA0010.mp4 (arquivo anexado)'))

    def testMediaMessageToPath(self):
        self.assertEqual(
            whatsapp_archive.MediaMessageToPath(
                'VID-20221225-WA0010.mp4 (arquivo anexado)'),
            'VID-20221225-WA0010.mp4'
        )


if __name__ == '__main__':
    unittest.main()
