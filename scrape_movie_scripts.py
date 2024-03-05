import string
import os
import pandas as pd
from tqdm import tqdm
from fuzzywuzzy import process
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from pathlib import Path

IMSDB_BASE_URL = "https://imsdb.com/alphabetical"
KAGGLE_DATASET_CREDITS_PATH = "tmdb_movie_metadata/tmdb_5000_credits.csv"
KAGGLE_DATASET_MOVIES_PATH = "tmdb_movie_metadata/tmdb_5000_movies.csv"

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
    letters = string.ascii_uppercase + '0'
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

if __name__ == "__main__":
    movie_titles = load_movies_from_dataset()
    driver = initialize_webdriver()
    available_movies_titles, script_links = scrape_available_movies(driver)

    matches = []
    for movie_title in tqdm(movie_titles):
        closest = process.extractOne(movie_title, available_movies_titles)
        if closest[1] >= 95:
            matches.append((movie_title, script_links[available_movies_titles.index(closest[0])]))

    print(len(matches))

    # script_dir = Path("scripts")
    # if not os.path.exists(script_dir):
    #     os.mkdir(script_dir)

    # error_file_path = Path("no_scripts.txt")
    # if os.path.isfile(error_file_path):
    #     os.remove(error_file_path)

    # for i, title_path in enumerate(tqdm(title_paths)):
    #     try:
    #         script_web_path = str(base_url / Path(title_path))
    #         driver.get(script_web_path)
    #         script = driver.find_element(By.CLASS_NAME, "scrtext")

    #         if len(script.text) <= 57:
    #             raise Exception
            
    #         script_path = script_dir / Path(titles[i] + ".txt")
    #         with open(script_path, "w") as file:
    #             file.write(script.text)
    #     except:
    #         with open(error_file_path, "a") as file:
    #             file.write(titles[i] + "\n")




