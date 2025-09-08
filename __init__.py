import json
import sys
import time
from locale import getlocale
from pathlib import Path
from typing import Callable, override

from albert import setClipboardText  # pyright: ignore[reportUnknownVariableType]
from albert import (
    Action,
    Item,
    PluginInstance,
    Query,
    StandardItem,
    TriggerQueryHandler,
)

setClipboardText: Callable[[str], None]

sys.path.append(str(Path(__file__).parent))  # isort: skip

# pylint: disable=wrong-import-position
from google_trans_new.constant import LANGUAGES  # noqa: E402
from google_trans_new.google_trans_new import google_translator  # noqa: E402

_default_warning: Callable[[str], None] = lambda _: None  # noqa: E731
warning: Callable[[str], None] = globals().get('warning', _default_warning)  # pyright: ignore[reportAny]

md_iid = '3.0'
md_version = '1.4'
md_name = 'Google Translate Steven'
md_description = 'Translate sentences using Google Translate'
md_license = 'MIT'
md_url = 'https://github.com/stevenxxiu/albert_google_translate_steven'
md_authors = ['@stevenxxiu']

ICON_URL = f'file:{Path(__file__).parent / "icons/google_translate.png"}'


class Plugin(PluginInstance, TriggerQueryHandler):
    translator: google_translator | None = None
    language: str | None = None
    synonyms: dict[str, str] = {}

    def __init__(self):
        PluginInstance.__init__(self)
        TriggerQueryHandler.__init__(self)

        self.synonyms = LANGUAGES
        with (Path(self.configLocation()) / 'settings.json').open() as sr:
            self.synonyms = json.load(sr)
            for dest in self.synonyms.values():
                if dest not in LANGUAGES:
                    warning(f'Invalid language: {dest}')
                    continue

        self.translator = google_translator()
        language_code = getlocale()[0]
        assert language_code is not None
        self.language = language_code[0:2]

    @override
    def synopsis(self, _query: str) -> str:
        return '[[src] dest] text'

    @override
    def defaultTrigger(self):
        return 'tr '

    def get_lang_with_synonym(self, lang: str) -> str:
        return self.synonyms.get(lang, lang)

    @override
    def handleTriggerQuery(self, query: Query) -> None:
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
        assert lang_tgt is not None

        splits = text.split(maxsplit=1)
        if len(splits) > 1 and self.get_lang_with_synonym(splits[0]) in LANGUAGES:
            lang_tgt, text = self.get_lang_with_synonym(splits[0]), splits[1]
            splits = text.split(maxsplit=1)
            if len(splits) > 1 and self.get_lang_with_synonym(splits[0]) in LANGUAGES:
                lang_src = lang_tgt
                lang_tgt, text = self.get_lang_with_synonym(splits[0]), splits[1]

        assert self.translator is not None
        translate_texts: str | list[str] = (  # pyright: ignore[reportUnknownVariableType]
            self.translator.translate(text, lang_src=lang_src, lang_tgt=lang_tgt)  # pyright: ignore[reportUnknownMemberType]
            if lang_src
            else self.translator.translate(text, lang_tgt=lang_tgt)  # pyright: ignore[reportUnknownMemberType]
        )

        if isinstance(translate_texts, str):
            translate_texts = [translate_texts]

        items: list[Item] = []
        for translate_text in translate_texts:  # pyright: ignore[reportUnknownVariableType]
            assert isinstance(translate_text, str)
            copy_call: Callable[[str], None] = lambda value_=translate_text: setClipboardText(value_)  # noqa: E731
            item = StandardItem(
                id=f'{md_name}/copy',
                text=translate_text,
                subtext=(
                    f'From {LANGUAGES[lang_src]} to {LANGUAGES[lang_tgt]}' if lang_src else f'To {LANGUAGES[lang_tgt]}'
                ),
                iconUrls=[ICON_URL],
                actions=[
                    Action(
                        f'{md_name}/copy',
                        'Copy result to clipboard',
                        copy_call,
                    )
                ],
            )
            items.append(item)
        query.add(items)  # pyright: ignore[reportUnknownMemberType]
