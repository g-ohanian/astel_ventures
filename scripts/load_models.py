from transformers import pipeline, GPT2Tokenizer, GPT2LMHeadModel
from transformers.pipelines.token_classification import AggregationStrategy


def load_models():
    pipeline(
        "ner",
        aggregation_strategy=AggregationStrategy.FIRST,
        model="dbmdz/bert-large-cased-finetuned-conll03-english")

    pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

    model_name = "gpt2-medium"
    GPT2Tokenizer.from_pretrained(model_name)
    GPT2LMHeadModel.from_pretrained(model_name)


if __name__ == '__main__':
    load_models()
