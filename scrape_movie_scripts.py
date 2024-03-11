import os
import pandas as pd
from tqdm import tqdm
from fuzzywuzzy import process
from string import ascii_uppercase
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from pathlib import Path

IMSDB_BASE_URL = "https://imsdb.com/alphabetical"
KAGGLE_DATASET_CREDITS_PATH = "tmdb_movie_metadata/tmdb_5000_credits.csv"
KAGGLE_DATASET_MOVIES_PATH = "tmdb_movie_metadata/tmdb_5000_movies.csv"
SCRIPT_DIR = "scripts"
ERROR_FILE_PATH = "no_scripts.txt"
MATCH_THRESHOLD = 96

def initialize_webdriver():
    options = Options()
    options.add_argument("--window-size=1920,1080")
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--allow-running-insecure-content')
    options.add_argument("--disable-extensions")
    options.add_argument("--proxy-server='direct://'")
    options.add_argument("--proxy-bypass-list=*")
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
    options.add_argument('--headless')

    driver = webdriver.Chrome(options=options)
    return driver

def scrape_available_movies(driver: webdriver.Chrome):
    letters = ascii_uppercase + '0'
    all_titles = []
    title_urls = []
    for letter in tqdm(letters):
        alphabet_path = Path(IMSDB_BASE_URL) / Path(letter)
        driver.get(str(alphabet_path))
        titles = driver.find_elements(By.CSS_SELECTOR, "td p a")
        
        for title in titles:
            all_titles.append(title.text)
            title_urls.append(title.get_attribute('href'))

    return all_titles, title_urls

def load_movies_from_dataset():
    credits = pd.read_csv(KAGGLE_DATASET_CREDITS_PATH)
    credits.rename(columns={'movie_id': 'id'}, inplace=True)
    credits.drop("title", axis=1, inplace=True)
    movies = pd.read_csv(KAGGLE_DATASET_MOVIES_PATH)
    data = movies.merge(credits, on="id")
    titles = data["title"].to_list()

    return titles

def find_matches(movie_titles, available_movie_titles, script_links):
    edited_movie_titles = [movie_title.replace(", The", "").replace("The", "").strip().replace("  ", " ") for movie_title in movie_titles]
    edited_available_movie_titles = [movie_title.replace(", The", "").replace("The", "").strip().replace("  ", " ") for movie_title in available_movie_titles]

    matches = []
    for i, movie_title in enumerate(tqdm(edited_movie_titles)):
        closest = process.extractOne(movie_title, edited_available_movie_titles)
        if closest[1] >= MATCH_THRESHOLD:
            matches.append((movie_titles[i], script_links[edited_available_movie_titles.index(closest[0])]))
        else:
            error_file_path = Path(ERROR_FILE_PATH)
            with open(error_file_path, "a") as file:
                file.write(movie_titles[i] + "\n")

    return matches

def check_error_file():
    error_file_path = Path(ERROR_FILE_PATH)
    if os.path.isfile(error_file_path):
        os.remove(error_file_path)

def check_script_dir():
    script_dir = Path(SCRIPT_DIR)
    if not os.path.exists(script_dir):
        os.mkdir(script_dir)

def scrape_scripts(driver: webdriver.Chrome, matches):
    script_dir = Path(SCRIPT_DIR)
    error_file_path = Path(ERROR_FILE_PATH)

    for movie_title, script_link in tqdm(matches):
        try:
            driver.get(script_link)
            driver.find_elements(By.CSS_SELECTOR, 'td a')[-1].click()
            script = driver.find_element(By.CLASS_NAME, "scrtext").text

            if len(script) <= 300:
                raise Exception
            
            script_path = script_dir / Path(movie_title + ".txt")
            with open(script_path, "w") as file:
                file.write(script)
        except Exception as e:
            print(e)
            with open(error_file_path, "a") as file:
                file.write(movie_title + ", " + script_link + "\n")
        
if __name__ == "__main__":
    check_error_file()
    check_script_dir()

    movie_titles = load_movies_from_dataset()
    driver = initialize_webdriver()
    available_movies_titles, script_links = scrape_available_movies(driver)
    matches = find_matches(movie_titles, available_movies_titles, script_links)
    scrape_scripts(driver, matches)
