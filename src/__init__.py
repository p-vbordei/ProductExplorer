#############
# __init__.py
from flask import Flask
import connexion

app = Flask(__name__)
connex_app = connexion.App(__name__, specification_dir='../')
connex_app.add_api('swagger.yaml')

#===============