#############
# __init__.py
import connexion

# Create an instance of Connexion
connex_app = connexion.App(__name__, specification_dir='./')

# Add the API to Connexion, which implicitly creates the Flask app
connex_app.add_api('swagger.yaml')

# Expose the underlying Flask app
app = connex_app.app
#===============