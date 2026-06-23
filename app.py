from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = 'lasyapriya'  

# Database connection
def get_db_connection():
    conn = sqlite3.connect('tech_vision.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    return render_template('login.html')
@app.route('/index')
def index():
    if 'user_id' not in session:
        flash('You must be logged in to access this page.', 'error')
        return redirect(url_for('login'))
    return render_template('index.html')  

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('Please fill in all fields.', 'error')
            return redirect(url_for('login'))

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if not user:
            flash('No account found with this username. Please sign up first.', 'error')
            return redirect(url_for('login'))

        if check_password_hash(user['password'], password):
            session['user_id'] = user['id']  # Store user_id in session
            session['username'] = user['username']
            session['email'] = user['email']
            return redirect(url_for('index'))

        else:
            flash('Incorrect password. Please try again.', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        
        # Check if the username and email already exist in the database
        conn = get_db_connection()
        user_by_username = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        user_by_email = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        
        if user_by_username and user_by_email:
            flash('An account with this email and username already exists. Please log in.', 'error')
            return redirect(url_for('login'))
        elif user_by_username:
            flash('Username already exists. Please choose a different username.', 'error')
            return redirect(url_for('signup'))
        elif user_by_email:
            flash('Email is already associated with another account. Please use a different email.', 'error')
            return redirect(url_for('signup'))
        
        # Hash the password before storing it in the database
        hashed_password = generate_password_hash(password)

        # Insert the new user into the database if the username and email don't exist
        conn.execute('INSERT INTO users (email, username, password) VALUES (?, ?, ?)', (email, username, hashed_password))
        conn.commit()
        conn.close()

        flash('Account created successfully! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/favorites')
def favorites():
    if 'user_id' not in session:
        flash('You must be logged in to view your favorites.', 'error')
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection()

    # Fetch favorite technologies for the user
    favorites = conn.execute('SELECT tech_name FROM favorites WHERE user_id = ?', (user_id,)).fetchall()
    conn.close()

    # Convert the result to a list
    favorite_techs = [favorite['tech_name'] for favorite in favorites]

    return render_template('favorites.html', favorites=favorite_techs)


@app.route('/technology')
def technology_home():
    if 'user_id' not in session:
        flash('You must be logged in to access this page.', 'error')
        return redirect(url_for('login'))
    return render_template('technology.html')

@app.route('/technology/<tech_name>')
def technology(tech_name):
    if 'user_id' not in session:
        flash('You must be logged in to access this page.', 'error')
        return redirect(url_for('login'))

    tech_name = tech_name.lower()
    try:
        # Ensure that tech_name corresponds to an actual file
        return render_template(f'{tech_name}.html', tech_name=tech_name)  # Pass tech_name here
    except:
        flash(f"Technology page '{tech_name}' not found.", 'error')
        return redirect(url_for('technology_home'))

@app.route('/coding_platform_login/<platform_name>')
def coding_platform_login(platform_name):
    # Redirect to the appropriate platform's login page
    if platform_name == 'leetcode':
        return redirect("https://leetcode.com/accounts/login/")
    elif platform_name == 'hackerrank':
        return redirect("https://www.hackerrank.com/login")
    elif platform_name == 'hackerearth':
        return redirect("https://www.hackerearth.com/challenges/")
    elif platform_name == 'codechef':
        return redirect("https://www.codechef.com/login")
    elif platform_name == 'codeforces':
        return redirect("https://codeforces.com/enter")
    elif platform_name == 'topcoder':
        return redirect("https://www.topcoder.com/settings/sign-in")
    else:
     
        return "Platform not found", 404

@app.route('/logout')
def logout():
    session.pop('username', None)  
    session.pop('email', None)    
    session.clear()               
    flash('You have been logged out successfully. Please log in again to access your account.', 'success')
    return redirect(url_for('login'))

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('You must be logged in to view your profile.', 'error')
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection()
    
    # Get the user's favorite technologies
    favorites = conn.execute('SELECT tech_name FROM favorites WHERE user_id = ?', (user_id,)).fetchall()
    conn.close()

    # Convert the result into a list of tech names
    favorite_techs = [favorite['tech_name'] for favorite in favorites]

    user = {
        'username': session['username'],
        'email': session['email'],
        'favorites': favorite_techs  # Pass the list of favorite technologies
    }

    return render_template('profile.html', user=user)

@app.route('/add_to_favorites', methods=['POST'])
def add_to_favorites():
    if 'user_id' not in session:
        flash('You must be logged in to add favorites.', 'error')
        return redirect(url_for('login'))

    tech_name = request.form.get('tech_name').strip()  # Trim any extra spaces from the input
    user_id = session['user_id']


    tech_name_lower = tech_name.lower()

   
    conn = get_db_connection()
    existing_favorite = conn.execute('SELECT * FROM favorites WHERE user_id = ? AND LOWER(tech_name) = ?',
                                     (user_id, tech_name_lower)).fetchone()

    if existing_favorite:
        flash(f'{tech_name} is already in your favorites.', 'info')
    else:
        # Add the technology to the user's favorites (save original case)
        conn.execute('INSERT INTO favorites (user_id, tech_name) VALUES (?, ?)', (user_id, tech_name))
        conn.commit()
        flash(f'{tech_name} has been added to your favorites!', 'success')

    conn.close()
    return redirect(request.referrer)  # Redirect to the previous page




def init_db():
    conn = get_db_connection()
    
    # Create the 'users' table if it doesn't exist
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            reset_token TEXT
        );
    ''')
    
    # Create the 'favorites' table with tech_name column
    conn.execute('''
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            tech_name TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    ''')
    
    conn.commit()
    conn.close()



if __name__ == '__main__':
    init_db()
    app.run(debug=True)
