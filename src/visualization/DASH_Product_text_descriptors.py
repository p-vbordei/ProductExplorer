# %%
import dash
from dash import dcc
import dash_bootstrap_components as dbc
from dash import html

import pandas as pd


import json
# %%
import json
with open('/Users/vladbordei/Documents/Development/oaie2/summarised_product_information.json') as file:
    json_string = file.read()
    data = json.loads(json_string)


# %%
app = dash.Dash(__name__)

app.layout = html.Div(
    children=[
        html.H1("Product Information Dashboard"),
        html.H2("Product Summary"),
        html.P(data["product_summary_dict"]["Product Summary"]),
        
        html.H2("What is in the box"),
        html.P(data["what_is_in_the_box_dict"]["What is in the box"]),
        
        html.H2("Technical Facts"),
        html.Ul([html.Li(fact) for fact in data["technical_facts_dict"]["Technical Facts"]]),

        html.H2("Features"),
        html.Ul([html.Li(f"{key}: {value}") for key, value in data["features_dict"]["Features"].items()]),

        html.H2("Outliers"),
        html.Ul([html.Li(f"ASIN: {outlier['ASIN']}, Feature: {outlier['Feature']}") for outlier in data["features_dict"]["Outliers"]]),

        html.H2("Outliers Explanation"),
        html.P(data["features_dict"]["OutliersExplanation"]["HelpsChildrenLearnAndWriteTheAlphabetCorrectly"]),


        html.Div(id='features_output'),
        html.H2("How the product is used"),
        html.P(data["how_product_use_dict"]["How the product is used"]),
        
        html.Div(id='how_product_use_dict'),
        html.H2("Where the product is used"),
        html.P(data["where_product_use_dict"]["Where the product is used"]),

        html.H2("User Description"),
        html.P(data["user_description_dict"]["User Description"]),
    ]
)

@app.callback(
    dash.dependencies.Output('features_output', 'children'),
    [dash.dependencies.Input('features_dropdown', 'value')]
)
def display_features(selected_features):
    if selected_features:
        return html.Ul([html.Li(feature) for feature in selected_features])
    else:
        return html.P("No features selected.")

if __name__ == '__main__':
    app.run_server(debug=True)

#  