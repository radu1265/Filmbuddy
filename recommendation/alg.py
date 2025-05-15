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


# def recommend_top_n_movies(model, user_id, n=5):
#     all_movies = dl.load_movies()
#     ratings = dl.load_dataset()

#     # Get the list of movies the user has already rated
#     rated_movie_ids = ratings[ratings['user_id'] == user_id]['movie id'].unique()

#     # Get the list of movies the user has NOT rated
#     unrated_movies = all_movies[~all_movies['movie id'].isin(rated_movie_ids)]

#     # Predict ratings for all unrated movies
#     predictions = [
#         (movie_id, model.predict(user_id, movie_id).est)
#         for movie_id in unrated_movies['movie id']
#     ]

#     # Sort predictions by estimated rating
#     top_n = sorted(predictions, key=lambda x: x[1], reverse=True)[:n]

#     # Convert to DataFrame for better readability
#     top_n_df = pd.DataFrame(top_n, columns=['movie id', 'predicted_rating'])
#     top_n_df = top_n_df.merge(all_movies, on ='movie id', how='left')

#     return top_n_df[['title', 'predicted_rating']]

def apply_svd():

    # Load the dataset
    data = dl.data_for_surprise()
    train, test = train_test_split(data, test_size=0.2, random_state=42)
    model = SVD(random_state=42)
    model.fit(train)
    predictions = model.test(test)
    rmse_value = rmse(predictions, verbose=True)
    return model, rmse_value


if __name__ == "__main__":
    # Test the functions
    data = analize_data()
    model, rmse_value = apply_svd()
    user_id = 196  # Example user ID
    # print a prediction for a specific user
    movies = dl.load_movies()
    top_3_movies = [] # list of tuples (movie_id, predicted_rating)
    for movie_id in movies['movie id']:
        prediction = model.predict(user_id, movie_id)
        # check if the prediction is better than the current 3 predictions
        if len(top_3_movies) < 3:
            top_3_movies.append((movie_id, prediction.est))
        else:
            min_rating = min(top_3_movies, key=lambda x: x[1])[1]
            if prediction.est > min_rating:
                top_3_movies.remove(min(top_3_movies, key=lambda x: x[1]))
                top_3_movies.append((movie_id, prediction.est))
    # print the top 3 movies
    top_3_movies_df = pd.DataFrame(top_3_movies, columns=['movie id', 'predicted_rating'])
    top_3_movies_df = top_3_movies_df.merge(movies, on ='movie id', how='left')
    top_3_movies_df = top_3_movies_df.sort_values(by='predicted_rating', ascending=False)
    print("Top 3 recommended movies for user {}: \n{}".format(user_id, top_3_movies_df[['movie title', 'predicted_rating']]))
    # top_n_movies = recommend_top_n_movies(model, user_id, n=5)
    # print("Top N recommended movies for user {}: \n{}".format(user_id, top_n_movies))