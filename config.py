import os

class Config:
    SECRET_KEY = 'your-secret-key'  # You can replace this with any random string
    SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
