import json
import sys
import time
from locale import getdefaultlocale
from pathlib import Path

from albert import (  # noqa: E402, pylint: disable=import-error
    Action,
    Item,
    Query,
    QueryHandler,
    configLocation,
    setClipboardText,
    warning,
)


sys.path.append(str(Path(__file__).parent))  # isort: skip

# pylint: disable=wrong-import-position
from google_trans_new.constant import LANGUAGES  # noqa: E402
from google_trans_new.google_trans_new import google_translator  # noqa: E402


md_iid = '0.5'
md_version = '1.0'
md_name = 'Google Translate Steven'
md_description = 'Translate sentences using Google Translate'
md_url = 'https://github.com/stevenxxiu/albert_google_translate_steven'
md_maintainers = '@stevenxxiu'

ICON_PATH = str(Path(__file__).parent / 'icons/google_translate.png')


class Plugin(QueryHandler):
    translator: google_translator | None = None
    language: str | None = None
    synonyms: dict[str, str] = {}

    def id(self) -> str:
        return __name__

    def name(self) -> str:
        return md_name

    def description(self) -> str:
        return md_description

    def defaultTrigger(self) -> str:
        return 'tr '

    def synopsis(self) -> str:
        return '[[src] dest] text'

    def initialize(self) -> None:
        self.synonyms = LANGUAGES
        with (Path(configLocation()) / __name__ / 'settings.json').open() as sr:
            self.synonyms = json.load(sr)
            for dest in self.synonyms.values():
                if dest not in LANGUAGES:
                    warning(f'Invalid language: {dest}')
                    continue

        self.translator = google_translator()
        self.language = getdefaultlocale()[0][0:2]

    def get_lang_with_synonym(self, lang: str) -> str:
        return self.synonyms.get(lang, lang)

    def handleQuery(self, query: Query) -> None:
        query_str = query.string.strip()
        if not query_str:
            return

        # Avoid rate limiting
        for _ in range(50):
            time.sleep(0.01)
            if not query.isValid:
                return

        lang_src = None
        lang_tgt, text = self.language, query_str
        splits = text.split(maxsplit=1)
        if len(splits) > 1 and self.get_lang_with_synonym(splits[0]) in LANGUAGES:
            lang_tgt, text = self.get_lang_with_synonym(splits[0]), splits[1]
            splits = text.split(maxsplit=1)
            if len(splits) > 1 and self.get_lang_with_synonym(splits[0]) in LANGUAGES:
                lang_src = lang_tgt
                lang_tgt, text = self.get_lang_with_synonym(splits[0]), splits[1]

        if lang_src:
            translate_text = self.translator.translate(text, lang_src=lang_src, lang_tgt=lang_tgt)
        else:
            translate_text = self.translator.translate(text, lang_tgt=lang_tgt)

        query.add(
            Item(
                id=f'{md_name}/copy',
                text=translate_text,
                subtext=(
                    f'From {LANGUAGES[lang_src]} to {LANGUAGES[lang_tgt]}' if lang_src else f'To {LANGUAGES[lang_tgt]}'
                ),
                icon=[ICON_PATH],
                actions=[
                    Action(
                        f'{md_name}/copy',
                        'Copy result to clipboard',
                        lambda translate_text_=translate_text: setClipboardText(translate_text_),
                    )
                ],
            )
        )
