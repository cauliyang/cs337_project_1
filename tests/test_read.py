import json
import zipfile

from rich import print

from award.extract import Extractor


def test_read_zip_json():
    with zipfile.ZipFile("data/gg2013.json.zip") as z:
        file_name = z.namelist()[0]
        with z.open(file_name) as f:
            data = json.load(f)
    print(data[:10])


def test_extract():
    extractor = Extractor("data/gg2013.json.zip", [], [])
    count = 0
    for tweet in extractor.extract():
        print(tweet)
        count += 1
        if count > 10:
            break
