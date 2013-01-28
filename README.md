trigramosaurus
==============

scripts to automate trigramosaurus and other qwantz related toys

There is a nascent option to batch analyze a directory full of dinosaur comics. It will save the text from each comic into a database with this schema:

database schema

    create table comics(
      id integer primary key,
      filename text);

    create table lines(
      id integer primary key,
      comic_id integer,
      panel_id integer,
      line_id integer,
      line text);

This schema will be changed once I know who is talking using callout detection.

WIPs
====

accented characters (at least those used in french)
  grave e and acute e done because they're in my test suite

callout detection
  works

"something went wrong" detection ✓
  need a proper/standard way to report this

todos
=====

recursive callouts

hyphenation detection
