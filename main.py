import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from config import SECRET_KEY
from db import db
from routes import register_blueprints

app = Flask(__name__)
app.secret_key = SECRET_KEY

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:mysql123@localhost/dashcapital'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

register_blueprints(app)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=1158)

#merge version 1.0 