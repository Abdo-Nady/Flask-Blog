from flask import Flask, render_template, request, redirect, url_for, session, flash

import psycopg2
from psycopg2.extras import RealDictCursor
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
import os

load_dotenv() 

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

bcrypt = Bcrypt(app)

########################## DB MODELS ##################################
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)
    
   
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(300))
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)




@app.route("/")
def home():
    return render_template('home.html')

@app.route("/Posts" , methods=['GET'])
def posts_list():
    post = Post.query.all()
    return render_template('posts.html' , posts=post)

@app.route("/register" , methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form.get('confirm_password')
        if not username or not password or not confirm_password:
            flash('Please fill out all fields!')
        elif password != confirm_password:
             flash('Passwords do not match!')
        else:   
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            
            user=User(username=username, password=hashed_password) 
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
            
    return render_template('register.html')





@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            session['username'] = user.username
            flash('Login successful.', 'success')
            return redirect(url_for('welcome', username=username))
        else:
            flash('Invalid credentials.', 'error')
    return render_template('login.html')


@app.route('/profile')
def profile():
    if not session.get('username'): 
        flash('You must be logged in to view your profile!', 'danger')
        return redirect(url_for('login'))
    username = session['username']
    return render_template('profile.html', username=username)


@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Logged out.', 'success')
    return redirect(url_for('home'))

@app.route("/welcome")
def welcome():
    username = request.args.get('username', 'Guest')  
    return render_template('welcome.html', username=username)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=8000)
