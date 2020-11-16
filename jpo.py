import re as _re
from unidecode import unidecode
# import nltk
# stopwords = nltk.download()
#
# stop_words = stopwords.words("english")


class Tag:
    def __init__(self, begin_tag: str, end_tag:str):
        self.begin = begin_tag
        self.end = end_tag


class TextTools:
    @classmethod
    def lower(cls, text: str) -> str:
        return text.lower()

    @classmethod
    def remove_unicode(cls, text: str) -> str:
        text = unidecode(text)
        return cls.trim_regex(text.encode('ascii', 'ignore').decode(), "\[\?\]")

    @classmethod
    def remove_stopwords(cls, text: str, stopwords: list) -> str:
        return " ".join([i for i in text.strip().split() if i not in stopwords])

    @classmethod
    def normalize_whitespaces(cls, text: str) -> str:
        return " ".join(text.strip().split())

    @classmethod
    def normalize_letters(cls, text: str, min_len=2, do_read_check=True) -> str:
        return " ".join([
            i for i in text.strip().split() if (
                    len(i) > min_len and
                    (cls.is_human_readable(i) if do_read_check else True)
            )
        ])

    @classmethod
    def trim_tag(cls, text: str, tags: Tag) -> str:
        reg = "<\s*"+ tags.begin +"\s*>(.*?)<\s*\/\s*" + tags.end + "\s*>"
        return cls.trim_regex(text, reg)

    @classmethod
    def trim_regex(cls, text: str, regex: str, replace='', flags=0) -> str:
        return _re.sub(regex, replace, text, flags=flags)

    @staticmethod
    def is_human_readable(text: str, min_letter_count=.5) -> bool:
        """
        Guess if a string is human readable
        :param min_letter_count: ratio between 1 and 0. .5 mean 50% characters of string has to be letters
        """
        return sum(c.isalpha() for c in text) > min_letter_count*len(text)


class NLPTools:
    @classmethod
    def ngrams(cls, text: str, n: int) -> list:
        return [tuple(text[i:i+n]) for i in range(len(text)-n+1)]

    @classmethod
    def count_grams(cls, grams: list) -> list:
        uniq = list(set(grams))
        return [(i, grams.count(i)) for i in uniq]

    @classmethod
    def sort_grams(cls, grams: list) -> list:
        return sorted(grams, key=lambda x: x[1], reverse=True)


class Fonctionnels:
    def __init__(self):
        self._stopwords = []

    @classmethod
    def load(cls, filename='fonctionnels_en.txt') -> 'Fonctionnels':
        _cls = cls()
        with open(filename, 'r') as f:
            l = f.readlines()
            _cls.parse(l)
        return _cls

    def parse(self, words_list: list) -> None:
        for line in words_list:
            l = line.strip()
            if l.startswith("#"):
                continue
            if len(l) < 1:
                continue
            self._stopwords.append(l)

    @property
    def stopwords(self) -> list:
        return self._stopwords


class JPCOParser:
    KEYWORDS_HEADER = "KEYWORDS\t"
    HEADER_REGEX = "^[A-Z]+\t(.*?)\n"
    TAGS = [
        Tag("tex-math", "tex-math"),
        Tag("mml:math", "math")
    ]
    IGNORES_REGEX = [
        "\[\s*[0-9\-,\s\?]+\s*\]",
        "\\\\\\(\s*\\\\\\)",
        "\\([\w\s\\.]+\\)",
        "__SECTION__"
    ]

    def __init__(self):
        self.keywords = []
        self._text = ""
        self._original_text = ""
        self.stop_words = []

    @classmethod
    def from_text(cls, text: str) -> 'JPCOParser':
        _cls = cls()
        _cls._text = text
        return _cls

    def parse_keywords(self) -> 'JPCOParser':
        self.keywords.extend([j.strip() for j in sum([j.replace(self.KEYWORDS_HEADER, "", 1).split(";") for j in [i for i in self._text.split("\n") if i.startswith(self.KEYWORDS_HEADER)]], [])])
        return self

    def set_stopwords(self, stopwords: list) -> 'JPCOParser':
        self.stop_words = stopwords
        return self

    def clean(self) -> 'JPCOParser':
        self._original_text = self._text
        text = self._text

        text = TextTools.trim_regex(text, self.HEADER_REGEX, flags=_re.MULTILINE|_re.DOTALL)

        for tag in self.TAGS:
            text = TextTools.trim_tag(text, tag)

        for regex in self.IGNORES_REGEX:
            text = TextTools.trim_regex(text, regex)

        text = TextTools.remove_unicode(text)
        text = TextTools.normalize_whitespaces(text)
        text = TextTools.normalize_letters(text)
        text = TextTools.remove_stopwords(text, self.stop_words)

        self._text = text
        return self

stop_words = Fonctionnels.load().stopwords

with open("10_JPCO/jpco_1_1_011001.txt", "r", encoding="utf-8", errors="ignore") as f:
    l = f.readlines()

parser = JPCOParser().from_text("".join(l)).parse_keywords().set_stopwords(stop_words).clean()

print(parser.keywords)
print(parser._text)

N_TOP = 20

text = TextTools.lower(parser._text)

NGRAMS = [3, 8, 16, 24]

for n in NGRAMS:
    all_n_grams = NLPTools.ngrams(text, n)
    counted_n_grams = NLPTools.count_grams(all_n_grams)
    sorted_n_grams = NLPTools.sort_grams(counted_n_grams)
    top_n = sorted_n_grams[:N_TOP]
    print(f"Top {N_TOP} {n}-grams: ", " ,".join(["\'{0}\'".format(''.join(i[0])) for i in top_n]))

words = [tuple(i) for i in text.strip().split()]
counted_words = NLPTools.count_grams(words)
sorted_words = NLPTools.sort_grams(counted_words)
top_n = sorted_words[:N_TOP]
print(f"Top {N_TOP} words: ", " ,".join(["\'{0}\'".format(''.join(i[0])) for i in top_n]))
