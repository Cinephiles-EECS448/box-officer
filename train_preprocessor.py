import json
import pandas as pd
from collections import defaultdict

CREDITS_PATH = "tmdb_movie_metadata/tmdb_5000_credits.csv"
MOVIES_PATH = "tmdb_movie_metadata/tmdb_5000_movies.csv"

class cast_member:
    def __init__(self, name, character, gender):
        self.name = name
        self.character = character
        self.gender = gender

class crew_member:
    def __init__(self, name, job, department):
        self.name = name
        self.job = job
        self.department = department

def load_data(credits_path, movies_path):
    credits = pd.read_csv(credits_path)
    credits.rename(columns={'movie_id': 'id'}, inplace=True)
    credits.drop("title", axis=1, inplace=True, )
    movies = pd.read_csv(movies_path)
    data = movies.merge(credits, on="id")

    data = data[data['revenue'] != 0]
    data = data[data['budget'] != 0]

    return data

def convert_dict_to_1d_list(json_str):
    json_dict = json.loads(json_str)
    return_list = []
    for item in json_dict:
        return_list.append(item['name'])
    return return_list

def convert_dict_to_class_list(json_str, class_type, dimension1, dimension2, dimension3='none'):
    json_dict = json.loads(json_str)
    return_list = []
    for item in json_dict:
        if class_type == 'cast_members':
            gender = item.get(dimension3, None)
            tmp_person = cast_member(item[dimension1], item[dimension2], gender)
            return_list.append(tmp_person)
        elif class_type == 'crew_members':
            department = item.get(dimension3, None)
            tmp_person = crew_member(item[dimension1], item[dimension2], department)
            return_list.append(tmp_person)
    return return_list

def get_director(crew_list):
    for item in crew_list:
        if item.job == 'Director':
            return item.name
    return 'none'

def get_crew_member_count_by_job(crew_list, job_type):
    crew_member_count = 0
    for item in crew_list:
        if job_type in item.job:
            crew_member_count += 1
    return crew_member_count

def get_department_size(crew_list, department):
    department_size = 0
    for item in crew_list:
        if department in item.department:
            department_size += 1
    return department_size

def get_cast_number(cast_list, gender):
    cast_count = 0
    for item in cast_list:
        if str(item.gender) == str(gender):
            cast_count += 1
    return cast_count

def organize_data(data):
    x = data.copy()

    x['genres']  =  x['genres'].apply(convert_dict_to_1d_list)
    x['keywords'] = x['keywords'].apply(convert_dict_to_1d_list)
    x['production_companies'] = x['production_companies'].apply(convert_dict_to_1d_list)
    x['production_countries'] = x['production_countries'].apply(convert_dict_to_1d_list)

    x['country'] = x['production_countries'].apply(lambda x:x[0] if len(x)>0 else None)

    x['cast'] = x['cast'].apply(convert_dict_to_class_list,
                                                                args=('cast_members', 'name', 'character', 'gender'))
    x['crew'] = x['crew'].apply(convert_dict_to_class_list,
                                                                args=('crew_members', 'name', 'job', 'department'))

    x['director_name'] = x['crew'].apply(get_director)

    x['dominant_genre'] = x['genres'].apply(lambda x:x[0] if len(x)>0 else 'none')

    x['title_year'] = pd.to_datetime(x['release_date']).apply(lambda x:0 if pd.isnull(x.year) else int(x.year))

    x['release_week'] = pd.to_datetime(x['release_date']).apply(lambda x:0 if pd.isnull(x.week) else int(x.week))

    x['cast_size'] = x['cast'].apply(lambda x:len(x) if len(x)>0 else 0)
    x['crew_size'] = x['crew'].apply(lambda x:len(x) if len(x)>0 else 0)
    x['number_production_companies'] = x['production_companies'].apply(lambda x:len(x) if len(x)>0 else 0)

    x['director_count'] = x['crew'].apply(get_crew_member_count_by_job, args=('Director',))
    x['writer_count'] = x['crew'].apply(get_crew_member_count_by_job, args=('Screenplay',))
    x['editor_count'] = x['crew'].apply(get_crew_member_count_by_job, args=('Editor',))

    x['sound_department_size'] = x['crew'].apply(get_department_size, args=('Sound',))
    x['costume_department_size'] = x['crew'].apply(get_department_size, args=('Costume & Make-Up',))
    x['editing_department_size'] = x['crew'].apply(get_department_size, args=('Editing',))
    x['production_department_size'] = x['crew'].apply(get_department_size, args=('Production',))
    x['art_department_size'] = x['crew'].apply(get_department_size, args=('Art',))
    x['camera_department_size'] = x['crew'].apply(get_department_size, args=('Camera',))
    x['vx_department_size'] = x['crew'].apply(get_department_size, args=('Visual Effects',))

    x['male_cast_count'] = x['cast'].apply(get_cast_number, args = ('2'))
    x['female_cast_count'] = x['cast'].apply(get_cast_number, args = ('1'))
    x['unstated_gender_cast_count'] = x['cast'].apply(get_cast_number, args = ('0'))

    x['spoken_languages'] = x['spoken_languages'].apply(convert_dict_to_1d_list)

    return x

def one_hot_encoder(df, column_to_encode, control_df, control_subset_size, control_column, output_prefix):
    control_list = set(control_df.nlargest(control_subset_size, control_column)[control_column])

    def encode_item(item):
        if isinstance(item, list):
            encoded = {output_prefix + elem.replace(" ", ""): 1 for elem in item if elem in control_list}
        else:
            encoded = {output_prefix + item.replace(" ", ""): 1 if item in control_list else 0}
        return encoded

    encoded_data = df[column_to_encode].apply(lambda x: encode_item(x) if pd.notna(x) else {})

    encoded_df = pd.DataFrame(list(encoded_data)).fillna(0).astype(int)

    df = df.drop(column_to_encode, axis=1).reset_index(drop=True)
    df = pd.concat([df, encoded_df], axis=1)

    return df

def calculate_average_revenue(df, column):
    revenue_sum = defaultdict(float)
    count = defaultdict(int)

    for index, row in df.iterrows():
        entities = [row[column]] if isinstance(row[column], str) else row[column]
        if entities is None:
            continue
        for entity in entities:
            revenue_sum[entity] += row['revenue']
            count[entity] += 1

    # Calculate average revenue
    average_revenue = {entity: revenue_sum[entity] / count[entity] for entity in revenue_sum}

    return average_revenue

def one_hot_encode_top_x_by_revenue(df, columns, top_x):
    one_hot_encoded_dfs = []  # To hold one-hot encoded DataFrames for each column before concatenating
    for column in columns:
        average_revenue = calculate_average_revenue(df, column)

        # Sort entities based on average revenue and select top X
        top_entities = sorted(average_revenue, key=average_revenue.get, reverse=True)[:top_x]

        # Prepare a dict to hold the encoded data
        encoded_data = {f'{column}_is_{entity}': [] for entity in top_entities}

        # Fill in the encoded data
        for index, row in df.iterrows():
            entities = [row[column]] if isinstance(row[column], str) else row[column]
            if entities is None:
                for entity in top_entities:
                    encoded_data[f'{column}_is_{entity}'].append(0)
                continue
            for entity in top_entities:
                encoded_data[f'{column}_is_{entity}'].append(1 if entity in entities else 0)

        # Convert the encoded data to a DataFrame
        encoded_df = pd.DataFrame(encoded_data, index=df.index)
        one_hot_encoded_dfs.append(encoded_df)

    # Concatenate all one-hot encoded DataFrames with the original DataFrame
    df = pd.concat([df] + one_hot_encoded_dfs, axis=1)

    return df

def one_hot_encode_data(x):
    columns_to_encode = ['director_name', 'production_companies', 'genres', 'spoken_languages', 'country', ]
    x_onehot = one_hot_encode_top_x_by_revenue(x, columns_to_encode, top_x=10000)
    columns_to_drop = ['genres', 'homepage', 'id', 'keywords', 'original_language',
                   'original_title', 'production_companies',
                   'production_countries', 'release_date', 'spoken_languages',
                   'status', 'title', 'director_name', 'country',
                   'cast', 'crew', 'id', 'dominant_genre', 'vote_count', 'popularity', 'vote_average']

    x_cleaned = x_onehot.drop(columns=columns_to_drop)
    x_cleaned = x_cleaned.fillna(0)
    x_cleaned = x_cleaned.reset_index()
    taglines = x_cleaned["tagline"].replace(0, "")
    overview = x_cleaned["overview"].replace(0, "")

    descriptions = taglines + " " + overview
    descriptions = descriptions.map(lambda x: x.strip() if isinstance(x, str) else x)

    Y = x_cleaned['revenue']
    X = x_cleaned.drop(columns=['revenue', 'overview', 'tagline'], axis=1)  

    return X, Y, descriptions

def preprocess_data(credits_path, movies_path):
    data = load_data(credits_path, movies_path)
    x = organize_data(data)
    X, Y, descriptions = one_hot_encode_data(x)

    return (X, Y, descriptions)


if __name__ == "__main__":
    (X, Y, descriptions) = preprocess_data(CREDITS_PATH, MOVIES_PATH)