trigramosaurus
==============

scripts to automate trigramosaurus and other qwantz related toys

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

todos
=====

accented characters (at least those used in french)
callout detection
"something went wrong" detection

