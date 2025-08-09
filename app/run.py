# app/run.py
from app import create_app, db

app = create_app()

# Auto-create tables on first boot (works on Render free tier)
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
