#!/usr/bin/python3

import whatsapp_archive
import unittest
import datetime

INPUT_1 = ["13/01/18, 01:23 - Fake Name: line1\n", "line2\n"]
INPUT_2 = ["13/01/18, 01:23 - Fake Name: line1\n", "line2\n",
        "13/01/18, 01:24 - Name Two: single line\n"]
INPUT_3 = ["13/01/18, 01:23 - Fake Name: line1\n", "line2\n",
        "13/01/18, 01:24 - Fake Name: line3\n",
        "13/01/18, 01:25 - Name Two: single line\n"]

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
        template_data = whatsapp_archive.TemplateData(messages)
        self.assertEqual(template_data, {
            'by_user': [('Fake Name',
              [(datetime.datetime(2018, 1, 13, 1, 23),
                  'Fake Name',
                  'line1\nline2'),
               (datetime.datetime(2018, 1, 13, 1, 24),
                  'Fake Name', 'line3')]),
             ('Name Two',
              [(datetime.datetime(2018, 1, 13, 1, 25),
                'Name Two',
                'single line')])]})

if __name__ == '__main__':
    unittest.main()

