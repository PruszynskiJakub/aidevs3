import requests

import api


def fetch_data() -> [str]:
    response = requests.get(
        url="https://poligon.aidevs.pl/dane.txt"
    )
    # Split the response text by new lines to create a list of strings
    string_list = response.text.strip().split('\n')
    # Transform the list into a numpy array
    print(f'Fetch data result {string_list}')
    return string_list


api.answer(task="POLIGON", response=fetch_data())
