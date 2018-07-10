# whatsapp-archive

Format your exported WhatsApp conversation in HTML.

Use the [Saving your chat history][saving] instructions to export your chat
history. You'll get an email with a .txt file. Save it on disk, and then run
this script.

Requirements:

   * python3-dateutil (on Debian)
   * python2-jinja2

On Linux, run this in shell. On Windows, run this in cmd.

    ./whatsapp_archive.py -i your_file.txt -o output.html

[saving]: https://faq.whatsapp.com/en/android/23756533/?category=5245251
