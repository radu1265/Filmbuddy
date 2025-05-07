import numpy as np
from surprise import Dataset, Reader, SVD
from surprise.model_selection import train_test_split
from surprise.accuracy import rmse
# import pandas as pd

import dataLoader as dl

def apply_svd():

    data = dl.data_for_surprise()
    print("Data loaded successfully")
    trainset, testset = train_test_split(data, test_size=0.2, random_state=42)
    model = SVD()
    model.fit(trainset)
    predictions = model.test(testset)
    rmse_value = rmse(predictions, verbose=True)


    return model, rmse_value

def get_movie_recommendation(model, user_id, item_id):
    # Predict the rating for a specific user and item
    prediction = model.predict(user_id, item_id)
    return prediction.est
    

# if __name__ == "__main__":
#     model, rmse_value = apply_svd()
