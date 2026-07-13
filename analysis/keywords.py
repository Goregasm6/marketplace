import json


with open("data/keywords.json") as f:
    keywords=json.load(f)


def keyword_score(text):

    text=text.lower()

    score=0

    for word in keywords["high_value"]:
        if word in text:
            score += 10


    for word in keywords["repair"]:
        if word in text:
            score += 5


    for word in keywords["danger"]:
        if word in text:
            score -= 20


    return score