"""Point d'entree de l'application"""
import os
from app.main import create_app

config_name = os.getenv('FLASK_ENV', 'development')
app, socketio = create_app(config_name)

if __name__ == '__main__':
    socketio.run(app, host=app.config['HOST'], port=app.config['PORT'], debug=app.config['DEBUG'])
