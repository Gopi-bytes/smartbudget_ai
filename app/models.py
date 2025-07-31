from app import db, login_manager
from flask_login import UserMixin

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# User Model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    
    # ✅ Role: 'user' (default) or 'admin'
    role = db.Column(db.String(10), nullable=False, default='user')

    # Relationships
    categories = db.relationship('Category', backref='owner', lazy=True)
    entries = db.relationship('BudgetEntry', backref='owner', lazy=True)

    def __repr__(self):
        return f"<User {self.email}>"

# Category Model
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"<Category {self.name}>"

# Budget Entry Model
class BudgetEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'income' or 'expense'

    def __repr__(self):
        return f"<BudgetEntry {self.date} - {self.category} - {self.amount}€>"
