import os
import requests
import random
import hashlib
import json
from urllib.parse import urlparse, urlunparse, quote_plus
from datetime import datetime, timedelta
import time
import colorlog
import logging

# Constants and Paths
downloaded_urls_file = '/Users/jamestan/Desktop/downloaded_urls.json'
API_KEY = '48852575-5c62366bc6446d03b9d38d30d'
API_URL = "https://pixabay.com/api/"
cities = {}

# GeoNames API setup
GEO_NAMES_API_URL = 'http://api.geonames.org/citiesJSON'
GEO_NAMES_API_KEY = 'xxxxxxxxxxxxxxxxx'

# Load previously downloaded URLs
if os.path.exists(downloaded_urls_file):
    with open(downloaded_urls_file, 'r') as f:
        downloaded_urls = json.load(f)
else:
    downloaded_urls = []

# Set up colored logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Create the API logging handler and set up the formatter
formatter = colorlog.ColoredFormatter(
    '%(log_color)s%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'bold_red',
    }
)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Fetch cities data from the GeoNames API
def fetch_city_data():
    global cities
    try:
        response = requests.get(GEO_NAMES_API_URL, params={
            'lang': 'en',
            'username': GEO_NAMES_API_KEY,
            'north': 90,
            'south': -90,
            'east': 180,
            'west': -180,
            'maxRows': 1000
        })
        if response.status_code == 200:
            data = response.json()
            for city in data['geonames']:
                city_name = city['name']
                lat = float(city['lat'])
                lon = float(city['lng'])
                cities[city_name] = {"lat_min": lat - 0.1, "lat_max": lat + 0.1, "lon_min": lon - 0.1, "lon_max": lon + 0.1}
            logger.info(f"Fetched {len(cities)} cities from GeoNames API.")
        else:
            logger.error(f"Failed to fetch cities. Status code: {response.status_code}")
    except Exception as e:
        logger.error(f"Error fetching cities: {e}")

# Function to fetch images using Pixabay API
def fetch_images_from_pixabay(query, num_images=1, per_page=20):
    all_images = []
    total_images_fetched = 0
    page = random.randint(1, 10)

    if per_page < 3:
        per_page = 3
    elif per_page > 200:
        per_page = 200

    while total_images_fetched < num_images:
        params = {
            'key': API_KEY,
            'q': quote_plus(query),
            'image_type': 'photo',
            'orientation': 'horizontal',
            'category': 'animals',
            'per_page': per_page,
            'page': page,
            'safesearch': 'true',
        }

        request_url = API_URL + "?" + "&".join([f"{key}={value}" for key, value in params.items()])
        response = requests.get(request_url)

        if response.status_code == 200:
            data = response.json()
            hits = data['hits']

            for hit in hits:
                img_url = hit['webformatURL']
                standarized_url = standarize_url(img_url)

                if standarized_url not in downloaded_urls:
                    all_images.append(standarized_url)
                    downloaded_urls.append(standarized_url)
                    total_images_fetched += 1
                    if total_images_fetched >= num_images:
                        break

            page += 1
        else:
            logger.error(f"Failed to fetch data from Pixabay. Status code: {response.status_code}")
            break

    # Save updated list of downloaded URLs
    with open(downloaded_urls_file, 'w') as f:
        json.dump(downloaded_urls, f)

    return all_images

# Standarize URL to avoid duplicates
def standarize_url(url):
    parsed_url = urlparse(url)
    parsed_url = parsed_url._replace(query='')
    return urlunparse(parsed_url)

# Generate random location within a city's bounding box or totally random location
def generate_random_location():
    # Define a high chance to select a city (90% chance)
    if random.random() < 0.9 and cities:
        city_name = random.choice(list(cities.keys()))
        city = cities[city_name]
        lat = random.uniform(city["lat_min"], city["lat_max"])
        lon = random.uniform(city["lon_min"], city["lon_max"])
        logger.info(f"Selected city: {city_name} (Lat: {lat}, Lon: {lon})")
    else:
        # Generate a completely random location (10% chance)
        lat = random.uniform(-90, 90)
        lon = random.uniform(-180, 180)
        logger.info(f"Generated random location: (Lat: {lat}, Lon: {lon})")
    return lat, lon

# Generate random time between 2024/11/11 and 2025/02/14, from 7 AM to 10 PM
def generate_random_time():
    start_date = datetime(2024, 11, 11, 7, 0)
    end_date = datetime(2025, 2, 14, 22, 0)
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    random_time = start_date + timedelta(days=random_days)
    random_minutes = random.randint(7 * 60, 22 * 60)
    random_time = random_time.replace(hour=random_minutes // 60, minute=random_minutes % 60)
    return random_time.strftime("%Y-%m-%d %H:%M:%S")

# Create a random photo marker
def generate_random_photo_marker():
    animal_images = fetch_images_from_pixabay("animals", num_images=1, per_page=1)
    if not animal_images:
        return None

    img_url = animal_images[0]
    lat, lon = generate_random_location()
    time = generate_random_time()

    photo_id = hashlib.md5(img_url.encode('utf-8')).hexdigest()

    marker = {
        "markerId": photo_id,
        "position": {"latitude": lat, "longitude": lon},
        "photoUrl": img_url,
        "time": time
    }

    return marker

if __name__ == "__main__":
    fetch_city_data()  # Fetch city data
    while True:
        marker = generate_random_photo_marker()
        if marker:
            logger.info(f"Generated Marker: {json.dumps(marker)}")

        time.sleep(random.uniform(1, 2))
