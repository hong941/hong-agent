import re


def tokenize(text: str) -> list[str]:
    text = text.lower()
    tokens = re.findall(r"[a-z0-9]+", text)
    chinese_segments = re.findall(r"[\u4e00-\u9fff]+", text)
    for segment in chinese_segments:
        if len(segment) == 1:
            tokens.append(segment)
        else:
            tokens.append(segment)
            tokens.extend(segment[i : i + 2] for i in range(len(segment) - 1))
    return tokens
