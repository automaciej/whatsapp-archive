# whatsapp-archive

Format your exported WhatsApp conversation in HTML.

Use the [Saving your chat history][saving] instructions to export your chat
history. You'll get an email with a .txt file. Save it on disk, and then run
this script.

Requirements (on Debian):

   * `python3-dateutil`
   * `python3-jinja2`
   * `python3-parameterized`

On Linux, run this in shell. On Windows, run this in cmd.

    ./whatsapp_archive.py -i your_file.txt -o output.html

## Contributing

When sending pull requests, please stick to these points:

1. Make sure the old unit tests are passing.
2. Add unit tests related to your pull request.
3. Make sure the coding style follows the [Google Python Style Guide][pystyle].
4. The generated HTML and CSS must be valid. (You can use https://validator.w3.org/ to check it.)

If you send me a pull request which doesn't do the above things, I'll add
comments asking for changes.

[pystyle]: https://google.github.io/styleguide/pyguide.html

## Interesting forks of this repository

- https://github.com/shrick/comm-history supports email as well.
- https://github.com/dsadinoff/whatsapp-archive handles bidirectional text
  (see Issue #5).
- https://github.com/djax666/whatsapp-archive contains good instructions
  about how to make an export.

[saving]: https://faq.whatsapp.com/en/android/23756533/?category=5245251
