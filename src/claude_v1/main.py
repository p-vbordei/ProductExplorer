"""
product_explorer.py

Modular product analysis and improvement recommendation system.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

import pandas as pd
import openai
from google.cloud import firestore

from product_explorer import etl, analysis, modeling, reporting


# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI API client
openai.api_key = os.getenv("OPENAI_API_KEY") 

# Initialize Firestore DB client 
cred_path = Path("./productexplorerdata-firebase-adminsdk-ulb3d-465f23dff3.json")
db = firestore.Client.from_service_account_json(cred_path)


def main():
    """Main workflow orchestration"""
    
    # 1. Extract, transform and load data
    asin_list = etl.load_asins("data/external/asin_list.csv")
    reviews = etl.extract_reviews(asin_list, db)
    prepared_data = etl.prepare_reviews(reviews)
    
    # 2. Analyze and transform data
    product_summary = analysis.summarize_products(prepared_data)
    clusters = analysis.cluster_reviews(prepared_data)
    issues = analysis.extract_issues(clusters)

    # 3. Generate insights 
    problem_statement = modeling.define_problem_statement(product_summary, issues)
    solutions = modeling.generate_solutions(problem_statement, prepared_data, product_summary)
    
    # 4. Compile and export report
    report = reporting.generate_report(solutions, problem_statement, issues, product_summary)
    reporting.export_report(report, "output/report.pdf")

    
if __name__ == "__main__":
    main()