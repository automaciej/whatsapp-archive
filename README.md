# whatsapp-archive

Format your exported WhatsApp conversation in HTML.

Use the [Saving your chat history][saving] instructions to export your chat
history. You'll get an email with a .txt file. Save it on disk, and then run
this script.

## Installation

Option 1, pip (any OS with Python 3.9+):

    pip install .

This installs a `whatsapp-archive` command:

    whatsapp-archive -i your_file.txt -o output.html

Option 2, run the script directly without installing, using a virtual
environment:

    python3 -m venv venv
    source venv/bin/activate   # on Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ./whatsapp_archive.py -i your_file.txt -o output.html

Option 3, on Debian, install dependencies as system packages:

   * `python3-dateutil`
   * `python3-jinja2`

then run:

    ./whatsapp_archive.py -i your_file.txt -o output.html

For running the tests, also install the dev requirements:
`pip install -r requirements-dev.txt` (or `python3-parameterized` on Debian).

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
- https://github.com/dsadinoff/whatsapp-archive was the original inspiration
  for RTL/bidi text support (Issue #5); that feature has since been
  implemented natively in this repository.
- https://github.com/djax666/whatsapp-archive contains good instructions
  about how to make an export, plus a heavier reskin with thumbnails,
  avatars, and a jQuery-based media viewer.
- https://github.com/FalkTannhaeuser/whatsapp-archive adds mobile-friendly
  image scaling and a manually-curated table of contents (via an external
  YAML file, not automatic).

[saving]: https://faq.whatsapp.com/en/android/23756533/?category=5245251
