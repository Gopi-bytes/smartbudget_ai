from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, SelectField, DateField
from wtforms.validators import DataRequired, Email, EqualTo
from wtforms.validators import DataRequired, Length
from wtforms import SubmitField

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])

# Registration form
class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

# Login form
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# Budget entry form
class BudgetForm(FlaskForm):
    date = DateField('Date', validators=[DataRequired()])
    
    # ✅ Leave choices empty; they are loaded dynamically
    category = SelectField('Category', choices=[], validators=[DataRequired()])
    
    amount = FloatField('Amount', validators=[DataRequired()])
    type = SelectField('Type', choices=[('income', 'Income'), ('expense', 'Expense')], validators=[DataRequired()])
    submit = SubmitField('Add Entry')
# Delete account form
class DeleteAccountForm(FlaskForm):
    submit = SubmitField('Delete My Account')
