from django.shortcuts import render, redirect
from django.http import JsonResponse
import json 
import pandas as pd
from .datawork import data_preprocessing
import google.generativeai as genai
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import pickle 
load_dotenv()  

# Connecting to Mongo
Mongo_url = os.getenv('mongo')
client = MongoClient(Mongo_url)
db = client["ACE"]
convo = db["CLUSTERS"]
ADS = db["ADS"]

# data_upload
def du (request) :
    if request.method == "POST" and request.FILES.get("csv_file"):
        # print ("file uploaded")
        # Read uploaded CSV file
        csv_file = request.FILES["csv_file"]
        df = pd.read_csv(csv_file)
        plotname = data_preprocessing(df)
        
        # Return JSON response with base64 image
        return JsonResponse({"plot_filename": plotname})
    return render(request, "Bdashboard.html")



# adds recommendations and returns the result
def adds (request) :
    # print("Backend(ad) Checkpoint 1")
    records = list(convo.find({}, {'_id': 0}))
    if not records:
        return JsonResponse({"error": "No clustered data found!"})
    df = pd.DataFrame(records)

    # Loading the trained clustering model
    with open('model.pkl', 'rb') as f:
        kmeans = pickle.load(f)

    cluster_centers = kmeans.cluster_centers_


    for cluster_id in range(kmeans.n_clusters):
        cluster_df = df[df["Cluster"] == cluster_id]
        criteria = {
                    "average_age": float(round(cluster_df["Age"].mean(), 2)),
                    "popular_category": cluster_df["Category"].mode()[0] if not cluster_df["Category"].mode().empty else "Unknown",
                    "most_purchased_item": cluster_df["Item Purchased"].mode()[0] if not cluster_df["Item Purchased"].mode().empty else "Unknown",
                    "common_season": cluster_df["Season"].mode()[0] if not cluster_df["Season"].mode().empty else "Unknown",
                    "preferred_payment": cluster_df["Preferred Payment Method"].mode()[0] if not cluster_df["Preferred Payment Method"].mode().empty else "Unknown",
                    "centroid_values": cluster_centers[cluster_id].tolist()
                }
        # print(criteria)
        
        prompt = f"""
    Generate exactly 5 different marketing ads for customers based on the following cluster characteristics:

    - Average Age: {criteria['average_age']}
    - Most Purchased Item: {criteria['most_purchased_item']}
    - Popular Category: {criteria['popular_category']}
    - Preferred Shopping Season: {criteria['common_season']}
    - Preferred Payment Method: {criteria['preferred_payment']}
    - Numerical Feature Centroids: {criteria['centroid_values']}

    Each ad should be engaging and relevant to the target audience. Make sure the ads are unique.

    Return the ads as a JSON array only and nothing else:
[
    "Ad 1 :", 
    "Ad 2 :", 
    "Ad 3 :", 
    "Ad 4 :", 
    "Ad 5 :" ,
] 
    """

        # Defining the llm
        gemini_api_key = os.getenv("google_gemini_api")
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        # print('Backend(ads) Checkpoint 2 : ',response.text)

        ads = response.text.split("\n") if response.text else ["No ads generated"]
        # print(ads)
        ads = [ad.strip() for ad in ads if ad.strip()]  # Clean up empty lines
        ads = ads[:6] 
        # print(ads)

    # Save Criteria & Ads to MongoDB
        ADS.update_one(
            {"Cluster": str(cluster_id)},  # Find the cluster in MongoDB
            {"$set": {
                "criteria": criteria,  # Store criteria details
                "ads": ads             # Store generated ads
            }},
            upsert=True  # If cluster doesn't exist, create it
        )
    
    return redirect('display_ads') 
    
# display_ads
def display_ads(request):
    records = list(ADS.find({}, {'Cluster': 1, 'ads': 1}))
    if not records:
        return JsonResponse({"error": "No ads or cluster criteria found in the database!"})
    ads_per_cluster = {
        record["Cluster"]: record.get("ads", ["No ads generated"])
        for record in records
    }
    context = {'ads': ads_per_cluster}
    return render(request, 'existads.html', context)