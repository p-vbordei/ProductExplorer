import dash
import plotly
import openai
import os
from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State

# Set up your API key for OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Define the function to generate responses from the chatbot
def generate_response(prompt):
    response = openai.Completion.create(
        engine=="gpt-3.5-turbo",
        prompt=f"{prompt}\n",
        max_tokens=50,
        n=1,
        stop=None,
        temperature=0.5,
    )

    return response.choices[0].text.strip()

# Assuming the result DataFrame is already created
filepath = '/Users/vladbordei/Documents/Development/oaie2/resulting_key_data_data_df.csv'
result = pd.read_csv(filepath)

reviews_db_filepath = '/Users/vladbordei/Documents/Development/oaie2/reviews_db.csv'
reviews_db = pd.read_csv(reviews_db_filepath)

database = {
    "ASIN": result["asin.original"].unique(),
    "data_label": result["data_label"].unique(),
    "selection": result
}

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

heatmap_data_positive = result.pivot_table(index='data_label', columns='asin.original', values='weighted_positive_sentiment')

heatmap = go.Heatmap(
    z=heatmap_data_positive.values,
        x=heatmap_data_positive.columns,
    y=heatmap_data_positive.index,
    colorscale='YlGnBu',
    showscale=True
)

layout = go.Layout(
    title='Heatmap of Weighted Positive Sentiment by ASIN and Main Characteristic',
    xaxis=dict(title='ASIN'),
    yaxis=dict(title='Main Characteristic'),
    autosize=True,
    hovermode='closest'
)

fig = go.Figure(data=[heatmap], layout=layout)

app.layout = html.Div([
    dcc.Graph(id='heatmap', figure=fig, style={'height': '80vh'}),
    html.Div(id='database-selection', children=[]),
    html.Div(id='heatmap-click', style={'display': 'none'}),
    dbc.Row(
        [
            dbc.Col(
                [
                    html.H2("ChatGPT Chatbot"),
                    dcc.Textarea(id="user-input", placeholder="Type your message..."),
                    html.Button("Send", id="send-button"),
                    html.Div(id="chat-output"),
                ],
                md=12,
            )
        ]
    )
])

@app.callback(
    Output('heatmap-click', 'children'),
    [Input('heatmap', 'clickData')]
)
def update_heatmap_click(clickData):
    if clickData:
        asin = clickData['points'][0]['x']
        main_char = clickData['points'][0]['y']
        return f"{asin} - {main_char}"
    return None

@app.callback(
    Output('database-selection', 'children'),
    [Input('heatmap-click', 'children')]
)
def update_database_selection(click_info):
    if click_info:
        asin, main_char = click_info.split(" - ")

        selection = result.loc[
            (result['asin.original'] == asin) &
            (result['data_label'] == main_char)
        ]

        if not selection.empty:
            ids = []
            if isinstance(selection['id'].tolist()[0], (int, float)):
                ids = selection['id'].tolist()
            else:
                for sublist in selection['id'].tolist():
                    ids.extend([int(i) for i in sublist.strip('[]').split(', ') if i.isdigit()])

            result_df = reviews_db[reviews_db['id'].isin(ids)]

            return dbc.Table.from_dataframe(result_df, striped=True, bordered=True, hover=True)

    return []

@app.callback(
    Output("chat-output", "children"),
    [Input("send-button", "n_clicks")],
    [State("user-input", "value")],
)
def update_chat_output(n_clicks, user_input):
    if n_clicks is not None:
        chatbot_response = generate_response(user_input)

        return html.Div(
            [
                html.Div(f"User: {user_input}", className="user-message"),
                html.Div(f"Chatbot: {chatbot_response}", className="chatbot-message"),
            ]
        )
    return ""

if __name__ == '__main__':
    app.run_server(debug=True)

