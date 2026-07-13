from analysis.keywords import keyword_score


def calculate(listing):

    score=0

    text = (
        listing["title"]
        +" "
        +listing["description"]
    )


    score += keyword_score(text)


    if listing["price"] < 100:
        score += 20


    return score