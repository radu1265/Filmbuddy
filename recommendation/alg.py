from surprise import SVD
from surprise.model_selection import train_test_split
from surprise.accuracy import rmse
from surprise.model_selection import cross_validate
import pandas as pd

# from recommendation import dataLoader as dl
import dataLoader as dl

def analize_data():
    data = dl.data_loader()
    print("Data loaded successfully")
    print("Number of users:", data['user_id'].nunique())
    print("Number of items:", data['item_id'].nunique())
    print("Number of ratings:", len(data))
    print("Sample data:\n", data.head())

    return data

def apply_svd():


    data = dl.data_for_surprise()
    print("Data loaded successfully")
    trainset, testset = train_test_split(data, test_size=0.2, random_state=42)
    model = SVD()
    model.fit(trainset)
    predictions = model.test(testset)
    rmse_value = rmse(predictions, verbose=True)
    print(cross_validate(model, data, measures=['RMSE'], cv=5, verbose=True))


    return model, rmse_value

def recommend_top_n_movies(model, user_id, n=5):
    all_movies = dl.load_movies()
    ratings = dl.load_dataset()

    # Get the list of movies the user has already rated
    rated_movie_ids = ratings[ratings['user_id'] == user_id]['item_id'].unique()

    # Get the list of movies the user has NOT rated
    unrated_movies = all_movies[~all_movies['item_id'].isin(rated_movie_ids)]

    # Predict ratings for all unrated movies
    predictions = [
        (movie_id, model.predict(user_id, movie_id).est)
        for movie_id in unrated_movies['item_id']
    ]

    # Sort predictions by estimated rating
    top_n = sorted(predictions, key=lambda x: x[1], reverse=True)[:n]

    # Convert to DataFrame for better readability
    top_n_df = pd.DataFrame(top_n, columns=['item_id', 'predicted_rating'])
    top_n_df = top_n_df.merge(all_movies, on='item_id')

    return top_n_df[['title', 'predicted_rating']]



if __name__ == "__main__":
    analize_data()