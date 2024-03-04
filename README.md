ProductExplorer
==============================

Overview
ProductExplorer is a cutting-edge platform designed to revolutionize the product management landscape. Leveraging advanced AI algorithms and Knowledge Graph technology, this tool offers product teams an unparalleled ability to swiftly access comprehensive reviews insights and actionable solutions, optimizing product development and strategy.

Technical Description
At its core, ProductExplorer aims to meticulously analyze customer feedback, providing in-depth product insights and recommending enhancements based on sophisticated review analysis. The platform's architecture is engineered around several key components:

Data Acquisition: Utilizes an API to fetch detailed product and reviews data from Amazon, ensuring a rich dataset for analysis.
Review Processing: Employs advanced NLP techniques to process and cluster product review data, extracting significant attributes and sentiments.
Insight Generation: Analyzes clustered data to quantify attributes, identifying key areas for product improvement and innovation.
Core Technologies
Semantic Similarity Models
Utilizes state-of-the-art semantic similarity models to assess and cluster review content. SBERT and Hugging Face models are pivotal in understanding nuanced customer feedback.
Topic Clustering
Implements sophisticated clustering algorithms as outlined in SBERT documentation, enabling the identification of core topics within customer reviews for targeted insights. SBERT Clustering serves as a foundation for this process.
Data Architecture: FIRESTORE Integration
The platform's data management is structured within Firestore, facilitating efficient data storage and retrieval. This hierarchical schema encompasses:

User Management: Stores user profiles, subscriptions, and associated metadata.
Payment Processing: Records payment transactions, linking them to user subscriptions.
Investigative Analysis: Organizes product investigations, including status tracking and outcome documentation.
Product Insights: Centralizes product data alongside aggregated review insights for easy access and analysis.
Attribute Clustering: Details the clustering of product attributes based on customer feedback, aiding in the quantification of insights.
Deployment and Usage
Local Setup:

Initialize the platform within the ProductExplorer project directory: python -m main
Access the local UI at http://192.168.31.31:8080/ui/


##########


FIRESTORE Data Structure:

        Firestore Root
        |
        |-- users (Collection)
        |   |
        |   |-- userId (Document)
        |       |
        |       |-- subscriptions (Subcollection)
        |       |   |
        |       |   |-- subscriptionId (Document)
        |       |
        |       |-- ... (Other fields in the user document)
        |
        |-- payments (Collection)
        |   |
        |   |-- paymentId (Document)
        |
        |-- investigations (Collection)
        |   |
        |   |-- investigationId (Document)
        |
        |-- products (Collection)
        |   |
        |   |-- asin (Document)
        |       |
        |       |-- details (Field)
        |       |
        |       |-- reviews (Subcollection)
        |           |
        |           |-- reviewId (Document)
        |
        |-- productInsights (Collection)
        |   |
        |   |-- investigationId (Document)
        |
        |-- clusters (Collection)
        |   |
        |   |-- investigationId (Document)
        |       |
        |       |-- attributeClustersWithPercentage (Field)
        |       |
        |       |-- attributeClustersWithPercentageByAsin (Field)
        |
        |-- reviewsInsights (Collection)
        |   |
        |   |-- investigationId (Document)
        |       |
        |       |-- attributeWithPercentage (Subcollection)
        |           |
        |           |-- attribute (Document)
        |               |
        |               |-- clusters (Field)
        


FIRESTORE Data Structure:

    Users (collection)
        Documents (e.g., userId1, userId2, ...)
            Fields: 
                - id: Auto-generated ID (string)
                - name: User's name (string)
                - email: User's email (string)
                - currentPackage: Current subscribed package (string, optional)
                - remainingInvestigations: Remaining investigations count (number, optional)
            
        Sub-collection: Subscriptions
            Documents (e.g., subscriptionId1, subscriptionId2, ...)
                Fields:
                    - id: Auto-generated ID (string)
                    - userId: Reference to the user's ID (string)
                    - package: Subscribed package (string)
                    - startDate: Subscription start date (timestamp)
                    - paymentStatus: Payment status (string, optional)
                    - paymentIntent: Payment intent ID (string, optional)

    Investigations (collection)
        Documents (e.g., investigationId1, investigationId2, ...)
            Fields: 
                - asins: List of ASINs (array of strings)
                - userId: User's ID (string)
                - status: Status of the investigation (string)
                - receivedTimestamp: Timestamp when the investigation was received (timestamp)
                - startedTimestamp: Timestamp when the investigation was started (timestamp, optional)
                - finishedTimestamp: Timestamp when the investigation was finished (timestamp, optional)
                - reviewedTimestamps: List of timestamps when the investigation was reviewed (array of timestamps)
    
    Payments (collection)
        Documents (e.g., paymentId1, paymentId2, ...)
            Fields: 
                - id: Auto-generated ID (string)
                - subscriptionId: Subscription ID (string)
                - date: Date of the payment (timestamp)
                - status: Status of the payment (string)
                - userId: User's ID (string)
                - amount: Amount paid (number)
                - paymentIntent: Payment intent ID (string)
    
    
    Products (collection)
        Documents (e.g., ASIN1234, ASIN5678, ...)
            Fields: 
                - details: Product details (object or map)
            
            Sub-collection: Reviews
                Documents (e.g., reviewId1, reviewId2, ...)
                    Fields:
                        - ... (Fields specific to each review, not detailed in the provided code)
    
    ProductInsights (collection)
        Documents (e.g., investigationId1, investigationId2, ...)
            Fields: 
                - shortProductData: Summarized product data (object or map)
                - otherProductData: Additional product data not included in the summary (object or map)
    
    Clusters (collection)
        Documents (e.g., investigationId1, investigationId2, ...)
            Fields: 
                - attributeClustersWithPercentage: Clusters with percentage information (array of objects)
                - attributeClustersWithPercentageByAsin: Clusters with percentage information by ASIN (array of objects)
    
    ReviewsInsights (collection)
        Documents (e.g., investigationId1, investigationId2, ...)
            Sub-collection: AttributeWithPercentage
                Documents (e.g., attribute1, attribute2, ...)
                    Fields:
                        - clusters: Data points list for the attribute (array of objects)



users.py - Implements user management logic including creating users, fetching user data, subscribing users, logging payments, adding/tracking investigations, and checking investigation limits. Relies on Firestore for persistence.



Module: data_processing_utils.py

Purpose: This module provides utility functions for processing and cleaning review data.

Functions:
num_tokens_from_string: Calculates the number of tokens in a given text string using a specified encoding.
clean_review: Cleans a review by removing non-alphanumeric characters.
initial_review_clean_data: Processes a DataFrame of reviews by cleaning the review text, calculating token counts, and truncating reviews that exceed a specified token limit.
initial_review_clean_data_list: Similar to the above, but processes a list of review dictionaries instead of a DataFrame.




Module: firebase_utils.py

Purpose: This module provides utility functions for interacting with Firestore, a NoSQL cloud database.

Setup:
Initializes a connection to Firestore using a provided credentials file.
Functions:
update_investigation_status: Updates the status of a specified investigation in Firestore.
get_asins_from_investigation: Retrieves ASINs (Amazon Standard Identification Numbers) associated with a specified investigation.
get_reviews_from_asin: Fetches product reviews for a given ASIN from Firestore.
get_investigation_and_reviews: Retrieves both the investigation and associated reviews for a given investigation ID.
write_reviews: Writes a list of cleaned reviews to Firestore, grouped by ASIN.



Module: openai_api.py

Purpose: This module provides utility functions for interacting with the OpenAI API, specifically for generating completions and embeddings.

Setup:
Defines headers for API requests and initializes asynchronous capabilities with nest_asyncio.
Functions:
get_completion: Fetches a completion from the OpenAI API for a given input.
get_completion_list: Fetches completions for a list of inputs.
get_embedding: Retrieves an embedding for a given text string from the OpenAI API.
process_dataframe_async_embedding: Processes a DataFrame to fetch embeddings for each row asynchronously.


Review Processing Module

This system processes product reviews, clusters them based on similarity, and quantifies the observations.

Initialization:

The ReviewProcessor class initializes with an investigation ID, OpenAI API key, and Firestore credentials.
Firestore is set up to interact with the database.
Review Retrieval and Cleaning:

Reviews related to a specific investigation are fetched from Firestore.
Each review is flattened and cleaned to extract relevant information.
Review Processing with OpenAI's GPT:

Each review is processed using OpenAI's GPT model to extract insights.
The insights are then merged with the original reviews.
Clustering:

The reviews are transformed into a DataFrame format.
Unnecessary columns are dropped, and missing values are handled.
The DataFrame is then pivoted and filtered.
Each review is embedded using a function from openai_utils.
Agglomerative clustering is applied to group similar reviews.
Cluster Labeling:

Each cluster of reviews is labeled using OpenAI's GPT model.
The labels are then merged with the clusters.
Saving Results to Firestore:

The processed reviews and their associated clusters are saved to Firestore.
Quantifying Observations:

Observations are quantified at both the investigation and ASIN levels.
The quantified observations are saved to Firestore.
Utility Functions:

The firebase_utils.py file contains utility functions to interact with Firestore.
Functions include updating investigation status, retrieving ASINs and reviews, writing reviews to Firestore, and saving clusters.

gcloud app logs tail -s default 


#################
###### RUN #####
in  ProductExplorer (project folder)
python -m main
http://192.168.31.31:8080/ui/

# Running on Docker
In the Working Dir
docker build -t flask-gae-app .

docker run -p 8080:8080 \
-e OPENAI_API_KEY="xxx" \
-e FIREBASE_KEY=/app/firebase-key.json \
-v /Users/vladbordei/Documents/Development/ProductExplorer/firebase-key.json:/app/firebase-key.json \
flask-gae-app

http://localhost:8080/ui/


Gunicorn Test
gunicorn -b :8080 '__init__:app'


# GAE Run
In the Working Dir
gcloud auth login
gcloud config set project productexplorerdata
gcloud app deploy

https://productexplorerdata.uc.r.appspot.com/ui


# Google Pub/Sub

gcloud pubsub topics create asin-data-acquisition --project=productexplorerdata
gcloud pubsub subscriptions create asin-data-subscription  --topic=asin-data-acquisition --project=productexplorerdata
project_id = "productexplorerdata"
topic_id = "asin-data-acquisition"
subscription_id = "asin-data-subscription"


Additional instals. To check if needed to run online
pip install --upgrade google-api-core
pip install firestore


Set the environment variables
export FLASK_APP=app.py 
export FLASK_ENV=development
export PYTHONPATH=.
export FLASK_DEBUG=1
export FLASK_RUN_PORT=8080

or 'production' based on your use case


Run your flask app
export GOOGLE_APPLICATION_CREDENTIALS="..."
flask run
http://localhost:8080/ui/

Demo / deployed
[https://productexplorerdata.uc.r.appspot.com]

You can stream logs from the command line by running:
  $ gcloud app logs tail -s default

To view your application in the web browser run:
  $ gcloud app browse

When debugging
!gcloud auth application-default login
!export GOOGLE_APPLICATION_CREDENTIALS="...."
