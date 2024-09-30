from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, PasswordField, IntegerField
from wtforms.validators import DataRequired
import random
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'
csrf = CSRFProtect(app)

DATABASE = 'game.db'

def get_db():
    """Connect to the SQLite database."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

class LoginForm(FlaskForm):
    """Form for user login."""
    username = StringField('username', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])

class GuessForm(FlaskForm):
    """Form for submitting guesses."""
    guess = IntegerField('guess', validators=[DataRequired()])

@app.route('/')
def home():
    """Redirect to the login page."""
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        # Hardcoded user login
        if username == 'player' and password == 'password':
            session['username'] = username
            session['score'] = 0
            session['attempts'] = 0
            session['number'] = random.randint(1, 10)
            # Drop game table records for the current user
            drop_game_records(username)
            save_user_to_db(username, password)
            return redirect(url_for('game'))
        else:
            flash('Invalid credentials, please try again.', 'danger')
    return render_template('login.html', form=form)

@app.route('/game', methods=['GET', 'POST'])
def game():
    """Handle the game logic."""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    form = GuessForm()
    message = ""
    if form.validate_on_submit():
        guess = form.guess.data
        number = session['number']
        attempts = session['attempts']
        
        if guess == number:
            message = "Congratulations, you did it."
            session['score'] += 1
            session['attempts'] = 0  # Reset attempts after a correct guess
            session['number'] = random.randint(1, 10)  # Generate a new random number
            form.guess.data = ''  # Clear the guess input field
        elif guess < number:
            message = "Hint: You guessed too small!"
            attempts += 1
            session['attempts'] = attempts
        else:
            message = "Hint: You guessed too high!"
            attempts += 1
            session['attempts'] = attempts
        
        if attempts >= 5 and guess != number:
            message = f"Sorry, you've used all your attempts! The correct number was {number}."
            session['attempts'] = 0  # Reset attempts after max attempts
            session['number'] = random.randint(1, 10)  # Generate a new random number
        
        # Update game details in the database
        update_game_details(session['username'], session['score'], guess)

    return render_template('game.html', form=form, score=session['score'], message=message)

@app.route('/logout', methods=['POST'])
def logout():
    """Handle user logout."""
    session.clear()
    return redirect(url_for('login'))

def save_user_to_db(username, password):
    """Save user to the database."""
    conn = get_db()
    with conn:
        # Insert or update user in the database
        conn.execute('''INSERT OR REPLACE INTO users (username, password) VALUES (?, ?)''', (username, password))
        # Insert or ignore game record if it doesn't exist
        conn.execute('''INSERT OR IGNORE INTO game (username, score, last_guess) VALUES (?, ?, ?)''', (username, 0, None))

def update_game_details(username, score, guess):
    """Update game details in the database."""
    conn = get_db()
    cursor = conn.cursor()
    with conn:
        # Update the game score and last guessed number if the row exists
        cursor.execute('''UPDATE game SET score = ?, last_guess = ? WHERE username = ?''', (score, guess, username))
        # If no rows were affected, insert a new row
        if cursor.rowcount == 0:
            cursor.execute('''INSERT INTO game (username, score, last_guess) VALUES (?, ?, ?)''', (username, score, guess))

def drop_game_records(username):
    """Drop game records for the current user."""
    conn = get_db()
    with conn:
        conn.execute('''DELETE FROM game WHERE username = ?''', (username,))

if __name__ == '__main__':
    # Initialize the database if it doesn't exist
    if not os.path.exists(DATABASE):
        conn = get_db()
        with conn:
            conn.execute('''CREATE TABLE users (username TEXT PRIMARY KEY, password TEXT)''')
            conn.execute('''CREATE TABLE game (
                                id INTEGER PRIMARY KEY,
                                username TEXT UNIQUE,
                                score INTEGER,
                                last_guess INTEGER,
                                FOREIGN KEY(username) REFERENCES users(username)
                            )''')
        conn.close()
    app.run(debug=True)
