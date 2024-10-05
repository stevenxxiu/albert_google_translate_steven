# Albert Launcher Google Translate Extension
Translate sentences using *Google Translate*.

## Install
To install, copy or symlink this directory to `~/.local/share/albert/python/plugins/google_translate_steven/`.

## Config
Config is stored in `~/.config/albert/albert.google_translate_steven/settings.json`.

Synonyms can be added for languages in `google_trans_new.constant`.

Example config:

```json
{
  "cn": "zh-cn"
}
```

## Development Setup
To setup the project for development, run:

    $ cd google_translate_steven/
    $ pre-commit install --hook-type pre-commit --hook-type commit-msg

To lint and format files, run:

    $ pre-commit run --all-files
