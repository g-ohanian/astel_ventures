import json
import re
from abc import ABC, abstractmethod
from logging import getLogger
from typing import Literal

import requests
import spacy
from openai import OpenAI
from spacy.lang.en.stop_words import STOP_WORDS
from transformers import pipeline, GPT2Tokenizer, GPT2LMHeadModel
from transformers.pipelines.token_classification import AggregationStrategy

from asel_ventures.settings import MUSIXMATCH_API_KEY, MUSIXMATCH_URL, OPEN_API_KEY
from songs.errors import MusixmatchException
from utils.fetch_countries import get_country

logger = getLogger(__name__)


class SummaryData:
    def __init__(
            self, source_type: Literal["local", "open_ai"],
            summary: str = "",
            countries: str = "",
            error: str = ""
    ):
        self.__source_type = source_type
        self.__summary = summary
        self.__countries = countries
        self.__error = error

    @property
    def source_type(self) -> str:
        return self.__source_type

    @property
    def summary(self) -> str:
        return self.__summary

    @property
    def countries(self) -> str:
        return self.__countries

    @property
    def error(self) -> str:
        return self.__error

    @error.setter
    def error(self, error) -> None:
        self.__error = str(error)

    @property
    def to_dict(self) -> dict:
        return {
            self.source_type: {
                "summary": self.summary,
                "countries": self.countries,
                "error": self.error
            }
        }


class AbstractSummarizer(ABC):
    @abstractmethod
    def summarize(self, title: str, artist: str) -> SummaryData:
        pass


class SongSummerizerService:
    def __init__(self) -> None:
        self.musixmatch = MusixmatchSummerizer()
        self.openai = OpenAISummerizer()

    def search_for_song(self, title, artist) -> dict:
        summary_data = {}
        try:
            musixmatch_data = self.musixmatch.summarize(title, artist)
        except MusixmatchException as e:
            logger.info(f"Exception in Musixmatch. Error:{e}")
            print(f"Exception in Musixmatch. Error:{e}")
            error = str(e)
            if e.status_code == 404:
                error = ""
            musixmatch_data = SummaryData("local", error=error)

        try:
            openai_data = self.openai.summarize(title, artist)
        except Exception as e:
            logger.info(f"Exception in OpenAI. Error:{e}")
            print(f"Exception in OpenAI. Error:{e}")
            openai_data = SummaryData("open_ai", error=str(e))

        summary_data.update(musixmatch_data.to_dict)
        summary_data.update(openai_data.to_dict)
        return summary_data


class MusixmatchSummerizer(AbstractSummarizer):
    API_KEY = MUSIXMATCH_API_KEY
    MUSIXMATCH_URL = MUSIXMATCH_URL
    ERROR_MESSAGE_MAP = {
        "404": "We have not found lyrics with provided parameters",
        "401": "Unauthorized request",
    }
    DEFAULT_ERROR_MESSAGE = "Something went wrong"

    def summarize(self, title: str, artist: str) -> SummaryData:
        endpoint = "matcher.lyrics.get"
        lyrics = self.__make_get_requests(endpoint, q_track=title, q_artist=artist)
        summary_data = SummaryData(
            source_type="local",
            summary=self.__summarize_lyrics(lyrics),
            countries=self.__extract_countries(lyrics)
        )
        return summary_data

    def __summarize_lyrics(self, lyrics: str) -> str:
        top_keywords = self.get_candidate_labels(lyrics)
        classified_labels = self.classify_lyrics(lyrics, top_keywords)
        summary = self.generate_summary(classified_labels["labels"])
        return summary

    def __extract_countries(self, lyrics: str) -> str:
        ner = pipeline(
            "ner",
            aggregation_strategy=AggregationStrategy.FIRST,
            model="dbmdz/bert-large-cased-finetuned-conll03-english")
        ner_results = ner(lyrics.strip())
        loc_entities = [result["word"] for result in ner_results if result['entity_group'] == 'LOC']
        countries = self.__fetch_countries(loc_entities)
        return ", ".join(countries)

    def get_candidate_labels(self, lyrics) -> list:
        nlp = spacy.load("en_core_web_sm")
        lyrics_doc = nlp(lyrics)
        noun_chunks = [chunk.text.lower() for chunk in lyrics_doc.noun_chunks]
        candidate_labels = {chunk for chunk in noun_chunks if chunk not in STOP_WORDS and len(chunk) > 1}
        candidate_labels = list(candidate_labels)
        filtered_labels = [label for label in candidate_labels if len(label.split()) > 1]
        return filtered_labels

    def classify_lyrics(self, lyrics, candidate_labels) -> list:
        text = lyrics.lower()
        text = re.sub(r'[^\w\s]', '', text)
        classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
        result = classifier(text, candidate_labels, max_length=len(lyrics) + 1, min_length=30, num_beams=4)
        return result

    def generate_summary(self, labels) -> str:
        model_name = "gpt2-medium"
        tokenizer = GPT2Tokenizer.from_pretrained(model_name)
        model = GPT2LMHeadModel.from_pretrained(model_name)
        joined_labels = ' and '.join(labels[0:3])
        prompt_text = f"This song is about {joined_labels}."

        input_ids = tokenizer.encode(prompt_text, return_tensors='pt')
        output = model.generate(
            input_ids,
            max_new_tokens=len(input_ids),
            num_return_sequences=1,
            temperature=1,
            top_k=50
        )

        generated_text = tokenizer.decode(output[0], skip_special_tokens=True)
        return f"{generated_text.split('.')[0]}."

    def __fetch_countries(self, loc_entities) -> list:
        countries_set = set()
        for entity in loc_entities:
            country_name = get_country(entity.strip())
            if not country_name:
                continue
            countries_set.add(country_name)
        return list(countries_set)

    def __make_get_requests(self, endpoint: str, **params) -> str:
        full_uri = f"{self.MUSIXMATCH_URL}{endpoint}"
        params["apikey"] = self.API_KEY
        response = requests.get(full_uri, params=params)
        musixmatch_data = response.json()["message"]
        status_code = musixmatch_data["header"]["status_code"]
        if status_code != 200:
            raise MusixmatchException(
                status_code=status_code,
                message=self.ERROR_MESSAGE_MAP.get(status_code, self.DEFAULT_ERROR_MESSAGE)
            )
        lyrics = musixmatch_data["body"]["lyrics"]["lyrics_body"].split("*")[0]
        return lyrics


class OpenAISummerizer(AbstractSummarizer):
    OPEN_AI_KEY = OPEN_API_KEY

    def summarize(self, title, artist) -> SummaryData:
        client = OpenAI(api_key=self.OPEN_AI_KEY)
        prompt = (f"Provide a one-sentence summary of the song \"{title}\" by \"{artist}\", "
                  f"and please extract all the countries and cities mentioned in song lyrics. "
                  f"If no countries or cities are mentioned in the song lyrics, return an empty string. "
                  f"For cities, please take only the country name they are located in.maal "
                  f"Format the response as json in a format: "
                  f"{{\"summary\": [song meaning], \"countries\": [list of countries]}}. "
                  f"If song was not found summary value should be empty string. "
                  f"If no countries/cities are mentioned, "
                  f"countries value should be empty string.")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": prompt
                }
            ]
        )
        generated_text = response.choices[0].message.content.strip()
        generated_text = json.loads(generated_text)
        generated_text["countries"] = ", ".join(generated_text["countries"])
        return SummaryData("open_ai", **generated_text)
