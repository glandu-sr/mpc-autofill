import re
import string


def text_to_list(input_text: str) -> list[int]:
    # Helper function to translate strings like "[2, 4, 5, 6]" into lists
    if input_text == "":
        return []
    return [int(x) for x in input_text.strip("][").replace(" ", "").split(",")]


def fix_whitespace(input_str: str) -> str:
    # Replace any consecutive whitespace characters by a single splace and strip the string
    return re.sub(r"\s+", " ", input_str).strip()


def to_searchable(input_str: str) -> str:
    if not input_str:
        return ""

    # Convert a card name to a search-friendly string
    # First, convert to lowercase
    input_str = input_str.lower()

    # Remove text inside brackets
    input_str = re.sub(r"[\(\[].*?[\)\]]", "", input_str)

    # Remove hyphens and substitute right apostrophes (’) for single quotes (')
    input_str = input_str.replace("-", " ").replace("’", "'")

    # Remove punctuation
    input_str = input_str.translate(str.maketrans("", "", string.punctuation))

    # Remove all digits
    input_str = input_str.translate(str.maketrans("", "", string.digits))

    # Fix whitespace
    input_str = fix_whitespace(input_str)

    return input_str


__all__ = ["text_to_list", "fix_whitespace", "to_searchable"]
