import pandas as pd
from surprise import Dataset, Reader
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'MovieLens100K')

# Load the MovieLens 100K dataset

def load_dataset():

    df = pd.read_csv(os.path.join(DATA_PATH, 'u.data'), sep='\t', header=None, names=['user_id', 'item_id', 'rating', 'timestamp'])
    return df[['user_id', 'item_id', 'rating']]

def load_movies():
    df = pd.read_csv(os.path.join(DATA_PATH, 'u.item'), sep='|', header=None, encoding='latin-1', names=['item_id', 'title'])
    return df[['item_id', 'title']]


def data_loader():
    df = load_dataset()
    movies = load_movies()
    df = pd.merge(df, movies, on='item_id')
    return df[['user_id', 'item_id', 'rating', 'title']]

# preaper data for Surprise

def data_for_surprise():
    reader = Reader(rating_scale=(1, 5))
    data = Dataset.load_from_df(load_dataset(), reader)
    return data