import json
from os.path import join, dirname

from django.core.cache import cache


def load_city_data():
    with open(join(dirname(__file__), 'cities.json'), 'r') as file:
        return json.load(file)


def get_country(location):
    location = location.lower()
    country_data = cache.get('country_data')
    if not country_data:
        country_data = load_city_data()
        cache.set('country_data', country_data, timeout=None)

    for data in country_data:
        country_name = data['country_name'].lower()
        if country_name == location:
            return data['country_name']
        city_name = data['name'].lower()
        if city_name == location or location == " ".join(city_name.split(" ")[0:2]):
            return data['country_name']

    return None
