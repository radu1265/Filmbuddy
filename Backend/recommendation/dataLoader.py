import os

import pandas as pd
from surprise import Dataset, Reader

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'MovieLens100K')

def load_users():
    df = pd.read_csv(os.path.join(DATA_PATH, 'u.user'), sep='|', header=None, names=['user_id','age','gender','occupation','zip'])
    return df

def load_dataset():
    df = pd.read_csv(os.path.join(DATA_PATH, 'u.data'), sep='\t', header=None, names=['user_id', 'item_id', 'rating', 'timestamp'])
    return df[['user_id', 'item_id', 'rating']]
    # return df

def load_genres_stats():
    df = pd.read_csv(os.path.join(DATA_PATH, 'u.genre'), sep='|', header=None, names=['genre', 'index'], encoding='latin-1').dropna()
    # print(df)
    return df


# compute genre matrix
def load_movies_gener():
    item_cols = [
        'movie_id', 'title', 'release_date', 'video_release_date', 'IMDb_URL'
    ] + [f'genre_{i}' for i in range(19)]

    # we only need columns 0,1 for id & title and 5–23 for the 19 genre flags
    df = pd.read_csv(
        os.path.join(DATA_PATH, 'u.item'),
        sep='|',
        header=None,
        encoding='latin-1',
        names=item_cols,
        usecols=[0, 1] + list(range(5, 24))
    )

    return df


def data_for_surprise():
    df = load_dataset()
    reader = Reader(rating_scale=(1, 5))
    data = Dataset.load_from_df(df, reader)
    return data