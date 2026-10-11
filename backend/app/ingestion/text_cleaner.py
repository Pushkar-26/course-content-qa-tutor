import re


def clean_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def join_lines(lines: list[str]) -> str:
    """Join wrapped PDF lines into one paragraph string.

    If a line ends with a hyphen and the next line starts with a lowercase
    letter, the word is glued back together (inter- + national).
    """
    result = ""

    for line in lines:
        line = line.strip()

        if not line:
            continue

        if not result:
            result = line
        elif (
            result.endswith("-")
            and len(result) > 1
            and result[-2].isalpha()
            and line[0].islower()
        ):
            result = result[:-1] + line
        else:
            result = f"{result} {line}"

    return result