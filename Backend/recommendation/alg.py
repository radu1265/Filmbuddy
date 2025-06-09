import psycopg2
import pandas as pd
import numpy as np
import os

from surprise import Dataset, Reader, SVD
from surprise.model_selection import train_test_split
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv

load_dotenv()

# ────────────────────────────────────────────────────────────────────────────────
# Database connection parameters
DB_NAME = "movielens"
DB_USER = "postgres"  
DB_PASS = os.getenv("PASSWORD")
DB_HOST = "localhost"
DB_PORT = 5432
# ────────────────────────────────────────────────────────────────────────────────

def get_db_connection():
    """
    Returns a new psycopg2 connection to the movielens database.
    """
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        host=DB_HOST,
        port=DB_PORT
    )


def apply_svd_and_genre(test_size=0.2, random_state=42):
    """
    1. Pull all ratings from PostgreSQL and build a Surprise Dataset.
    2. Split into train/test and fit an SVD model on trainset.
    3. Pull movie metadata + genre flags from PostgreSQL and compute a genre-similarity matrix.
    Returns:
      - svd: trained Surprise SVD model
      - trainset, testset: Surprise train/test sets
      - movies_df: pandas DataFrame with columns ['movie_id','title',<genre columns>]
      - genre_similarity: NumPy array (num_movies × num_movies) of genre-based cosine similarities
      - movie_idx: dict mapping raw_movie_id → index in movies_df / in genre_similarity
    """
    # ─── Step 1: Load and split the rating data from PostgreSQL ──────────────────
    conn = get_db_connection()
    # Fetch all (user_id, movie_id, rating) from ratings table
    df_ratings = pd.read_sql_query(
        "SELECT user_id AS userId, movie_id AS movieId, rating "
        "FROM ratings;",
        conn
    )
    df_ratings.rename(columns={
        "userid": "userId",
        "movieid": "movieId"
    }, inplace=True)
    # Surprise expects userId and movieId as strings (so it can internally index them)
    df_ratings["userId"] = df_ratings["userId"].astype(str)
    df_ratings["movieId"] = df_ratings["movieId"].astype(str)

    # Build a Surprise Dataset from the DataFrame
    reader = Reader(rating_scale=(1, 5))
    data = Dataset.load_from_df(df_ratings[["userId", "movieId", "rating"]], reader)

    # Split into trainset/testset
    trainset, testset = train_test_split(data, test_size=test_size, random_state=random_state)

    # Train SVD on the training set
    svd = SVD(random_state=random_state)
    svd.fit(trainset)

    # ─── Step 2: Load movie metadata + genres from PostgreSQL ────────────────────
    # 2a) Load basic movie info
    df_movies = pd.read_sql_query(
        "SELECT movie_id, title FROM movies;",
        conn
    )

    # 2b) Load all genres
    df_genres = pd.read_sql_query(
        "SELECT genre_id, name FROM genres ORDER BY genre_id;",
        conn
    )
    # We'll need a mapping: genre_id → genre_name
    genre_id_to_name = dict(zip(df_genres["genre_id"], df_genres["name"]))

    # 2c) Load movie-genre relationships
    df_mg = pd.read_sql_query(
        "SELECT movie_id, genre_id FROM movie_genres;",
        conn
    )
    conn.close()

    # 2d) Pivot df_mg into one-hot genre columns
    # Create a DataFrame where rows = movie_id, columns = genre names, values = 0 or 1
    # First, map genre_id → genre_name in df_mg
    df_mg["genre_name"] = df_mg["genre_id"].map(genre_id_to_name)

    # Use crosstab to create a one-hot encoding: index=movie_id, columns=genre_name
    genre_ohe = pd.crosstab(df_mg["movie_id"], df_mg["genre_name"])
    # Ensure that every genre in df_genres appears as a column (even if some movie has 0)
    for g in df_genres["name"]:
        if g not in genre_ohe.columns:
            genre_ohe[g] = 0
    # Re-index so that all movie_ids appear (in case some movies have no genres, though unlikely)
    genre_ohe = genre_ohe.reindex(df_movies["movie_id"], fill_value=0)

    # 2e) Build the final movies_df by joining df_movies with one-hot DataFrame
    # Reset index on genre_ohe so movie_id is a column
    genre_ohe = genre_ohe.reset_index()
    # Merge with df_movies on movie_id
    movies_df = pd.merge(df_movies, genre_ohe, how="left", on="movie_id")
    # Fill any NaNs (shouldn't really exist) with 0
    movies_df.fillna(0, inplace=True)

    # ─── Step 3: Compute genre-similarity matrix ──────────────────────────────────
    # Identify which columns in movies_df are genre columns:
    # (anything except "movie_id" and "title" are genre flags)
    genre_cols = [col for col in movies_df.columns if col not in ["movie_id", "title"]]
    # Convert those columns to a NumPy matrix (dtype=int)
    genre_matrix = movies_df[genre_cols].values.astype(int)

    # Compute cosine similarity (movies × movies)
    genre_similarity = cosine_similarity(genre_matrix)

    # Build a mapping from raw movie_id (int) → index in movies_df (0..num_movies-1)
    movie_idx = {int(mid): idx for idx, mid in enumerate(movies_df["movie_id"].values)}

    return svd, trainset, testset, movies_df, genre_similarity, movie_idx


def hybrid_recommendations(svd, trainset, movies_df, genre_similarity, movie_idx,
                           user_id, top_n=10, alpha=0.5):
    """
    Generate hybrid recommendations for a user by combining SVD and genre similarity.

    - svd: trained SVD model
    - trainset: Surprise Trainset (so we can check which movies are already rated by the user)
    - movies_df: pandas DataFrame with ['movie_id', 'title', <genre columns>]
    - genre_similarity: NumPy array (num_movies × num_movies)
    - movie_idx: dict mapping raw_movie_id → index in movies_df / genre_similarity
    - user_id: raw user ID (int or str)
    - top_n: number of recommendations to return
    - alpha: weight for SVD score vs genre score (0 ≤ alpha ≤ 1)
    """
    # Ensure user_id is a string (Surprise was trained with string IDs)
    raw_uid = str(user_id)

    # 1) Convert raw UID to Surprise's internal UID (to verify if they exist in trainset)
    try:
        inner_uid = trainset.to_inner_uid(raw_uid)
    except ValueError:
        # User has no ratings in trainset (they might be brand-new) → cannot produce SVD preds
        inner_uid = None

    # 2) Build a set of movie_ids that the user has already rated (so we skip them)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT movie_id FROM ratings WHERE user_id = %s;",
        (user_id,)
    )
    rated_by_user = {row[0] for row in cur.fetchall()}
    cur.close()
    conn.close()

    # 3) Compute SVD-predicted scores for all movies the user hasn't rated (if inner_uid is not None)
    svd_scores = {}
    if inner_uid is not None:
        for raw_mid in movies_df["movie_id"].astype(int):
            if raw_mid in rated_by_user:
                continue
            try:
                est = svd.predict(raw_uid, str(raw_mid)).est
            except:
                est = svd.predict(raw_uid, raw_mid).est
            svd_scores[raw_mid] = est

    # 4) Compute a "genre preference vector" for this user:
    #    - For each movie they have rated, weight its genre vector by the rating,
    #      then normalize by total sum of ratings.
    num_movies = movies_df.shape[0]
    num_genres = genre_similarity.shape[0]  # same as num_movies
    # Actually, genre_similarity is movies×movies. Instead, we want the genre vector
    # for each movie. We already have that as genre_matrix in apply_svd_and_genre,
    # but since we don't pass it here, we can extract from movies_df:
    genre_cols = [col for col in movies_df.columns if col not in ["movie_id", "title"]]
    # Build a dict: movie_id → genre_vector (NumPy array)
    movie_genre_map = {
        int(row["movie_id"]): row[genre_cols].values.astype(float)
        for _, row in movies_df.iterrows()
    }

    # Fetch all (movie_id, rating) for this user
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT movie_id, rating FROM ratings WHERE user_id = %s;",
        (user_id,)
    )
    user_ratings = cur.fetchall()  # list of (movie_id, rating)
    cur.close()
    conn.close()

    # Build the user's aggregated genre profile
    user_profile = np.zeros(len(genre_cols), dtype=float)
    total_weight = 0.0
    for mid, rating in user_ratings:
        if mid in movie_genre_map:
            user_profile += rating * movie_genre_map[mid]
            total_weight += rating
    if total_weight > 0:
        user_profile /= total_weight
    # If total_weight == 0, user_profile stays as zero vector

    # 5) For all unseen movies, compute hybrid score:
    #    hybrid_score = alpha * svd_score + (1 - alpha) * (user_profile ⋅ movie_genre_vector)
    hybrid_scores = {}
    for raw_mid in movies_df["movie_id"].astype(int):
        if raw_mid in rated_by_user:
            continue
        # SVD component (if available; else 0)
        cf_score = svd_scores.get(raw_mid, 0.0)
        # Content (genre) component
        genre_vec = movie_genre_map[raw_mid]
        content_score = float(np.dot(user_profile, genre_vec))
        # Combine
        hybrid_scores[raw_mid] = alpha * cf_score + (1 - alpha) * content_score

    # 6) Rank movies by hybrid score descending and take top_n
    ranked = sorted(hybrid_scores.items(), key=lambda x: x[1], reverse=True)
    top_n_raw = [mid for mid, _ in ranked[:top_n]]

    # 7) Retrieve titles for the top_n
    title_map = dict(zip(movies_df["movie_id"].astype(int), movies_df["title"]))
    titles = [title_map[mid] for mid in top_n_raw]

    # Build a DataFrame of results
    return pd.DataFrame({
        "movie_id": top_n_raw,
        "title": titles,
        "hybrid_score": [hybrid_scores[mid] for mid in top_n_raw]
    })


def recommend_top_n_movies(user_id, n, alpha):
    """
    Main entrypoint: retrain SVD + genre similarity on all available ratings,
    then produce a top-n recommendation for the given user_id.
    """
    svd, trainset, testset, movies_df, genre_sim, movie_idx = apply_svd_and_genre()
    recs_df = hybrid_recommendations(
        svd,
        trainset,
        movies_df,
        genre_sim,
        movie_idx,
        user_id=user_id,
        top_n=n,
        alpha=alpha
    )
    return recs_df



# if __name__ == "__main__":
#     df_recs = recommend_top_n_movies(user_id=12, n=5, alpha=0.9)
#     print(df_recs)