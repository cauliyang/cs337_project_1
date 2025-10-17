import json
import zipfile
import re
import spacy

from rich import print

                   

def test_extract_awards_only():

    with zipfile.ZipFile("data/gg2013.json.zip") as z:
        with z.open("gg2013.json") as f:
            data = json.load(f)
    

    award_pattern = re.compile(r"\b(best [\w\s,-]+?)(?:[.!?]|$)", re.IGNORECASE)
    freq = {}

    for _tweet in data:
        text = _tweet['text']
        if "best" not in text.lower():
            continue

        matches = award_pattern.findall(text)
        for m in matches:
            award = m.strip().lower()
            award = re.sub(r"[-,:]+$", "", award)
            freq[award] = freq.get(award, 0) + 1


    ranked = sorted(freq.items(), key=lambda kv: kv[1], reverse=True)
    
    for award_str, count in ranked[:20]:
        print(f"Award: {award_str}  |  Count: {count}")

    return ranked


def test_get_noms():
    ## could use LM to ask whether the award is for a person or movie etc to inform the entity label (ent.label_)
    award_name = "best supporting actor"
    nlp = spacy.load("en_core_web_sm")

    with zipfile.ZipFile("data/gg2013.json.zip") as z:
        with z.open("gg2013.json") as f:
            data = json.load(f)


    nominee_freq = {}

    for tweet in data:
        text = tweet['text']

        if award_name.lower() not in text.lower():
            continue

        doc = nlp(text)

        # Look for proper nouns (NNP) before or after the award phrase
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                # basic heuristic: entity appears before the award mention
                if ent.start_char < text.lower().find(award_name.lower()):
                    name = ent.text.strip()
                    if name and "@" not in name:
                        nominee_freq[name] = nominee_freq.get(name, 0) + 1

    ranked_nominees = sorted(nominee_freq.items(), key=lambda kv: kv[1], reverse=True)

    for nominee, count in ranked_nominees[:20]:
        print(f"Nominee: {nominee}  |  Count: {count}")

    return ranked_nominees
