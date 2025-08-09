# routes.py (Hardened + Debug logging + session fixes)

from flask import (
    Blueprint, render_template, redirect, url_for, flash, request, make_response,
    jsonify, current_app, abort, session
)
from app import db, bcrypt, limiter
from app.forms import RegistrationForm, LoginForm, BudgetForm, DeleteAccountForm
from app.models import User, BudgetEntry, Category
from flask_login import login_user, current_user, logout_user, login_required
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from calendar import month_name
from app.utils import admin_required
from sqlalchemy.exc import IntegrityError
import csv
import io

main = Blueprint('main', __name__)

@main.app_errorhandler(429)
def ratelimit_handler(e):
    if request.path == "/login":
        return render_template("429.html"), 429
    return jsonify(error="Too many requests. Please try again later."), 429

# ---- Debug: who is logged in?
@main.route("/_whoami")
def whoami():
    return {
        "authenticated": current_user.is_authenticated,
        "email": getattr(current_user, "email", None)
    }, 200

@main.route("/")
@main.route("/home")
def home():
    return redirect(url_for('main.login'))

@main.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(email=form.email.data, password=hashed_pw, role='user')
        db.session.add(user)
        db.session.commit()

        # Default categories
        default_categories = ['Food', 'Rent', 'Utilities', 'Salary', 'Entertainment', 'Other']
        for cat in default_categories:
            db.session.add(Category(name=cat, user_id=user.id))
        db.session.commit()

        current_app.logger.info(f"[REGISTER] New user created: {user.email} (ID: {user.id})")
        flash('Account created!', 'success')
        return redirect(url_for('main.login'))
    else:
        if form.errors:
            current_app.logger.warning(f"[REGISTER] Failed: {form.errors}")

    return render_template('register.html', form=form)

@main.route("/login", methods=['GET', 'POST'])
@limiter.exempt   # ⬅️ disable rate limit during debugging
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user:
            current_app.logger.info(f"[LOGIN] User found in DB: {user.email} (ID: {user.id})")
        else:
            current_app.logger.warning(f"[LOGIN] No user found with email: {form.email.data}")

        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            current_app.logger.info(f"[LOGIN] SUCCESS for {user.email}")
            return redirect(url_for('main.dashboard'))
        else:
            current_app.logger.warning(f"[LOGIN] FAILED for {form.email.data}")
            flash('Login failed. Please check your email or password.', 'danger')
    else:
        if form.errors:
            current_app.logger.warning(f"[LOGIN] Form errors: {form.errors}")

    return render_template('login.html', form=form)

@main.route("/logout")
@login_required
def logout():
    current_app.logger.info(f"User {current_user.email} logged out")
    logout_user()
    session.clear()  # ⬅️ ensure no stale session data remains
    flash("Logged out successfully.", "info")
    return redirect(url_for('main.login'))

@main.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    form = BudgetForm()
    delete_form = DeleteAccountForm()

    # Load user's categories for form
    categories = Category.query.filter_by(user_id=current_user.id).all()
    form.category.choices = [(c.name, c.name) for c in categories]

    # Process BudgetForm submission
    if form.validate_on_submit():
        entry = BudgetEntry(
            date=form.date.data,
            category=form.category.data,
            amount=form.amount.data,
            type=form.type.data,
            user_id=current_user.id
        )
        db.session.add(entry)
        db.session.commit()
        current_app.logger.info(f"{current_user.email} added {entry.type}: {entry.category} - ₹{entry.amount}")
        flash("Entry added successfully!", "success")
        return redirect(url_for('main.dashboard'))

    # Filters
    selected_category = request.args.get("category", default=None, type=str)
    selected_type = request.args.get("type", default=None, type=str)
    start_date = request.args.get("start_date", type=str)
    end_date = request.args.get("end_date", type=str)

    query = BudgetEntry.query.filter_by(user_id=current_user.id)
    if selected_category:
        query = query.filter_by(category=selected_category)
    if selected_type:
        query = query.filter_by(type=selected_type)
    if start_date:
        query = query.filter(BudgetEntry.date >= datetime.strptime(start_date, "%Y-%m-%d").date())
    if end_date:
        query = query.filter(BudgetEntry.date <= datetime.strptime(end_date, "%Y-%m-%d").date())

    entries = query.order_by(BudgetEntry.date.desc()).all()

    # Summary
    total_income = sum(e.amount for e in entries if e.type == "income")
    total_expense = sum(e.amount for e in entries if e.type == "expense")
    balance = total_income - total_expense

    # AI Tips
    tips = []
    recent_entries = [e for e in entries if e.date >= datetime.today().date() - timedelta(days=30)]
    if total_income > 0 and total_expense > total_income * 0.5:
        tips.append("⚠️ You’ve spent more than 50% of your income in the last 30 days.")
    food_expenses = sum(e.amount for e in recent_entries if e.category.lower() == "food")
    if food_expenses > 150:
        tips.append("🍔 Your food expenses are high. Consider meal planning.")

    # Chart Data (last 6 months of expenses)
    monthly_data = defaultdict(float)
    for e in entries:
        if e.type == "expense":
            key = f"{month_name[e.date.month]} {e.date.year}"
            monthly_data[key] += e.amount

    chart_labels = list(monthly_data.keys())[-6:]
    chart_data = list(monthly_data.values())[-6:]

    return render_template(
        "dashboard.html",
        form=form,
        delete_form=delete_form,
        entries=entries,
        tips=tips,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
        chart_labels=chart_labels,
        chart_data=chart_data,
        categories=categories,
        selected_category=selected_category,
        selected_type=selected_type,
        start_date=start_date,
        end_date=end_date
    )

@main.route("/edit/<int:entry_id>", methods=["GET", "POST"])
@login_required
def edit_entry(entry_id):
    entry = BudgetEntry.query.get_or_404(entry_id)
    if entry.user_id != current_user.id:
        flash("You are not authorized to edit this entry.", "danger")
        return redirect(url_for("main.dashboard"))

    form = BudgetForm(obj=entry)
    form.category.choices = [(c.name, c.name) for c in Category.query.filter_by(user_id=current_user.id)]

    if form.validate_on_submit():
        entry.date = form.date.data
        entry.category = form.category.data
        entry.amount = form.amount.data
        entry.type = form.type.data
        db.session.commit()
        current_app.logger.info(f"{current_user.email} edited entry #{entry.id}")
        flash("Entry updated successfully.", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("edit_entry.html", form=form)

@main.route("/delete/<int:entry_id>", methods=["POST"])
@login_required
def delete_entry(entry_id):
    entry = BudgetEntry.query.get_or_404(entry_id)
    if entry.user_id != current_user.id:
        flash("You are not authorized to delete this entry.", "danger")
        return redirect(url_for("main.dashboard"))

    db.session.delete(entry)
    db.session.commit()
    current_app.logger.info(f"{current_user.email} deleted entry #{entry.id}")
    flash("Entry deleted successfully.", "success")
    return redirect(url_for("main.dashboard"))

@main.route("/download_csv")
@login_required
def download_csv():
    entries = BudgetEntry.query.filter_by(user_id=current_user.id).order_by(BudgetEntry.date.desc()).all()
    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(["Date", "Category", "Amount", "Type"])
    for e in entries:
        writer.writerow([e.date.strftime('%Y-%m-%d'), e.category, e.amount, e.type])
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=budget_entries.csv"
    output.headers["Content-type"] = "text/csv"
    current_app.logger.info(f"{current_user.email} downloaded budget CSV")
    return output

@main.route("/download_json")
@login_required
def download_json():
    entries = BudgetEntry.query.filter_by(user_id=current_user.id).all()
    data = [
        {
            "date": e.date.strftime('%Y-%m-%d'),
            "category": e.category,
            "amount": e.amount,
            "type": e.type
        }
        for e in entries
    ]
    current_app.logger.info(f"{current_user.email} downloaded JSON data")
    return jsonify(data)

@main.route("/add_category", methods=["POST"])
@login_required
def add_category():
    category_name = request.form.get("new_category")
    if category_name:
        exists = Category.query.filter_by(name=category_name, user_id=current_user.id).first()
        if not exists:
            db.session.add(Category(name=category_name, user_id=current_user.id))
            db.session.commit()
            current_app.logger.info(f"{current_user.email} added new category: {category_name}")
            flash("Category added!", "success")
        else:
            flash("Category already exists.", "warning")
    return redirect(url_for('main.dashboard'))

@main.route("/delete_account", methods=["POST"])
@login_required
def delete_account():
    form = DeleteAccountForm()
    if form.validate_on_submit():
        user = current_user
        BudgetEntry.query.filter_by(user_id=user.id).delete()
        Category.query.filter_by(user_id=user.id).delete()
        db.session.delete(user)
        db.session.commit()
        logout_user()
        flash("Your account and data have been deleted.", "info")
        return redirect(url_for("main.login"))
    flash("Invalid CSRF token or form submission.", "danger")
    return redirect(url_for("main.dashboard"))

@main.route("/admin/logs")
@login_required
@admin_required
def view_logs():
    try:
        with open('logs/audit.log', 'r') as file:
            log_data = file.read()
    except FileNotFoundError:
        log_data = "No logs found."
    return render_template('admin_logs.html', logs=log_data)

@main.app_errorhandler(403)
def forbidden(e):
    return render_template("403.html"), 403

@main.route("/admin/dashboard")
@login_required
@admin_required
def admin_dashboard():
    users = User.query.all()
    entries = BudgetEntry.query.all()
    categories = Category.query.distinct(Category.name).count()

    category_counts = Counter([e.category for e in entries])
    top_categories = category_counts.most_common(5)
    recent_users = User.query.order_by(User.id.desc()).limit(5).all()

    log_data = ""
    try:
        with open('logs/audit.log', 'r') as file:
            log_data = file.read().strip()
    except FileNotFoundError:
        log_data = "No logs found."

    return render_template(
        "admin_dashboard.html",
        total_users=len(users),
        total_entries=len(entries),
        total_categories=categories,
        top_categories=top_categories,
        recent_users=recent_users,
        logs=log_data
    )
