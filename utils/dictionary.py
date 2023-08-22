import config_data

headers = {
    "X-RapidAPI-Key": config_data.config.RAPID_API_KEY,
    "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
}

headers_image = {
    "content-type": "application/json",
    "X-RapidAPI-Key": config_data.config.RAPID_API_KEY,
    "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
}

url_images = "https://hotels4.p.rapidapi.com/properties/v2/detail"
url_price = "https://hotels4.p.rapidapi.com/properties/v2/list"
url_meta = "https://hotels4.p.rapidapi.com/v2/get-meta-data"
url_get_city = "https://hotels4.p.rapidapi.com/locations/v3/search"

my_calendar = {'y': 'год', 'm': 'месяц', 'd': 'день'}

currencies = ["$", "€", "£", "¥"]