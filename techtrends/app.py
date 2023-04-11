import sqlite3

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort
from datetime import datetime
import logging
import sys

# Count cumulated database connections made
cumul_connection_count = 0

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    global cumul_connection_count
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    cumul_connection_count += 1
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
      logging_post('Article with id="{id}" does not exist!'.format(id=post_id), 1)
      return render_template('404.html'), 404
    else:
      logging_post('Article T="{title}" successfully retrieved!'.format(title=post['title']), 0)
      return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    logging_post('About page retrieval success!', 0)
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()
            logging_post('New article T="{title}" created!'.format(title=title), 0)

            return redirect(url_for('index'))

    return render_template('create.html')


# Define healthz endpoint with Flask + function definition
@app.route("/healthz")
def healthz():

    connection = get_db_connection()
    connection.cursor()
    connection.execute("SELECT * FROM posts")
    connection.close()
    
    result = {"HTTP\1": 200, "result": "Ok - healthy"}
    return result


# Define metrics endpoint with Flask + function definition
@app.route("/metrics")
def metrics():

    try:
        connection = get_db_connection()
        posts = connection.execute("SELECT * FROM posts").fetchall()
        connection.close()

        status_code= 200
        posts_numb = len(posts)
        
        data = {"db_connection_count": cumul_connection_count, "post_count": posts_numb}
        result = {"HTTP\1": status_code, "responce": data}
        return result
    except Exception:
        
        status_code= 500
        return {"result": "ERROR - [ Metrics ] with code"}, status_code


# Logging_post function
def logging_post(msg, input):
    if input == 0:
        app.logger.info(
            '{time} | {post}'.format( time=datetime.now().strftime("%d/%m/%Y, %H:%M:%S"), post=msg))
        sys.stdout.write(
            '{time} | {post} \n'.format( time=datetime.now().strftime("%d/%m/%Y, %H:%M:%S"), post=msg))
        
    if input == 1:
        app.logger.error(
            '{time} | {post}'.format( time=datetime.now().strftime("%d/%m/%Y, %H:%M:%S"), post=msg))
        sys.stderr.write(
            '{time} | {post} \n'.format( time=datetime.now().strftime("%d/%m/%Y, %H:%M:%S"), post=msg))
                
        

# start the application on port 3111
if __name__ == "__main__":
    ## configure logs to debug level
    logging.basicConfig(level=logging.DEBUG)

    app.run(host='0.0.0.0', port='3111')
