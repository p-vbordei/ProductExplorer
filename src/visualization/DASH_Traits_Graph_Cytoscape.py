#%%
import pandas as pd


import dash
import dash_cytoscape as cyto
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc

# Load extra layouts and stylesheets
cyto.load_extra_layouts()

cyto_stylesheet =[
    {
        'selector':  'node[type = "Fact"]',
        'style': {
            'label': 'data(label)',
            'text-wrap': 'wrap',
            'text-max-width': '200px',
            'text-overflow-wrap': 'ellipsis',
            'background-color': '#f3969a',
            'border-width': '0px',
            'border-color': '#000',
            'shape': 'rectangle',
            'width': 'label',
            'height': 'label',
            'padding': '40px',
            'text-halign': 'center',
            'text-valign': 'center',
            'font-size': 'data(fontSize)',
            'font-family': 'Arial, sans-serif',
            'color': 'white'  # Text color
        }
    },
        {
        'selector':  'node[type = "Issue"]',
        'style': {
            'label': 'data(label)',
            'text-wrap': 'wrap',
            'text-max-width': '200px',
            'text-overflow-wrap': 'ellipsis',
            'background-color': '#ffce67',
            'border-width': '0px',
            'border-color': '#000',
            'shape': 'octagon',
            'width': 'label',
            'height': 'label',
            'padding': '40px',
            'text-halign': 'center',
            'text-valign': 'center',
            'font-size': 'data(fontSize)',
            'font-family': 'Arial, sans-serif',
            'color': 'white'  # Text color
        }
    },
        {
        'selector':  'node[type = "Improvement"]',
        'style': {
            'label': 'data(label)',
            'text-wrap': 'wrap',
            'text-max-width': '200px',
            'text-overflow-wrap': 'ellipsis',
            'background-color': '#6cc3d5',
            'border-width': '0px',
            'border-color': '#000',
            'shape': 'circle',
            'width': 'label',
            'height': 'label',
            'padding': '40px',
            'text-halign': 'center',
            'text-valign': 'center',
            'font-size': 'data(fontSize)',
            'font-family': 'Arial, sans-serif',
            'color': 'white'  # Text color
            

        }
    },
        {
        'selector':  'node[type = "Product"]',
        'style': {
            'label': 'data(label)',
            'text-wrap': 'wrap',
            'text-max-width': '300px',
            'text-overflow-wrap': 'ellipsis',
            'background-color': '#FFF',
            'border-width': '0px',
            'border-color': '#000',
            'background-opacity': 0,
            'shape': 'rectangle',
            'width': '300px',
            'height': '300px',
            'padding': '10px',
            'text-halign': 'center',
            'text-valign': 'bottom', 
            'text-margin-y': '5px',  
            'background-image': 'data(faveIcon)',
            'background-fit': 'contain', 
            'font-size': '20px',
            'font-family': 'Arial, sans-serif',
            'color': '#484e53'  # Text color
        }
    },
            {
        'selector':  'node[type = "ProblemChild"]',
        'style': {
            'label': 'data(label)',
            'text-wrap': 'wrap',
            'text-max-width': '200px',
            'text-overflow-wrap': 'ellipsis',
            'background-color': '#484e53',
            'border-width': '0px',
            'border-color': '#000',
            'shape': 'rectangle',
            'width': 'label',
            'height': 'label',
            'padding': '10px',
            'text-halign': 'center',
            'text-valign': 'center',
            'font-size': '30px',
            'font-family': 'Arial, sans-serif',
            'color': 'white'  # Text color
        }
    },
                {
        'selector':  'node[type = "Solution"]',
        'style': {
            'label': 'data(label)',
            'text-wrap': 'wrap',
            'text-max-width': '200px',
            'text-overflow-wrap': 'ellipsis',
            'background-color': '#86c8b5',
            'border-width': '0px',
            'border-color': '#000',
            'shape': 'roundrectangle',
            'width': 'label',
            'height': 'label',
            'padding': '10px',
            'text-halign': 'center',
            'text-valign': 'center',
            'font-size': '30px',
            'font-family': 'Arial, sans-serif',
            'color': 'white'  # Text color
        }
    },
    {
        'selector': 'edge',
        'style': {
            'curve-style': 'unbundled-bezier',
            'control-point-distances': 100,
            'control-point-weights': 0.7,
            'target-arrow-shape': 'triangle',
            'line-color': 'rgba(0, 0, 0, 0.5)',  # Black color with 50% transparency
            'target-arrow-color': 'rgba(0, 0, 0, 0.5)',  # Black color with 50% transparency
            'width': 'data(width)',

        }
    },
    {
        'selector': ':parent',
        'style': {
            'background-opacity': 0.333,
            'background-color': '#999',
            'padding': '10px',
            'border-width': '1px',
            'border-color': '#333'
        }
    },
    {
        'selector': '.collapsed',
        'style': {
            'background-image': 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/71/Circle_arrow_left_font_awesome.svg/512px-Circle_arrow_left_font_awesome.svg.png',
            'background-fit': 'contain',
            'background-color': '#fff',
            'background-opacity': 0.85,
            'shape': 'rectangle',
            'width': '20px',
            'height': '20px'
        }
    },
    {
        'selector': '.expanded',
        'style': {
            'background-image': 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/02/Circle_arrow_right_font_awesome.svg/512px-Circle_arrow_right_font_awesome.svg.png',
            'background-fit': 'contain',
            'background-color': '#fff',
            'background-opacity': 0.85,
            'shape': 'rectangle',
            'width': '20px',
            'height': '20px'
        }
    },        
    {
        'selector': ':parent.expanded',
        'style': {
            'text-valign': 'bottom',
            'text-margin-y': '5px'
        }
    },
    {
        'selector': 'edge[rating = 1]',
        'style': {
            'line-color': '#ff7851', 
            'target-arrow-color': '#ff7851',
            'label': 'data(label)',  # Add label style here
            'text-rotation': 'autorotate',
            'text-margin-x': 5,
            'color': 'white',  # Text color
            'text-background-color':'#ff7851',   # Text background color
            'text-background-opacity': 1,  # Text background opacity
            'text-background-padding': 2,  # Text background padding
            'font-size': 'mapData(width, 1, 10, 10, 30)'  # Font size mapping function, adjust as necessary
        }
    },
    {
        'selector': 'edge[rating = 2]',
        'style': {
            'line-color': '#f3969a',
            'target-arrow-color': '#f3969a',
            'label': 'data(label)',  # Add label style here
            'text-rotation': 'autorotate',
            'text-margin-x': 5,
            'color': 'white',  # Text color
            'text-background-color': '#f3969a',  # Text background color
            'text-background-opacity': 1,  # Text background opacity
            'text-background-padding': 2,  # Text background padding
            'font-size': 'mapData(width, 1, 10, 10, 30)'  # Font size mapping function, adjust as necessary
        }
    },
    {
        'selector': 'edge[rating = 3]',
        'style': {
            'line-color': '#6cc3d5',
            'target-arrow-color': '#6cc3d5' ,
            'label': 'data(label)',  # Add label style here
            'text-rotation': 'autorotate',
            'text-margin-x': 5,
            'color': 'white',  # Text color
            'text-background-color': '#6cc3d5',  # Text background color
            'text-background-opacity': 1,  # Text background opacity
            'text-background-padding': 2,  # Text background padding
            'font-size': 'mapData(width, 1, 10, 10, 30)'  # Font size mapping function, adjust as necessary
        }
    },
    {
        'selector': 'edge[rating = 4]',
        'style': {
            'line-color': '#78c2ad', 
            'target-arrow-color': '#78c2ad',
            'label': 'data(label)',  # Add label style here
            'text-rotation': 'autorotate',
            'text-margin-x': 5,
            'color': 'white',  # Text color
            'text-background-color': '#78c2ad',  # Text background color
            'text-background-opacity': 1,  # Text background opacity
            'text-background-padding': 2,  # Text background padding
            'font-size': 'mapData(width, 1, 10, 10, 30)'  # Font size mapping function, adjust as necessary
        }
    },
    {
        'selector': 'edge[rating = 5]',
        'style': {
            'line-color': '#56cc9d',
            'target-arrow-color': '#56cc9d',
            'label': 'data(label)',  # Add label style here
            'text-rotation': 'autorotate',
            'text-margin-x': 5,
            'color': 'white',  # Text color
            'text-background-color': '#56cc9d', # Text background color
            'text-background-opacity': 1,  # Text background opacity
            'text-background-padding': 2,  # Text background padding
            'font-size': 'mapData(width, 1, 10, 10, 30)'  # Font size mapping function, adjust as necessary
        }
    }
]




# Create an SQLAlchemy engine to connect to the database
# from sqlalchemy import create_engine
# engine = create_engine('postgresql://postgres:mysecretpassword@localhost/postgres')
# Query the weighted_trait_graph table for the required data
# query = f"""
#     SELECT asin, data_label, cluster_label, type, rating_avg, rating, id, cluster_problem_statement, cluster_solution_1_title, cluster_solution_1_description, cluster_solution_2_title, cluster_solution_2_description, cluster_solution_3_title, cluster_solution_3_description
#     FROM weighted_trait_graph 
#     WHERE asin IN ({','.join(['%s']*len(asin_list))})
# """
# weighted_trait_df_graph = pd.read_sql_query(query, engine, params=asin_list)
# Query the products table for the required data
# query = f"""
#     SELECT asin, main_image, title 
#     FROM products 
#     WHERE asin IN ({','.join(['%s']*len(asin_list))})
# """
# products_df = pd.read_sql_query(query, engine, params=asin_list)


# ASIN values to be used for filtering
asin_list_path = 'data/external/asin_list.csv'
asin_list = pd.read_csv('asin_list.csv')['asin'].tolist()

# Read the cluster_solutions table for the required data
cluster_solution_path = 'data/processed/cluster_solutions_export.csv'
solutions_df = pd.read_csv('cluster_solutions.csv')

review_path = 'data/processed/reviews_export.csv'
reviews_df = pd.read_csv(review_path)

products_path = 'data/processed/products_export.csv'
products_df = pd.read_csv(products_path)

# Read the traits information from the database
weighted_trait_df_graph_path = 'data/processed/weighted_trait_graph_export.csv'
weighted_trait_df_graph = pd.read_csv(weighted_trait_df_graph_path)
weighted_trait_df_graph['id'] = weighted_trait_df_graph['id'].map(eval)

# Function to concatenate the lists but keep only distinct elements
def unique_elements(lst):
    return list(set([i for sublist in lst for i in sublist]))

# Group the DataFrame by 'cluster_label', apply the function to 'id_list'
grouped_df = weighted_trait_df_graph.groupby('cluster_label').agg({'id': unique_elements}).reset_index()

# Merge this DataFrame with the original one to create the 'cluster_id_list' column
weighted_trait_df_graph = pd.merge(weighted_trait_df_graph, grouped_df, how="left", on="cluster_label")
weighted_trait_df_graph.rename(columns={"id_y": "cluster_id_list", "id_x":"id"}, inplace=True)



def normalize_observation_count(count, min_val=1, max_val=10):
    # Assumes count is a number from 1 to infinity
    # Adjust these parameters according to your requirements
    MIN_OBSERVATIONS = 1
    MAX_OBSERVATIONS = 20  # set this to a higher number if you have a very large number of observations
    return int(round(min_val + (max_val - min_val) * (count - MIN_OBSERVATIONS) / (MAX_OBSERVATIONS - MIN_OBSERVATIONS),0))

def normalize_font_size(count, min_font_size=20, max_font_size=40):
    # Assumes count is a number from 1 to infinity
    # Adjust these parameters according to your requirements
    MIN_OBSERVATIONS = 1
    MAX_OBSERVATIONS = 30  # set this to a higher number if you have a very large number of observations
    font_size = round(min_font_size + (max_font_size - min_font_size) * (count - MIN_OBSERVATIONS) / (MAX_OBSERVATIONS - MIN_OBSERVATIONS),0)
    return int(max(min_font_size, font_size))


# Create the nodes and edges of the graph
root_nodes = []
root_edges = []

# Add cluster nodes and product nodes and edges
for idx, row in weighted_trait_df_graph.iterrows():
    asin = row['asin']
    target_node = row['cluster_label']
    trait_type = row['type']
    id_list = row['cluster_id_list']
    width = normalize_observation_count(len(id_list))
    width = max(1, width)
    font_size = normalize_font_size(len(id_list))
    root_nodes.append({'data': {'id': asin, 'label': asin, 'type': 'Product', 'asin': asin}})
    root_nodes.append({'data': {'id': target_node, 'label': target_node, 'type': trait_type,  'asin': asin, 'id_list': id_list, 'fontSize': font_size}})
    root_edges.append({'data': {'source': asin, 'target': target_node, 'rating': int(round(row['rating_avg'], 0)), 'width': width, 'label': str(width)}})


# Add child nodes and edges
child_nodes = []
child_edges = []

for idx, row in weighted_trait_df_graph.iterrows():
    asin = row['asin']
    source_node = row['asin']
    parent_node = row['cluster_label']
    target_node = row['data_label']
    trait_type = row['type']
    id_list = row['id']
    width = normalize_observation_count(len(id_list))
    width = max(1, width)
    child_nodes.append({'data': {'id': target_node, 'label': target_node,  'parent': parent_node, 'type': 'ProblemChild', 'asin': asin, 'id_list': id_list, 'observationsCount': len(id_list)}})
    child_edges.append({'data': {'source': parent_node, 'target': target_node, 'rating': int(round(row['rating_avg'], 0)), 'width': width, 'label': str(width)}})



# Add solution nodes and edges
solution_nodes = []
solution_edges = []

for idx, row in solutions_df.iterrows():
    if row.isnull().any():
    # If any value is null, skip to the next iteration
        continue
    source_node = row['cluster_label']
    target_node = row['solution_title']
    trait_type = row['type']
    solution_nodes.append({'data': {'id': target_node, 'label': target_node, 'type': 'Solution'}})
    solution_edges.append({'data': {'source': source_node, 'target': target_node, 'width': 1 }})

nodes = root_nodes + child_nodes + solution_nodes
edges = root_edges + child_edges + solution_edges

# Add nodes and images for products_df
for idx, row in products_df.iterrows():
    source_node = row['asin']
    image = row['main_image']
    product_title = row['title']
    title = product_title[:50]
    
    # Check if the image value is not None
    if image is not None:
        # Find the existing node with the same id
        existing_node = next((node for node in nodes if node['data']['id'] == source_node), None)
        
        # If the node is found, update the faveIcon and label values
        if existing_node:
            existing_node['data']['faveIcon'] = image
            existing_node['data']['label'] = title  # Update the label value
        # If the node is not found, do nothing (skip to the next iteration)
        else:
            continue





# Combine nodes and edges into a single elements list
# elements = root_nodes + root_edges + child_nodes + child_edges + solution_nodes + solution_edges
nodes = root_nodes + solution_nodes
elements = root_nodes + root_edges + solution_nodes + solution_edges
# %%

app = dash.Dash(__name__,     
                external_stylesheets=[
                    'minty_bootstrap.min.css'
                ]
)

@app.callback(
    [Output('product-button', 'className'),
     Output('fact-button', 'className'),
     Output('issue-button', 'className'),
     Output('improvement-button', 'className'),
     Output('problem-child-button', 'className'),
     Output('solution-button', 'className'),
     Output('rating-1-button', 'className'),
     Output('rating-2-button', 'className'),
     Output('rating-3-button', 'className'),
     Output('rating-4-button', 'className'),
     Output('rating-5-button', 'className')],
    [Input('product-button', 'n_clicks'),
     Input('fact-button', 'n_clicks'),
     Input('issue-button', 'n_clicks'),
     Input('improvement-button', 'n_clicks'),
     Input('problem-child-button', 'n_clicks'),
     Input('solution-button', 'n_clicks'),
     Input('rating-1-button', 'n_clicks'),
     Input('rating-2-button', 'n_clicks'),
     Input('rating-3-button', 'n_clicks'),
     Input('rating-4-button', 'n_clicks'),
     Input('rating-5-button', 'n_clicks')]
)
def toggle_active_class(product_clicks, fact_clicks, issue_clicks, improvement_clicks, problem_child_clicks, solution_clicks , rating_1_clicks, rating_2_clicks, rating_3_clicks, rating_4_clicks, rating_5_clicks):
    button_clicks = [product_clicks, fact_clicks, issue_clicks, improvement_clicks, problem_child_clicks, solution_clicks  ,rating_1_clicks, rating_2_clicks, rating_3_clicks, rating_4_clicks, rating_5_clicks]
    class_names = ['btn btn-primary mr-2', 'btn btn-secondary mr-2', 'btn btn-warning mr-2', 'btn btn-info mr-2','btn btn-danger mr-2','btn btn-success mr-2', 'btn btn-secondary mr-2', 'btn btn-secondary mr-2', 'btn btn-secondary mr-2', 'btn btn-secondary mr-2', 'btn btn-secondary mr-2']
    
    return [class_name + ' active' if clicks and clicks % 2 != 0 else class_name for clicks, class_name in zip(button_clicks, class_names)]

@app.callback(
    [Output('product-button', 'n_clicks'),
     Output('fact-button', 'n_clicks'),
     Output('issue-button', 'n_clicks'),
     Output('improvement-button', 'n_clicks'),
     Output('problem-child-button', 'n_clicks'),
     Output('solution-button', 'n_clicks'),
     Output('rating-1-button', 'n_clicks'),
     Output('rating-2-button', 'n_clicks'),
     Output('rating-3-button', 'n_clicks'),
     Output('rating-4-button', 'n_clicks'),
     Output('rating-5-button', 'n_clicks')],
    [Input('refresh-button', 'n_clicks')],
)
def reset_buttons(n):
    return [1, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0]

def dropdown_options_list(*args):
    return [{'label': val.capitalize(), 'value': val} for val in args]


@app.callback(
    Output('database-table', 'data'),
    Output('database-table', 'columns'),
    Input('cytoscape', 'tapNodeData')
)
def display_node_data(data):
    if not data:
        return None, None

    node_id = data['id']
    node_type = data['type']

    if node_type == 'Product':
        selected_data = products_df[products_df['asin'] == node_id]
        columns = [{'name': column, 'id': column} for column in selected_data.columns]
        data = selected_data.to_dict('records')
        return data, columns
    
    elif node_type in ['Fact', 'Improvement', 'Issue', 'ProblemChild']:
        id_list = data['id_list']
        params = asin_list + id_list

        selected_data = reviews_df[(reviews_df['asin'].isin(asin_list)) & (reviews_df['id'].isin(id_list))]
        selected_data = selected_data[['asin_variant', 'rating', 'review_summary', 'review']]

        columns = [{'name': column, 'id': column} for column in selected_data.columns]
        data = selected_data.to_dict('records')
        return data, columns
    
    elif  node_type == 'Solution':
        selected_data = solutions_df.loc[solutions_df['solution_title'] == node_id, ['solution_details', 'problem_statement']].drop_duplicates()
        columns = [{'name': column, 'id': column} for column in ['solution_details','problem_statement']]
        data = selected_data.to_dict('records')
        return data, columns



@app.callback(
    Output('cytoscape', 'elements'),
    [Input('product-button', 'n_clicks'),
     Input('fact-button', 'n_clicks'),
     Input('issue-button', 'n_clicks'),
     Input('improvement-button', 'n_clicks'),
     Input('problem-child-button', 'n_clicks'),
     Input('solution-button', 'n_clicks'),
     Input('rating-1-button', 'n_clicks'),
     Input('rating-2-button', 'n_clicks'),
     Input('rating-3-button', 'n_clicks'),
     Input('rating-4-button', 'n_clicks'),
     Input('rating-5-button', 'n_clicks'),
     Input('expand-trait-button', 'n_clicks'),
     Input('expand-solution-button', 'n_clicks')],
    [State('cytoscape', 'selectedNodeData')]
)
def update_graph(product_clicks, fact_clicks, issue_clicks, improvement_clicks, problem_child_clicks, solution_clicks, rating_1_clicks, rating_2_clicks, rating_3_clicks, rating_4_clicks, rating_5_clicks, expand_trait_clicks, expand_solution_clicks, selectedNodeData):
    ctx = dash.callback_context

    if not ctx.triggered:
        return elements

    new_elements = elements

    # Check if the expand-trait-button was clicked
    if expand_trait_clicks and selectedNodeData:
        # Get the id of the selected node
        selected_node_id = selectedNodeData[0]['id']

        # Get the child nodes and edges associated with the selected node
        new_child_nodes = [node for node in child_nodes if node['data']['parent'] == selected_node_id]
        new_child_edges = [edge for edge in child_edges if edge['data']['source'] == selected_node_id]

        # Add the new child nodes and edges to the elements of the Cytoscape graph
        new_elements = new_elements + new_child_nodes + new_child_edges

    # Check if the expand-solution-button was clicked
    if expand_solution_clicks and selectedNodeData:
        # Get the id of the selected node
        selected_node_id = selectedNodeData[0]['id']

        # Get the parent nodes and edges associated with the selected node
        new_solution_nodes = [node for node in solution_nodes if node['data']['id'] == selected_node_id]
        new_solution_edges = [edge for edge in solution_edges if edge['data']['target'] == selected_node_id]

        # Add the new parent nodes and edges to the elements of the Cytoscape graph
        new_elements = new_elements + new_solution_nodes + new_solution_edges

    # Filter the edges based on the rating buttons
    filtered_rating_edges = [edge for edge in new_elements if
                        ('source' in edge['data'] and 'target' in edge['data']) and
                        (not 'rating' in edge['data'] or (
                                ('rating' in edge['data']) and (
                                    (edge['data']['rating'] == 1 and rating_1_clicks % 2 != 0) or
                                    (edge['data']['rating'] == 2 and rating_2_clicks % 2 != 0) or
                                    (edge['data']['rating'] == 3 and rating_3_clicks % 2 != 0) or
                                    (edge['data']['rating'] == 4 and rating_4_clicks % 2 != 0) or
                                    (edge['data']['rating'] == 5 and rating_5_clicks % 2 != 0)
                                )
                            ))
                        ]
    filtered_edges =  filtered_rating_edges
    
    # Filter the nodes to only show those that satisfy the node type conditions
    filtered_nodes = [node for node in new_elements if
                      ('type' in node['data']) and (
                              (node['data']['type'] == 'Product' and product_clicks % 2 != 0) or
                              (node['data']['type'] == 'Fact' and fact_clicks % 2 != 0) or
                              (node['data']['type'] == 'Issue' and issue_clicks % 2 != 0) or
                              (node['data']['type'] == 'Improvement' and improvement_clicks % 2 != 0) or
                              (node['data']['type'] == 'ProblemChild' and problem_child_clicks % 2 != 0) or
                              (node['data']['type'] == 'Solution' and solution_clicks % 2 != 0)
                      )]

    # Find the IDs of all filtered nodes
    filtered_node_ids = set([node['data']['id'] for node in filtered_nodes])

    # Filter the edges to only show those that have both source and target nodes in the filtered nodes
    filtered_edges = [edge for edge in filtered_edges if (edge['data']['source']) in filtered_node_ids and edge['data']['target'] in filtered_node_ids]
    
    # Find the IDs of all source and target nodes from the filtered edges
    filtered_edge_node_ids = set([edge['data']['source'] for edge in filtered_edges] + [edge['data']['target'] for edge in filtered_edges])

    # Filter the nodes to only show those that are present in the filtered edges (either as source or target)
    filtered_nodes = [node for node in filtered_nodes if node['data']['id'] in filtered_edge_node_ids]
    
    return filtered_nodes + filtered_edges


app.layout = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col([
                dbc.Button('Refresh', id='refresh-button', n_clicks=1, className='btn btn-primary mr-2'),
                dbc.Button('Product', id='product-button', n_clicks=1, className='btn btn-primary mr-2'),
                dbc.Button('Fact', id='fact-button', n_clicks=0, className='btn btn-secondary mr-2'),
                dbc.Button('Issue', id='issue-button', n_clicks=0, className='btn btn-warning mr-2'),
                dbc.Button('Improvement', id='improvement-button', n_clicks=1, className='btn btn-info mr-2'),
                dbc.Button('Problem Child', id='problem-child-button', n_clicks=1, className='btn btn-danger mr-2'),
                dbc.Button('Solution', id='solution-button', n_clicks=1, className='btn btn-success mr-2'),
                dbc.Button('Expand Trait', id='expand-trait-button', n_clicks=0, className='btn btn-success mr-2'),
                dbc.Button('Expand Solution', id='expand-solution-button', n_clicks=0, className='btn btn-success mr-2'),
            ], width=12),
            dbc.Col([
                dbc.Button('Rating 1', id='rating-1-button', n_clicks=1, className='btn btn-secondary mr-2'),
                dbc.Button('Rating 2', id='rating-2-button', n_clicks=1, className='btn btn-secondary mr-2'),
                dbc.Button('Rating 3', id='rating-3-button', n_clicks=0, className='btn btn-secondary mr-2'),
                dbc.Button('Rating 4', id='rating-4-button', n_clicks=0, className='btn btn-secondary mr-2'),
                dbc.Button('Rating 5', id='rating-5-button', n_clicks=0, className='btn btn-secondary mr-2'),
            ], width=12),
            dbc.Col([
                html.Label('Layout'),
                dcc.Dropdown(
                    id='dropdown-layout',
                    options=dropdown_options_list(
                        'random',
                        'grid',
                        'circle',
                        'concentric',
                        'breadthfirst',
                        'cose',
                        'cose-bilkent',
                        'dagre',
                        'cola',
                        'klay',
                        'spread',
                        'euler'
                    ),
                    value='klay',
                    clearable=False
                )
            ], width=3),
        ], className="my-4"),
    ], fluid=True),
    # Add the Cytoscape graph
    dbc.Container([
        cyto.Cytoscape(
            id='cytoscape',
            elements=elements,
            layout={'name': 'klay'}, # , 'spacingFactor':3
            style={'width': '100%', 'height': '60vh'},
            stylesheet=cyto_stylesheet
        )
    ], fluid=True),
    # Add a table to display the node data
    dbc.Container([
        html.Div(
            dash_table.DataTable(
                id='database-table',
                columns=[{"name": i, "id": i} for i in []],  # initialize with an empty list
                style_header={
                                    'backgroundColor': '#9fcbae',
                                    'fontWeight': 'bold',
                                    'color': 'white',
                                    'font-family': 'Arial, sans-serif'
                                },
                    style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': '#f8f9fa',
                    },
                    {
                        'if': {'column_id': 'rating'},
                        'width': '100px'
                    },
                    {
                        'if': {'column_id': 'asin_variant'},
                        'width': '100px'
                    },
                    {
                        'if': {'column_id': 'review_summary'},
                        'width': 'auto'
                    }
                ],
                style_data={
                    'height': 'auto', 
                    'width': 'auto',
                    'whiteSpace': 'normal',
                    'backgroundColor': 'white'
                },
                style_table={
                    'overflowX': 'scroll',
                    'width': '100%',
                    'minWidth': '100%',
                },
                style_cell={
                    'textAlign': 'left',
                    'padding': '5px',
                    'font-family': 'Arial, sans-serif'
                },
                style_cell_conditional=[
        {
            'if': {'column_id': 'rating'},
            'textAlign': 'center'
        },
        {
            'if': {'column_id': 'asin_variant'},
            'textAlign': 'center'
        }
        ], style_as_list_view=True
            ),
            className='dash-table-container',  # add this line
            style={'width': '100%', 'overflowY': 'auto', 'height': '400px'}
        )
    ], fluid=True)

])


# Callback to update the layout of the Cytoscape graph
@app.callback(Output('cytoscape', 'layout'),
              [Input('dropdown-layout', 'value')])
def update_cytoscape_layout(layout):
    return {'name': layout}

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)