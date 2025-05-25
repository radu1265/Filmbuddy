# dataLoader.py
import os

import pandas as pd
from surprise import Dataset, Reader

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'MovieLens100K')

def load_users():
    df = pd.read_csv(os.path.join(DATA_PATH, 'u.user'), sep='|', header=None, names=['user_id','age','gender','occupation','zip'])
    return df

def load_dataset():
    df = pd.read_csv(os.path.join(DATA_PATH, 'u.data'), sep='\t', header=None, names=['user_id', 'item_id', 'rating', 'timestamp'])
    # return df[['user_id', 'item_id', 'rating']]
    return df

def load_genres_stats():
    df = pd.read_csv(os.path.join(DATA_PATH, 'u.genre'), sep='|', header=None, names=['genre', 'index'], encoding='latin-1').dropna()
    # print(df)
    return df


# compute genre matrix
def load_movies_gener():
    df = pd.read_csv(os.path.join(DATA_PATH, 'u.item'), sep='|', header=None, encoding='latin-1',  names=['movie_id','title','release_date','video_release_date','IMDb_URL'] + [f'genre_{i}' for i in range(19)])
    # folosesti asta pentru a crea matricea de genuri
    # genre_matrix = df.iloc[:, 6:].values
    # return genre_matrix
    return df


def data_for_surprise():
    df = load_dataset()
    reader = Reader(rating_scale=(1, 5))
    data = Dataset.load_from_df(df, reader)
    return data

if __name__ == "__main__":
    load_movies_gener()
    # test data_loader
    # df = data_loader()
    # print("Data loaded successfully")
    # print("Number of users:", df['user_id'].nunique())
    # print("Number of items:", df['item_id'].nunique())
    # print("Number of ratings:", len(df))
    # print("Sample data:\n", df.head())
    # df = load_dataset()
    # print (df.head())
    # movies = load_movies()
    # print (movies.head())
