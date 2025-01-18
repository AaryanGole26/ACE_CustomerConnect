import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import pickle
from pymongo import MongoClient
import os
import base64
from dotenv import load_dotenv
load_dotenv()

# Connecting to Mongo
Mongo_url = os.getenv('mongo')
client = MongoClient(Mongo_url)
db = client["ACE"]
convo = db["CLUSTERS"]


def data_preprocessing (df):
    # feature selection
    features = ['Age','Gender','Item Purchased','Category','Purchase Amount (USD)','Size','Season','Review Rating','Discount Applied','Promo Code Used','Previous Purchases','Preferred Payment Method']
    df = df[features]

    # Encoding the Categorical Variables
    encode_col =  ['Gender', 'Item Purchased', 'Category', 'Size', 'Season', 'Discount Applied', 'Promo Code Used', 'Preferred Payment Method']
    df_encoded = pd.get_dummies(df, columns=encode_col, drop_first=False)
    df1 = df
    df = df_encoded
    df = df.drop(['Gender_Female', 'Discount Applied_No', 'Promo Code Used_No'], axis=1)

    # Scaling the attributes
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df)
    optimal_k = 4
    kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
    df["Cluster"] = kmeans.fit_predict(X_scaled)
    clusters = kmeans.fit_predict(X_scaled)
    df1["Cluster"] = clusters

    # Storing Clustered data in MongoDB
    records = df1.to_dict(orient='records')
    convo.insert_many(records)


    # saving the model
    # with open('model.pkl', 'wb') as f:
    #     pickle.dump(kmeans,f)

    # Plotting the Data Obtained
    plt.figure(figsize=(8, 6))
    sns.scatterplot(x=df1["Category"], y=df1["Item Purchased"], hue=df["Cluster"], palette="viridis", size='Season', data=df1)
    plt.title("Customer Clusters")
    
    # Save plot to a buffer
    plot_filename = 'cluster_plot.png' 
    plot_path = os.path.join('static', 'images', plot_filename) 
    plt.savefig(plot_path)
    plt.close()

    return plot_filename 

