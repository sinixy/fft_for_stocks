from flask import Flask
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
uri = os.environ['DATABASE_URL']
if uri and uri.startswith("postgres://"):
	uri = uri.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


import fourier.views