ProductExplorer
==============================

A software to enhance product teams work, enabeling them quick access to review insights and proposed solutions. Powered by AI and Knowledge Graphs


Run test visuals
python ./src/visualization/DASH_Traits_Graph_Cytoscape.py

Project Organization
------------

    ├── LICENSE
    ├── Makefile           <- Makefile with commands like `make data` or `make train`
    ├── README.md          <- The top-level README for developers using this project.
    ├── data
    │   ├── external       <- Data from third party sources.
    │   ├── interim        <- Intermediate data that has been transformed.
    │   ├── processed      <- The final, canonical data sets for modeling.
    │   └── raw            <- The original, immutable data dump.
    │
    ├── docs               <- A default Sphinx project; see sphinx-doc.org for details
    │
    ├── models             <- Trained and serialized models, model predictions, or model summaries
    │
    ├── notebooks          <- Jupyter notebooks. Naming convention is a number (for ordering),
    │                         the creator's initials, and a short `-` delimited description, e.g.
    │                         `1.0-jqp-initial-data-exploration`.
    │
    ├── references         <- Data dictionaries, manuals, and all other explanatory materials.
    │
    ├── reports            <- Generated analysis as HTML, PDF, LaTeX, etc.
    │   └── figures        <- Generated graphics and figures to be used in reporting
    │
    ├── requirements.txt   <- The requirements file for reproducing the analysis environment, e.g.
    │                         generated with `pip freeze > requirements.txt`
    │
    ├── setup.py           <- makes project pip installable (pip install -e .) so src can be imported
    ├── src                <- Source code for use in this project.
    │   ├── __init__.py    <- Makes src a Python module
    │   │
    │   ├── data           <- Scripts to download or generate data
    │   │   └── make_dataset.py
    │   │
    │   ├── features       <- Scripts to turn raw data into features for modeling
    │   │   └── build_features.py
    │   │
    │   ├── models         <- Scripts to train models and then use trained models to make
    │   │   │                 predictions
    │   │   ├── predict_model.py
    │   │   └── train_model.py
    │   │
    │   └── visualization  <- Scripts to create exploratory and results oriented visualizations
    │       └── visualize.py
    │
    └── tox.ini            <- tox file with settings for running tox; see tox.readthedocs.io


--------



#### Copy code

!docker run --name my_postgres -e POSTGRES_PASSWORD=mysecretpassword -p 5432:5432 -d postgres

!pip install psycopg2-binary

!docker pull dpage/pgadmin4

!docker run --name my_pgadmin -p 80:80 -e "PGADMIN_DEFAULT_EMAIL=binarybear@gmail.com" -e 
"PGADMIN_DEFAULT_PASSWORD=admin" --link my_postgres -d dpage/pgadmin4



#### Run all

Open your browser and navigate to [http://localhost](http://localhost) (or [http://127.0.0.1](http://127.0.0.1)) to access the pgAdmin web interface.

Log in to pgAdmin using the email and password you set in the `my_pgadmin` container.

Add the PostgreSQL server to pgAdmin:

1. Right-click on "Servers" in the left-side pane and select "Create > Server".
2. In the "General" tab, provide a name for the connection (e.g., "My PostgreSQL Server").
3. In the "Connection" tab, set the following fields:
   - Hostname/address: `my_postgres`
   - Port: `5432`
   - Maintenance database: `postgres`
   - Username: `postgres`
   - Password: `mysecretpassword` (the one you set in the `my_postgres` container)
4. Click "Save" to add the server.


<p><small>Project based on the <a target="_blank" href="https://drivendata.github.io/cookiecutter-data-science/">cookiecutter data science project template</a>. #cookiecutterdatascience</small></p>
