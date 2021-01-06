from flask import Flask, render_template, url_for, flash, redirect, session, logging, request
# this imports the Flask class, render_template, url_for from the flask module
# the render_template is used to showcase the or render the html page called from a function within a route
# the url_for is used to go to some address/location
# the flash is used to flash messages on the screen
# the redirect is used to redirect the user to the new page/url

# from data import Articles
# importing the hard coded data from the data.py file

from flask_mysqldb import MySQL
# importing the flask mysql database

from wtforms import Form, StringField, TextAreaField, PasswordField, validators
# the wtforms is used for form validation and filling purpose

from passlib.hash import sha256_crypt
# from passlib.handlers.sha2_crypt import sha256_crypt
# the passlib.hash is used to encrypt the password

from functools import wraps
# importing the wraps in order to wrap multiple statements

app = Flask(__name__)
# creating an instance of the flask class

# config mysql
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = {"YOUR MYSQL PASSWORD"}
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# initialize mysql
mysql = MySQL(app)

# Articles = Articles()
# creating a instance of the data and using the articles function included 

# HOME
@app.route('/')
@app.route('/home')
# creating a route with the help of a decorator. A decorator once called runs all the code mentioned in it. 
# A decorator starts with a "@"
def home():
    return render_template('home.html')

# ABOUT
@app.route('/about')
def about():
    return render_template('about.html')

# ALL ARTICLES
@app.route('/articles')
def articles():
    # create cursor for mysql queries
    cur = mysql.connection.cursor()

    # get articles from db
    result = cur.execute("SELECT * FROM articles")

    # get all the data in the form of dictionaries
    articles = cur.fetchall()

    if result > 0:
        return render_template('articles.html', articles = articles)
    else:
        msg = "No articles found"
        return render_template('articles.html', msg = msg)

    # closing the connection
    cur.close()

# SINGLE ARTICLE
@app.route('/articles/<string:id>/')
def article(id):
    # create cursor for mysql queries
    cur = mysql.connection.cursor()

    # get article from db
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    # get all the data in the form of dictionaries
    article = cur.fetchone()
    return render_template('article.html', article=article)

# REGISTER FORM MODEL(CLASS)
class RegisterForm(Form):   
    name = StringField('Name', validators=[validators.length(min=1, max=50)])
    username = StringField('Username', validators=[validators.length(min=4, max=25)])
    email = StringField('Email', validators=[validators.length(min=6, max=50)])
    password = PasswordField('Password', validators=[validators.DataRequired(), validators.EqualTo('confirm', message='Passwords do not match')])
    confirm = PasswordField('Confirm Password')
# creating a model for storing the data. The validors will do the authentification of the data entered

# REGISTER
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    # creating an instance of the model into the form variable
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))
        # with sha256 we encrypt the password

        # create the cursor to execute the mysql commands
        cur = mysql.connection.cursor()

        # execute the mysql query
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

        # commit to DB - save the changes and the added data to the database
        mysql.connection.commit()

        # close the connection
        cur.close()

        flash("You've been registered Successfully", 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)
    # passing the data of the form into the template 

# LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get form fields from the form
        username = request.form['username']
        password_candidate = request.form['password']

        # creating a cursor
        cur = mysql.connection.cursor()

        # get user by username from the database
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        # check the results we get from the database
        if result > 0:
            # get the stored hash password for that username
            data = cur.fetchone()
            password = data['password']

            # compare the passwords entered and that fetched from the database
            if sha256_crypt.verify(password_candidate, password):
                # passed and then creating a session for this user who has been logged in
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in.', 'success')
                return redirect(url_for('dashboard'))
            # if passwords didn't match
            else:
                error = 'Incorrect Password'
                # creating a error variable and storing a string to be displayed on screen
                return render_template('login.html', error=error)
            # closing the connection once the query to the database has been finished
            cur.close()

        # if username didn't match to any of those present in the database
        else:
            error = 'Username not found'
            # creating a error variable and storing a string to be displayed on screen
            return render_template('login.html', error=error)

    return render_template('login.html')

# CHECK IF USER IS LOGGEDIN
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login to continue.', 'danger')
            return redirect(url_for('login'))
    return wrap

# LOGOUT
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

# DASHBOARD
@app.route('/dashboard')
@is_logged_in                   # checking if user is logged in or not. if not rendering login page for them.
def dashboard():
    # create cursor for mysql queries
    cur = mysql.connection.cursor()

    # get articles from db
    result = cur.execute("SELECT * FROM articles")

    # get all the data in the form of dictionaries
    articles = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', articles = articles)
    else:
        msg = "No articles found"
        return render_template('dashboard.html', msg = msg)

    # closing the connection
    cur.close()

# ADD ARTICLES FORM MODEL(CLASS)
class ArticleForm(Form):   
    title = StringField('Title', validators=[validators.length(min=1, max=250)])
    body = TextAreaField('Body', validators=[validators.length(min=30)])

# ADD ARTICLE
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in                   # checking if user is logged in or not. if not rendering login page for them.
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data
        
        # Create Cursor
        cur = mysql.connection.cursor()

        # Execute the query
        cur.execute("INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)", (title, body, session['username'])) 

        # Commit the changes to db
        mysql.connection.commit()

        # Close the connection
        cur.close()

        flash('Article Created', 'success')
        return redirect(url_for('dashboard'))

    return render_template('add_article.html', form=form)

# EDIT ARTICLE
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in                   # checking if user is logged in or not. if not rendering login page for them.
def edit_article(id):
    # create cursor
    cur = mysql.connection.cursor()

    # get the article by id
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()

    # get the form
    form = ArticleForm(request.form)
    
    # Populate article form fields
    form.title.data = article['title']
    form.body.data = article['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']
        
        # Create Cursor
        cur = mysql.connection.cursor()

        # Execute the query
        cur.execute("UPDATE articles SET title=%s, body=%s WHERE id=%s", (title, body, id)) 

        # Commit the changes to db
        mysql.connection.commit()

        # Close the connection
        cur.close()

        flash('Article Updated', 'success')
        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)

# DELETE ARTICLE
@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
    # create a cursor
    cur = mysql.connection.cursor()

    # execute the query
    cur.execute("DELETE FROM articles WHERE id = %s", [id])
    # Commit the changes to db
    mysql.connection.commit()

    # Close the connection
    cur.close()
    flash('Article Deleted', 'success')
    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)         
# with "debug = True" runs the app in debug mode where we don't need to restart the server each time we update 
# the code
