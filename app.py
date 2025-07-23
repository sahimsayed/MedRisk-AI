from flask import Flask, render_template, request, redirect, url_for, flash, make_response
from flask_mysqldb import MySQL
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import MySQLdb.cursors
import json
from xhtml2pdf import pisa
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with your actual secret key

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'medriskai'

mysql = MySQL(app)

# Flask-Login Setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User model
class User(UserMixin):
    def __init__(self, id_, username, email, password):
        self.id = id_
        self.username = username
        self.email = email
        self.password = password

@login_manager.user_loader
def load_user(user_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
    user = cursor.fetchone()
    cursor.close()
    if user:
        return User(user['id'], user['username'], user['email'], user['password'])
    return None

# Routes --------------------------------------------------------

# Public Home Page
@app.route('/')
def home():
    return render_template('index.html')  # Public landing page

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM users WHERE username = %s OR email = %s', (username, email))
        account = cursor.fetchone()

        if account:
            flash('Account with this username or email already exists!', 'danger')
            cursor.close()
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        cursor.execute('INSERT INTO users (username, email, password) VALUES (%s, %s, %s)', (username, email, hashed_password))
        mysql.connection.commit()
        cursor.close()

        flash('You have successfully registered! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_or_email = request.form['username']
        password = request.form['password']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s OR email = %s', (username_or_email, username_or_email))
        user = cursor.fetchone()
        cursor.close()

        if user and check_password_hash(user['password'], password):
            user_obj = User(user['id'], user['username'], user['email'], user['password'])
            login_user(user_obj)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid login credentials.', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT disease, created_at, prediction_result FROM prediction_logs WHERE user_id = %s ORDER BY created_at', (current_user.id,))
    logs = cursor.fetchall()
    cursor.close()
    return render_template('dashboard.html', logs=json.dumps(logs))

def save_prediction(user_id, disease, input_data, result):
    cursor = mysql.connection.cursor()
    cursor.execute(
        'INSERT INTO prediction_logs (user_id, disease, input_data, prediction_result) VALUES (%s, %s, %s, %s)',
        (user_id, disease, json.dumps(input_data), result)
    )
    mysql.connection.commit()
    cursor.close()

@app.route('/predict/<disease>', methods=['GET', 'POST'])
@login_required
def predict(disease):
    if request.method == 'POST':
        input_data = request.form.to_dict()

        # Dummy prediction (replace with ML model logic)
        prediction_result = "Low Risk"

        save_prediction(current_user.id, disease, input_data, prediction_result)

        flash(f'{disease.capitalize()} prediction completed: {prediction_result}', 'success')
        return redirect(url_for('history'))

    return render_template('predict.html', disease=disease)

@app.route('/history')
@login_required
def history():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM prediction_logs WHERE user_id = %s ORDER BY created_at DESC', (current_user.id,))
    logs = cursor.fetchall()
    cursor.close()
    return render_template('history.html', logs=logs)

@app.route('/download_pdf/<int:log_id>')
@login_required
def download_pdf(log_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM prediction_logs WHERE id = %s AND user_id = %s', (log_id, current_user.id))
    log = cursor.fetchone()
    cursor.close()

    if not log:
        flash('Report not found.', 'danger')
        return redirect(url_for('history'))

    html = render_template('pdf_template.html', log=log)
    pdf = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=pdf)

    if pisa_status.err:
        flash('Failed to generate PDF.', 'danger')
        return redirect(url_for('history'))

    response = make_response(pdf.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=report_{log_id}.pdf'
    return response

# Run App
if __name__ == '__main__':
    app.run(debug=True)
