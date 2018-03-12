# Contributing to MyNotes

First, thank you for your interest in MyNotes. I would especially
appreciate help to translate MyNotes into more languages.

## Translation guidelines

I use gettext to manage the internationalization of my program.
Below are the steps to create a translation and compile it and submit a pull request:

1. Fork MyNotes and create a new branch (called `translation_<lang>` for instance)

2. Create the `<lang>.po` translation file from `MyNotes.pot` (in the `/po` folder):

```bash
    $ msginit --input=po/MyNotes.pot --locale=<lang> --output=po/<lang>.po
```

3. Translate the strings, for instance:

```
    msgid "Title"
    msgstr "<translation>"
```

4. Compile the translation file `<lang>.po`:

```bash
    $ mkdir -p mynoteslib/locale/<lang>/LC_MESSAGES
    $ msgfmt --output-file=mynoteslib/locale/<lang>/LC_MESSAGES/MyNotes.mo po/<lang>.po
```

5. Add the language in the `LANGUAGES` dictionary in `mynoteslib/constantes.py` (line 193):
   for instance, for the German translation, add `"de": "Deutsch"`.

6. Submit a pull request