import json
import random
import zipfile
import re
import spacy

from rich import print

from award.extract import Extractor
from award.processor import ProcessorPipeline
from award.processors import (
    EmptyTextFilter,
    FtfyCleaner,
    LanguageFilter,
    SpaceCombinationCleaner,
    UnidecodeCleaner,
    UrlCleaner,
)
from award.processors.transformer import HashTagExtractionTransformer, TagUsernameTransformer


def test_extracting_toolittle():
    pipeline = ProcessorPipeline(
        [
            FtfyCleaner(),
            UnidecodeCleaner(),
            SpaceCombinationCleaner(),
            UrlCleaner(),

            EmptyTextFilter(),
            LanguageFilter(language="en"),
            HashTagExtractionTransformer(),  # extract and remove hashtags from text
            TagUsernameTransformer(),  # transform hashtags and usernames to human-readable format
        ]
    )
    extractor = Extractor("data/gg2013.json.zip", pipeline=pipeline)

    award_pattern = re.compile(r"(best .+?)(?:!|\?|$)", re.IGNORECASE)

    spacy_model = spacy.load("en_core_web_sm")

    count = 0
    for _tweet in extractor.extract():
        text = _tweet.text
        matches = award_pattern.findall(text)
        if matches:
            spacy_output = spacy_model(text)
            winner = ''
            award = ''
            for chunk in spacy_output.noun_chunks:
                head_lemma = chunk.root.head.lemma_
                dep = chunk.root.dep_

                # Subject = winner
                if head_lemma in ("win", "nominate") and dep in ("nsubj", "nsubjpass"):
                    winner = chunk.text

                # Direct object or prepositional object
                if head_lemma in ("win", "nominate") and dep in ("dobj", "pobj"):
                    # Check for 'for' prep → award
                    for prep in [c for c in chunk.root.children if c.dep_ == "prep" and c.text.lower() == "for"]:
                        for pobj in [t for t in prep.children if t.dep_ == "pobj"]:
                            # full multi-word award
                            award = " ".join([tok.text for tok in pobj.subtree])
                    
                    # If no 'for', take the chunk text itself (for X wins Y)
                    if not award:
                        award = chunk.text

            # Combine into [before, after]
            pair = [winner, award]
            if(pair[0] != '' and pair[1] != ''):
                count += 1
                print(text)
                print(pair)  # ['Christoph Waltz', 'Best Supporting Actor']'''
            
        if count > 100:
            break

    

def test_extract_toomuch():
    pipeline = ProcessorPipeline(
        [
            FtfyCleaner(),
            UnidecodeCleaner(),
            SpaceCombinationCleaner(),
            UrlCleaner(),

            EmptyTextFilter(),
            LanguageFilter(language="en"),
            HashTagExtractionTransformer(),  # extract and remove hashtags from text
            TagUsernameTransformer(),  # transform hashtags and usernames to human-readable format
        ]
    )
    extractor = Extractor("data/gg2013.json.zip", pipeline=pipeline)

    award_pattern = re.compile(r"(best .+?)(?:!|\?|$)", re.IGNORECASE)

    spacy_model = spacy.load("en_core_web_sm")

    count = 0
    VERBS = {"win", "wins", "won", "nominate", "nominates", "nominated"}
    for _tweet in extractor.extract():
        text = _tweet.text
        matches = award_pattern.findall(text)
        if matches:
            spacy_output = spacy_model(text)
            winner = ''
            winner = None
            award_tokens = []


            # --- Step 1: find subject (winner) ---
            for chunk in spacy_output.noun_chunks:
                head_lemma = chunk.root.head.lemma_
                dep = chunk.root.dep_
                if head_lemma in ("win", "nominate") and dep in ("nsubj", "nsubjpass"):
                    winner = chunk.text
                    break  # first subject is usually enough

            # --- Step 2: find the award span ---
            for token in spacy_output:
                if token.lemma_.lower() in {"win", "nominate"}:
                    # everything after the verb in the sentence
                    start = token.i + 1
                    # collect tokens until punctuation or end
                    award_span = []
                    for t in spacy_output[start:]:
                        if t.is_punct:
                            break
                        award_span.append(t.text)
                    award_tokens.extend(award_span)
                    break  # only first relevant verb

            # --- Step 3: clean award string ---
            award_text = " ".join(award_tokens)

            # remove common filler like "the award for"
            fillers = ["the award for", "the award"]
            for f in fillers:
                if award_text.lower().startswith(f):
                    award_text = award_text[len(f):].strip()

            # Combine into [before, after]
            pair = [winner, award_text]
            if(pair[0] != '' and pair[1] != ''):
                count += 1
                print(text)
                print(pair)  # ['Christoph Waltz', 'Best Supporting Actor']'''
            
        if count > 300:
            break
