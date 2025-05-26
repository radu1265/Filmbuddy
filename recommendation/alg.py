# import dataLoader as dl
from recommendation import dataLoader as dl
from surprise import SVD
from surprise.model_selection import train_test_split
from surprise.accuracy import rmse
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import numpy as np


def apply_svd_and_genre(alpha=0.7, test_size=0.2, random_state=42):
    # 1. Load and split the rating data
    data = dl.data_for_surprise()
    trainset, testset = train_test_split(data, test_size=test_size, random_state=random_state)
    print (trainset)

    # 2. Train SVD on the training set
    svd = SVD(random_state=random_state)
    svd.fit(trainset)

    # 3. Load movie metadata (genres) and prepare similarity matrix
    movies_df = dl.load_movies_gener()
    # genres are in columns starting from index 5 onward
    genre_cols = movies_df.columns[5:]
    genre_matrix = movies_df[genre_cols].values
    genre_similarity = cosine_similarity(genre_matrix)

    # 4. Build a fast lookup from movie_id to row index in movies_df
    movie_idx = {mid: idx for idx, mid in enumerate(movies_df['movie_id'].astype(int))}

    return svd, trainset, testset, movies_df, genre_similarity, movie_idx


def hybrid_recommendations(svd, trainset, movies_df, genre_sim, movie_idx,
                           user_id, top_n=5, alpha=0.7):
    """
    Generate hybrid recommendations for a user by combining SVD scores
    and content-based genre similarity.
    """
    # Convert raw user ID to inner ID
    try:
        inner_uid = trainset.to_inner_uid(str(user_id))
    except ValueError:
        inner_uid = trainset.to_inner_uid(user_id)

    # Gather indices of movies the user has already rated
    rated_inner = [iid for (iid, _) in trainset.ur[inner_uid]]
    rated_raw = [int(trainset.to_raw_iid(iid)) for iid in rated_inner]

    # Prepare list for hybrid scores
    hybrid_scores = []

    for raw_mid, row in zip(movies_df['movie_id'].astype(int), movies_df.itertuples()):
        if raw_mid in rated_raw:
            continue  # skip already rated

        # 1) SVD prediction
        svd_pred = svd.predict(user_id, raw_mid).est

        # 2) Content-based score: avg similarity to rated movies
        if rated_raw:
            sims = []
            i = movie_idx[raw_mid]
            for rmid in rated_raw:
                j = movie_idx.get(rmid)
                if j is not None:
                    sims.append(genre_sim[i, j])
            content_score = np.mean(sims) if sims else 0.0
        else:
            content_score = 0.0

        # 3) Hybrid final score
        final_score = alpha * svd_pred + (1 - alpha) * content_score
        hybrid_scores.append((raw_mid, final_score))

    # Sort and pick top_n
    hybrid_scores.sort(key=lambda x: x[1], reverse=True)
    top = hybrid_scores[:top_n]

    # Map to titles
    titles = movies_df.set_index('movie_id').loc[[mid for mid, _ in top]]['title']
    return pd.DataFrame({
        'movie_id': [mid for mid, _ in top],
        'title': titles.values,
        'hybrid_score': [score for _, score in top]
    })

def recommend_top_n_movies(user_id, n, alpha):
    """
    Recommend top N movies for a given user using hybrid SVD and genre similarity.
    """
    svd, trainset, testset, movies_df, genre_sim, movie_idx = apply_svd_and_genre(alpha=alpha)
    recs_df = hybrid_recommendations(svd, trainset, movies_df, genre_sim, movie_idx,
                                     user_id=user_id, top_n=n, alpha=alpha)
    return recs_df