import random
import string
import urllib.parse

from unidecode import unidecode

from .config import WORDS_FILE_PATH
from .log import LOG

with open(WORDS_FILE_PATH) as f:
    LOG.d("load words file: %s", WORDS_FILE_PATH)
    _words = f.read().split()


def random_word():
    return random.choice(_words)


def random_words():
    """Generate a random words. Used to generate user-facing string, for ex email addresses"""
    nb_words = random.randint(2, 3)
    return "_".join([random.choice(_words) for i in range(nb_words)])


def random_string(length=10):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for _ in range(length))


def convert_to_id(s: str):
    """convert a string to id-like: remove space, remove special accent"""
    s = s.replace(" ", "")
    s = s.lower()
    s = unidecode(s)
    return s


def encode_url(url):
    return urllib.parse.quote(url, safe="")
