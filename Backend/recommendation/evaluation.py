# evaluation.py
from surprise import SVD
from surprise.accuracy import rmse, mae
from surprise.model_selection import cross_validate
from collections import defaultdict
import numpy as np
from surprise import Prediction

def evaluate_rating_prediction(algo, testset):
    """
    Compute RMSE and MAE on a Surprise testset.
    Returns the list of predictions.
    """
    preds = algo.test(testset)
    print("Rating prediction accuracy:")
    print(f"  RMSE = {rmse(preds):.4f}")
    print(f"   MAE = {mae(preds):.4f}")
    return preds

def evaluate_hybrid_prediction(svd, trainset, movies_df, genre_sim, movie_idx,
                               testset, alpha=0.7):
    """
    Compute RMSE/MAE for the hybrid model by
    combining SVD.est + content_score for each (user, item) in testset.
    """
    hybrid_preds = []

    # build a map of rated movies per user (inner IDs)
    user_rated_inner = {uid: [iid for (iid, _) in trainset.ur[uid]]
                        for uid in trainset.all_users()}

    for uid_raw, iid_raw, true_r in testset:
        # convert raw -> inner
        try:
            inner_uid = trainset.to_inner_uid(str(uid_raw))
        except ValueError:
            inner_uid = trainset.to_inner_uid(uid_raw)

        # content-based component
        rated_raw = [int(trainset.to_raw_iid(i)) for i in user_rated_inner[inner_uid]]
        if rated_raw:
            i = movie_idx[int(iid_raw)]
            sims = []
            for rmid in rated_raw:
                j = movie_idx.get(rmid)
                if j is not None:
                    sims.append(genre_sim[i, j])
            content_score = np.mean(sims) if sims else 0.0
            content_score = 1 + 4 * content_score  # scale to [1, 5]
        else:
            content_score = 0.0

        # SVD component
        svd_est = svd.predict(uid_raw, iid_raw).est

        # hybrid
        final_est = alpha * svd_est + (1 - alpha) * content_score

        hybrid_preds.append(Prediction(uid_raw, iid_raw, true_r, final_est, None))

    print("Hybrid model accuracy:")
    print(f"  RMSE = {rmse(hybrid_preds):.4f}")
    print(f"   MAE = {mae(hybrid_preds):.4f}")
    return hybrid_preds

# def cross_validate_svd(data, n_folds=5, random_state=42):
#     """
#     Run k-fold CV on an SVD model, reporting RMSE and MAE.
#     """
#     algo = SVD(random_state=random_state)
#     cv_results = cross_validate(algo, data,
#                                 measures=['RMSE', 'MAE'],
#                                 cv=n_folds,
#                                 verbose=True)
#     return cv_results

def get_top_n(predictions, n=10):
    """
    Return the top‐n recommended item IDs for each user from a set of predictions.
    """
    top_n = defaultdict(list)
    for uid, iid, true_r, est, _ in predictions:
        top_n[uid].append((iid, est))
    # keep only the n highest‐estimates per user
    for uid, user_ratings in top_n.items():
        user_ratings.sort(key=lambda x: x[1], reverse=True)
        top_n[uid] = [iid for (iid, _) in user_ratings[:n]]
    return top_n

def precision_recall_at_k(predictions, k=10, threshold=4.0):
    """
    Calculate Precision@k and Recall@k for each user, then return
    two dicts mapping user → precision and user → recall.

    - threshold: rating threshold to count as “relevant.”
    """
    # gather est, true for each user
    user_est_true = defaultdict(list)
    for uid, iid, true_r, est, _ in predictions:
        user_est_true[uid].append((est, true_r))

    precisions = {}
    recalls = {}
    for uid, user_ratings in user_est_true.items():
        # sort by estimated rating descending
        user_ratings.sort(key=lambda x: x[0], reverse=True)

        # take top-K recommendations
        top_k = user_ratings[:k]

        # count how many in the full set are relevant
        n_rel = sum(true_r >= threshold for (_, true_r) in user_ratings)
        # count how many of the top-K are relevant
        n_rel_and_rec = sum(true_r >= threshold for (_, true_r) in top_k)

        # precision is relevant@K out of K
        precisions[uid] = n_rel_and_rec / k
        # recall is relevant@K out of all relevant
        recalls[uid]    = n_rel_and_rec / n_rel if n_rel else 0

    return precisions, recalls

def overall_precision_recall(precisions, recalls):
    """
    Compute the macro‐averaged Precision@k and Recall@k.
    """
    avg_prec = np.mean(list(precisions.values()))
    avg_rec  = np.mean(list(recalls.values()))
    print(f"Top-K ranking metrics:")
    print(f"  Precision@K = {avg_prec:.4f}")
    print(f"     Recall@K = {avg_rec:.4f}")
    return avg_prec, avg_rec


if __name__ == "__main__":
    from dataLoader import data_for_surprise, load_movies_gener
    from alg import apply_svd_and_genre

    # 1) Load & train
    svd, trainset, testset, movies_df, genre_sim, movie_idx = apply_svd_and_genre()

    # 2) Rating‐prediction evaluation
    print("Ranking evaluation for hybrid:")
    preds = evaluate_hybrid_prediction(svd, trainset, movies_df,
                                    genre_sim, movie_idx,
                                    testset, alpha=0.8)

    # 3) Cross-validation (optional)
    # data = data_for_surprise()
    # cv_results = cross_validate_svd(data, n_folds=5)

    # 4) Top-N ranking evaluation

    top_n = get_top_n(preds, n=5)
    precisions, recalls = precision_recall_at_k(preds, k=5, threshold=4.0)
    overall_precision_recall(precisions, recalls)

    # # 5) Same evaluation for SVD only
    # print("Ranking evaluation for SVD only:")
    # preds = evaluate_rating_prediction(svd, testset)


    # # 6) Top-N ranking evaluation for SVD only
    # top_n_svd = get_top_n(preds, n=10)

    # precisions_svd, recalls_svd = precision_recall_at_k(preds, k=10, threshold=4.0)
    # overall_precision_recall(precisions_svd, recalls_svd)
    # print("Evaluation completed.")