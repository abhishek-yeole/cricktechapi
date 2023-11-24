from email.message import EmailMessage
from flask import Flask, request, jsonify, render_template
import random
import string
from flask_cors import CORS
import smtplib
import bcrypt
import mysql.connector

app = Flask(__name__)
CORS(app)

mysql = mysql.connector.connect(
    host= os.environ.get('MYSQL_HOST_NAME'),
    user= os.environ.get('MYSQL_USER_DATABASE'),
    password= os.environ.get('MYSQL_PASSWORD'),
    database= os.environ.get('MYSQL_USER_DATABASE'),
    port=3306
)

@app.route('/feedback', methods=['POST', 'GET'])
def feedback():
    if request.method == 'POST':
        data = request.get_json()

        cursor = mysql.cursor(dictionary=True)
        cursor.execute("INSERT INTO `feedbacks`(`email`, `feedback`) VALUES (%s, %s)",
                       (data.get('email'), data.get('feedback'),))
        mysql.commit()
        cursor.close()

        return jsonify({'success': True})

    if request.method == 'GET':
        cursor = mysql.cursor(dictionary=True)
        cursor.execute("SELECT * FROM `feedbacks`")
        feedback_data = cursor.fetchall()
        mysql.commit()
        cursor.close()

        return jsonify({'success': True, 'data': feedback_data})


@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        cursor = mysql.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (data.get('email'),))
        user = cursor.fetchone()
        mysql.commit()
        cursor.close()

        if user:
            error = 'Email address already in use. Please use a different email address.'
            return jsonify({'success': False, 'message': error})
        else:
            msg = EmailMessage()

            # alphabet = string.ascii_letters + string.digits
            otp = random.randint(100000, 999999)
            print(otp)

            cursor = mysql.cursor(dictionary=True)
            cursor.execute("INSERT INTO `otp`(`mail`, `otp`) VALUES (%s, %s)", (data.get('email'), otp,))
            mysql.commit()
            cursor.close()

            msg["Subject"] = "CrickTech Verification"
            msg["From"] = "storycircle123@gmail.com"
            msg["To"] = data.get('email')

            html_content = render_template('email.html', name=data.get('name'), otp=otp)
            msg.set_content(html_content, subtype='html')

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login('storycircle123@gmail.com', os.environ.get('GMAIL_APP_PASSWORD'))
                smtp.send_message(msg)

            return jsonify({'success': True})


@app.route('/verify', methods=['POST', 'GET'])
def verify():
    if request.method == 'POST':
        data = request.get_json()
        cursor = mysql.cursor(dictionary=True)
        cursor.execute("SELECT `otp` FROM `otp` WHERE `mail`=%s ORDER BY `id` DESC LIMIT 1", (data.get('email'),))
        system_otp = cursor.fetchone()
        mysql.commit()
        cursor.close()

        if system_otp['otp'] == data.get('otp'):
            cursor = mysql.cursor(dictionary=True)
            password = data.get('password').encode('utf-8')
            hash_password = bcrypt.hashpw(password, bcrypt.gensalt())
            cursor.execute("INSERT INTO `users` (`name`, `email`, `password`) VALUES (%s, %s, %s)",
                           (data.get('name'), data.get('email'), hash_password,))
            mysql.commit()
            cursor.close()
            return jsonify({'success': True})
        else:
            return jsonify({'success': False})


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('username')
        password = data.get('password').encode('utf-8')

        cursor = mysql.cursor(dictionary=True)
        cursor.execute("SELECT * FROM `users` WHERE email=%s", (email,))
        user = cursor.fetchone()
        mysql.commit()
        cursor.close()

        if user:
            if bcrypt.hashpw(password, user['password'].encode('utf-8')) == user['password'].encode('utf-8'):
                cursor = mysql.cursor(dictionary=True)
                cursor.execute("INSERT INTO `session`(`id`, `name`, `email`) VALUES (%s, %s, %s)",
                               (user['id'], user['name'], user['email'],))
                mysql.commit()
                cursor.close()

                return jsonify({'login': True, 'message': 'Valid User Login', 'id': user['id'],
                                'name': user['name'], 'email': user['email']})

            else:
                return jsonify({'login': False, 'message': 'Invalid Password'})
        else:
            return jsonify({'login': False})


@app.route('/logincheck', methods=['POST'])
def checklogin():
    # print(session)
    data = request.get_json()
    print(data)

    if data.get('email') == 'Meow':
        return jsonify({'login': False})

    cursor = mysql.cursor(dictionary=True)
    cursor.execute("SELECT `id`, `name`, `email` FROM `session` WHERE `email`= %s ORDER BY `index` DESC LIMIT 1;",
                   (data.get('email'),))
    user = cursor.fetchone()
    cursor.close()

    if user:
        return jsonify({'login': True, 'message': 'Valid User Login', 'id': user['id'],
                        'name': user['name'], 'email': user['email']})

    else:
        return jsonify({'login': False})


@app.route('/forgot', methods=['POST'])
def forgot():
    if request.method == 'POST':
        data = request.get_json()
        print(data)
        cursor = mysql.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (data.get('username'),))
        user = cursor.fetchone()
        mysql.commit()

        if user:
            msg = EmailMessage()

            otp = random.randint(100000, 999999)

            cursor = mysql.cursor(dictionary=True)
            cursor.execute("INSERT INTO `otp`(`mail`, `otp`) VALUES (%s, %s)", (data.get('username'), otp,))
            mysql.commit()
            cursor.close()

            msg["Subject"] = "CrickTech Verification"
            msg["From"] = "storycircle123@gmail.com"
            msg["To"] = data.get('username')

            html_content = render_template('pass.html', name=user['name'], otp=otp)
            msg.set_content(html_content, subtype='html')

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login('storycircle123@gmail.com', os.environ.get('GMAIL_APP_PASSWORD'))
                smtp.send_message(msg)

            return jsonify({'success': True})
        else:
            error = 'No such User found. Please Register first.'
            return jsonify(error)


@app.route('/verifyforgot', methods=['POST'])
def verifyforgot():
    if request.method == 'POST':
        data = request.get_json()
        print(data)
        cursor = mysql.cursor(dictionary=True)
        cursor.execute("SELECT `otp` FROM `otp` WHERE `mail`=%s ORDER BY `id` DESC LIMIT 1;", (data.get('username'),))
        system_otp = cursor.fetchone()
        print(system_otp['otp'])
        mysql.commit()
        cursor.close()

        if str(system_otp['otp']) == data.get('otp'):
            return jsonify({'success': True})
        else:
            return jsonify({'success': False})


@app.route('/reset', methods=['POST'])
def reset():
    if request.method == 'POST':
        data = request.get_json()
        password = data.get('password').encode('utf-8')
        hash_password = bcrypt.hashpw(password, bcrypt.gensalt())
        cursor = mysql.cursor(dictionary=True)
        cursor.execute("UPDATE `users` SET `password`= %s WHERE `email`= %s", (hash_password, data.get('username'),))
        mysql.commit()
        cursor.close()
        return jsonify({'success': True})


@app.route('/logout', methods=['POST'])
def logout():
    data = request.get_json()
    cursor = mysql.cursor(dictionary=True)
    cursor.execute("DELETE FROM `session` WHERE `email` = %s ;", (data.get('email'),))
    mysql.commit()
    cursor.close()
    return jsonify({'logout': True})
