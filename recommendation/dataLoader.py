# dataLoader.py
import os

import pandas as pd
from surprise import Dataset, Reader

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'MovieLens100K')

def load_dataset():
    df = pd.read_csv(os.path.join(DATA_PATH, 'u.data'), sep='\t', header=None, names=['user_id', 'item_id', 'rating', 'timestamp'])
    return df[['user_id', 'item_id', 'rating']]

def load_movies():
    df = pd.read_csv(os.path.join(DATA_PATH, 'u.item'), sep='|', header=None, encoding='latin-1', names=['movie id', 'movie title','release date','video release date','IMDb URL','unknown', 'Action','Adventure', 'Animation','Children', 'Comedy',  'Crime', 'Documentary','Drama', 'Fantasy',
'Film-Noir', 'Horror', 'Musical', 'Mystery', 'Romance', 'Sci-Fi',
'Thriller', 'War' , 'Western'])
    return df[['movie id', 'movie title']]

def data_loader():
    df = load_dataset()
    movies = load_movies()
    df = df.merge(movies, left_on='item_id', right_on='movie id', how='left')
    df = df.drop(columns=['movie id'])
    return df[['user_id', 'item_id', 'rating', 'movie title']]

# Needs improvement
def data_for_surprise():
    df = load_dataset()
    reader = Reader(rating_scale=(1, 5))
    data = Dataset.load_from_df(df, reader)
    return data

if __name__ == "__main__":
    # test data_loader
    df = data_loader()
    print("Data loaded successfully")
    print("Number of users:", df['user_id'].nunique())
    print("Number of items:", df['item_id'].nunique())
    print("Number of ratings:", len(df))
    print("Sample data:\n", df.head())
    # df = load_dataset()
    # print (df.head())
    # movies = load_movies()
    # print (movies.head())
