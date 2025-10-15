from transformers import pipeline

from award.processor import BaseProcessor
from award.tweet import Award, Tweet


class LMAwardGenerator(BaseProcessor):
    """Generate an award from a tweet."""

    def __init__(self, model_name: str = "deepset/roberta-base-squad2"):
        super().__init__(processor_type="LM award generator")
        self.model_name = model_name
        self.nlp = pipeline("question-answering", model=model_name, tokenizer=model_name)
        self.questions = {
            "winner": "Who is the winner of the award?",
            "nominees": "Who are the nominees of the award?",
            "presenters": "Who are the presenters of the award?",
            "host": "Who is the host of the award?",
        }

    def process(self, tweet: Tweet) -> Award:
        """Generate an award from a tweet.

        Examples:
         return from model:

               {'score': 0.21171437203884125,
                'start': 59,
                'end': 84,
                'answer': 'gives freedom to the user'}
        """
        answers = {}
        for question_type, question in self.questions.items():
            context = {
                "question": question,
                "context": tweet.text,
            }
            answers[question_type] = self.nlp(context)["answer"]

        return Award(**answers)
