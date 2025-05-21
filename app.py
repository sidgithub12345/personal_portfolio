from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import os
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'SidProfile'

UPLOAD_FOLDER = 'static/uploads/resumes'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'portfolio_db'

mysql = MySQL(app)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/home')
def home():
    if 'loggedin' in session and session.get('role') == 'user':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        cursor.execute('SELECT hero_title, hero_paragraph FROM hero_section WHERE id = 1')
        hero_data = cursor.fetchone()

        cursor.execute('SELECT about_paragraph, about_skills FROM about_section WHERE id = 1')
        about_data = cursor.fetchone()

        cursor.execute('SELECT * FROM projects')
        projects = cursor.fetchall()

        cursor.execute('SELECT * FROM testimonials')
        testimonials = cursor.fetchall()

        skills = about_data['about_skills'].split(',') if about_data and about_data['about_skills'] else []

        return render_template('home.html',
                               hero_title=hero_data['hero_title'],
                               hero_paragraph=hero_data['hero_paragraph'],
                               about_paragraph=about_data['about_paragraph'],
                               about_skills=skills,
                               projects=projects,
                               testimonials=testimonials)
    flash('Access denied!', 'danger')
    return redirect(url_for('login'))



@app.route('/admin/dashboard')
def admin_dashboard():
    if 'loggedin' in session and session.get('role') == 'admin':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        cursor.execute('SELECT hero_title, hero_paragraph FROM hero_section WHERE id = 1')
        hero_data = cursor.fetchone()

        cursor.execute('SELECT about_paragraph, about_skills FROM about_section WHERE id = 1')
        about_data = cursor.fetchone()

        cursor.execute('SELECT * FROM projects')
        projects = cursor.fetchall()

        cursor.execute("SELECT * FROM resume_section ORDER BY upload_date DESC LIMIT 1")
        resume_info = cursor.fetchone()

        cursor.close()

        return render_template('admin_dashboard.html',
                               hero_title=hero_data['hero_title'],
                               hero_paragraph=hero_data['hero_paragraph'],
                               about_paragraph=about_data['about_paragraph'],
                               about_skills=about_data['about_skills'],
                               projects = projects,
                               resume_info=resume_info)
    flash('Access denied!', 'danger')
    return redirect(url_for('login'))


@app.route('/admin/update-hero', methods=['POST'])
def update_hero():
    if 'loggedin' in session and session.get('role') == 'admin':
        title = request.form['hero_title']
        paragraph = request.form['hero_paragraph']

        cursor = mysql.connection.cursor()
        cursor.execute('UPDATE hero_section SET hero_title = %s, hero_paragraph = %s WHERE id = 1',
                       (title, paragraph))
        mysql.connection.commit()

        flash('Hero section updated successfully!', 'hero')
        return redirect(url_for('admin_dashboard'))
    flash('Access denied!', 'danger')
    return redirect(url_for('login'))

@app.route('/admin/update-about', methods=['POST'])
def update_about():
    if 'loggedin' in session and session.get('role') == 'admin':
        paragraph = request.form['about_paragraph']
        skills = request.form['about_skills']

        cursor = mysql.connection.cursor()
        cursor.execute('UPDATE about_section SET about_paragraph = %s, about_skills = %s WHERE id = 1',
                       (paragraph, skills))
        mysql.connection.commit()

        flash('About section updated successfully!', 'about')
        return redirect(url_for('admin_dashboard'))
    flash('Access denied!', 'danger')
    return redirect(url_for('login'))

@app.route('/admin/add-project', methods=['POST'])
def add_project():
    if 'loggedin' in session and session.get('role') == 'admin':
        title = request.form['title']
        description = request.form['description']
        image_filename = request.form['image_filename']
        github_link = request.form['github_link']

        cursor = mysql.connection.cursor()
        cursor.execute(
            'INSERT INTO projects (title, description, image_filename, github_link) VALUES (%s, %s, %s, %s)',
            (title, description, image_filename, github_link)
        )
        mysql.connection.commit()

        flash("Project added successfully.", "project")
        return redirect(url_for('admin_dashboard'))
    flash('Access denied!', 'danger')
    return redirect(url_for('login'))


@app.route('/admin/update-project', methods=['POST'])
def update_project():
    if 'loggedin' in session and session.get('role') == 'admin':
        project_id = request.form['project_id']
        title = request.form['title']
        description = request.form['description']
        image_filename = request.form['image_filename']
        github_link = request.form['github_link']

        cursor = mysql.connection.cursor()
        cursor.execute(
            'UPDATE projects SET title = %s, description = %s, image_filename = %s, github_link = %s WHERE id = %s',
            (title, description, image_filename, github_link, project_id)
        )
        mysql.connection.commit()

        flash("Project updated successfully.", "project")
        return redirect(url_for('admin_dashboard'))
    flash('Access denied!', 'danger')
    return redirect(url_for('login'))

@app.route('/admin/update-resume', methods=['POST'])
def update_resume():
    if 'loggedin' in session and session.get('role') == 'admin':
        if 'resume_file' not in request.files:
            flash('No file part', 'resume')
            return redirect(url_for('admin_dashboard'))

        file = request.files['resume_file']
        if file.filename == '':
            flash('No selected file', 'resume')
            return redirect(url_for('admin_dashboard'))

        if file and allowed_file(file.filename):
            filename = secure_filename("resume.pdf")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            cursor = mysql.connection.cursor()
            cursor.execute("""
                INSERT INTO resume_section (filename, uploaded_by)
                VALUES (%s, %s)
            """, (filename, session['username']))
            mysql.connection.commit()
            cursor.close()

            flash('Resume updated successfully!', 'resume')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid file format. Only PDF allowed.', 'resume')
            return redirect(url_for('admin_dashboard'))
    flash('Access denied!', 'danger')
    return redirect(url_for('login'))

@app.route('/admin/add-testimonial', methods=['POST'])
def add_testimonial():
    if 'loggedin' in session and session.get('role') == 'admin':
        name = request.form['name']
        message = request.form['message']
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO testimonials (name, message) VALUES (%s, %s)", (name, message))
        mysql.connection.commit()
        cursor.close()
        flash('Testimonial added successfully.', 'success')
        return redirect(url_for('admin_dashboard'))
    flash('Access denied!', 'danger')
    return redirect(url_for('login'))

@app.route('/admin/update-testimonial', methods=['POST'])
def update_testimonial():
    if 'loggedin' in session and session.get('role') == 'admin':
        tid = request.form['id']
        name = request.form['name']
        message = request.form['message']
        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE testimonials SET name = %s, message = %s WHERE id = %s", (name, message, tid))
        mysql.connection.commit()
        cursor.close()
        flash('Testimonial updated.', 'success')
        return redirect(url_for('admin_dashboard'))
    flash('Access denied!', 'danger')
    return redirect(url_for('login'))

@app.route('/admin/delete-testimonial/<int:testimonial_id>')
def delete_testimonial(testimonial_id):
    if 'loggedin' in session and session.get('role') == 'admin':
        cursor = mysql.connection.cursor()
        cursor.execute("DELETE FROM testimonials WHERE id = %s", (testimonial_id,))
        mysql.connection.commit()
        cursor.close()
        flash('Testimonial deleted.', 'success')
        return redirect(url_for('admin_dashboard'))
    flash('Access denied!', 'danger')
    return redirect(url_for('login'))



@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']

        if username == 'admin' and password == 'admin123':
            session['loggedin'] = True
            session['username'] = 'admin'
            session['role'] = 'admin'
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin_dashboard'))

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        account = cursor.fetchone()

        if not account:
            flash('User not registered. Please register first!', 'warning')
            return redirect(url_for('register'))
        elif account['password'] != password:
            msg = 'Incorrect password!'
        else:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            session['email'] = account['email']
            session['role'] = account['role']
            flash('You have successfully logged in!', 'success')
            return redirect(url_for('home'))

    return render_template('login.html', msg=msg)

@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'email' in request.form and 'password' in request.form:
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        account = cursor.fetchone()

        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only letters and numbers!'
        else:
            cursor.execute('INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, %s)',
                           (username, email, password, 'user'))
            mysql.connection.commit()
            flash('You have successfully registered!', 'success')
            return redirect(url_for('login'))

    return render_template('register.html', msg=msg)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out!', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)
