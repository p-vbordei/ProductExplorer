"""
#############
# __init__.py
from flask import Flask
import connexion

app = Flask(__name__)
connex_app = connexion.App(__name__, specification_dir='../')
connex_app.add_api('swagger.yaml')
app = connex_app.app
#===============
"""

#############
# __init__.py
import connexion

# Create an instance of Connexion
connex_app = connexion.App(__name__, specification_dir='../')

# Add the API to Connexion, which implicitly creates the Flask app
connex_app.add_api('swagger.yaml')

# Expose the underlying Flask app
app = connex_app.app
#===============