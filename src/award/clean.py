import json
import re
tweets = json.load(open("data/gg2013.json"))

for tweet in tweets:
    tweet["text"] = tweet["text"].lower()
    tweet["text"] = re.sub(r"http\S+", "<url>", tweet["text"])
    tweet["text"] = re.sub(r'#', '', tweet["text"])
    tweet["text"] = tweet["text"].replace("rt @", "")
    tweet["text"] = tweet["text"].replace("rt", "")
    tweet["text"] = tweet["text"].replace(":", "")

print(tweets[:10])
# json.dump(tweets, open("data/gg2013_clean.json", "w"))