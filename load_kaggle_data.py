import os
from dotenv import load_dotenv
from kaggle.api.kaggle_api_extended import KaggleApi

load_dotenv()

os.environ['KAGGLE_USERNAME'] = 'meisliknoah'
os.environ['KAGGLE_KEY'] = '3196c0a57e50183c1780104f4d98ac9c'

api = KaggleApi()
api.authenticate()

dataset = 'tmdb/tmdb-movie-metadata'

download_path = os.path.join(os.getcwd(), 'tmdb_movie_metadata')

if not os.path.exists(download_path):
    os.makedirs(download_path)

api.dataset_download_files(dataset, path=download_path, unzip=True)

print(f"Dataset downloaded to: {download_path}")
