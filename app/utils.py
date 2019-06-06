import random
import string

from unidecode import unidecode


def random_string(length=10):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for _ in range(length))


def convert_to_id(string: str):
    """convert a string to id-like: remove space, remove special accent"""
    string = string.replace(" ", "")
    string = string.lower()
    string = unidecode(string)
    return string
