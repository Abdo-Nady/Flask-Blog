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
    
    return render_template('home.html' )

@app.route("/posts" , methods=['GET'])
def posts_list():
    posts = Post.query.all()
    return render_template('posts.html' , posts=posts)


@app.route("/create_post" , methods=['GET','POST'])
def create_post():
    if request.method == 'POST':
        title= request.form['title']
        content= request.form['content']
        image_url= request.form.get('image_url')
        username = session.get('username')
        user = User.query.filter_by(username=username).first()
        if user:
            new_post = Post(title=title, content=content, image_url=image_url, author=user)
            db.session.add(new_post)
            db.session.commit()
            flash('Post created successfully!', 'success')
            return redirect(url_for('posts_list'))
        else:
            flash('You must be logged in to create a post!', 'danger')
            return redirect(url_for('login'))
    return render_template('create_post.html')

@app.route("/posts/<int:post_id>/delete" , methods=['POST'])
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted successfully!', 'success')
    return redirect(url_for('posts_list'))

@app.route("/posts/<int:post_id>" , methods=['GET'])
def view_post(post_id):
    print("Viewing post with ID:", post_id)
    post = Post.query.get_or_404(post_id)
    return render_template('view_post.html', post=post) 



@app.route("/edit_post/<int:post_id>/edit" , methods=['GET','POST'])
def edit_post(post_id):
    if request.method == 'POST':
        post = Post.query.get_or_404(post_id)
        post.title= request.form['title']
        post.content= request.form['content']
        post.image_url= request.form.get('image_url')
        db.session.commit()
        flash('Post updated successfully!', 'success')
        return redirect(url_for('posts_list'))
    post = Post.query.get_or_404(post_id)
    return render_template('edit_post.html', post=post)
            
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
        elif User.query.filter_by(username=username).first():
            flash('Username already exists! Please choose a different one.' , 'error')
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
        if (not username) or (not password):
            flash('Please enter both username and password.', 'error')
            return render_template('login.html')
        
        user = User.query.filter_by(username=username).first() 
        if user and bcrypt.check_password_hash(user.password, password):
            session['username'] = user.username
            session['user_id'] = user.id 
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
    app.run(debug=True, host='0.0.0.0', port=8000)
