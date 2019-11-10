from flask import Flask,render_template,g,request,session,redirect,url_for
from database import get_db
from werkzeug.security import generate_password_hash, check_password_hash
import os
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
import sqlite3
 # coonect to data base
def connect_db():
    sql = sqlite3.connect('question.db')
    sql.row_factory = sqlite3.Row
    return sql
# get data baset to connect
def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    if hasattr(g,'sqlite_db'):
        g.sqlite_db.close()
# getting current user data with session
def get_current_user():
    user_result = None
    if 'user' in session:
        user = session['user']
        db = get_db()
        user_cur = db.execute('select id, name, password,admin,expert from users where name = ?',[user])
        user_result = user_cur.fetchone()
        return user_result
# home page display question with answer
@app.route('/')
def index():
    user = get_current_user()
    db = get_db()
    question_cur = db.execute('''select 
                                 questions.id as question_id,  
                                 askers.name as asker_name, 
                                 experts.name as expert_name, 
                                 questions.question_text 
                                 from questions 
                                 join users as askers on askers.id = questions.asked_by_id 
                                 join users as experts on experts.id = questions.expert_id 
                                 where questions.answer_text is not null''')
    questions = question_cur.fetchall()
    return render_template('home.html',user = user,questions=questions)

# register the page insert data into data base create user
@app.route('/register',methods =[ 'GET','POST'])
def register():
    user = get_current_user()
    if request.method == 'POST':
        db = get_db()
        existing_user_cur = db.execute('select id from users where name = ?', [request.form['name']])
        existing_user = existing_user_cur.fetchone()
        if existing_user:
            return render_template( 'register.html',user = user,error = 'user already exits!' )

        hashed_password = generate_password_hash(request.form['password'], method = 'sha256')
        db.execute('insert into users (name,password,expert,admin) values(?,?,?,?)',[request.form['name'],hashed_password, '0', '0'])
        db.commit()
        #session['user'] = request.form['user']
        return redirect(url_for('index'))
    return render_template( 'register.html',user = user )

# login page and if user create then enter into website inside
@app.route('/login',methods = ["GET","POST"])
def login():
    error  = None
    user = get_current_user()
    if request.method == 'POST':
        db = get_db()
        name = request.form['name']
        password = request.form['password']
        user_cur = db.execute('select id, name, password from users where name = ?',[name])
        user_result = user_cur.fetchone()
        if user_result:
            if check_password_hash(user_result['password'], password ):
                session['user'] = user_result['name']
                return redirect(url_for('index'))
            else:
                error =  'incorrect password!'
        else:
            error  = 'incorrect username!'

    return render_template('login.html',user = user,error = error)
# retriving the question from database and display.
@app.route('/question/<question_id>')
def question(question_id):
    user = get_current_user()
    db = get_db()
    question_cur = db.execute('''select 
                                 questions.question_text, 
                                 questions.answer_text, 
                                 askers.name as asker_name, 
                                 experts.name as expert_name  
                                 from questions 
                                 join users as askers on askers.id = questions.asked_by_id 
                                 join users as experts on experts.id = questions.expert_id where questions.id = ?''',[question_id])
    question = question_cur.fetchone()
    return render_template('question.html',user = user, question = question)
# retriving the answer data from data base
@app.route('/answer/<question_id>', methods = ['POST','GET'])
def answer(question_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
   # if user['admin'] == 0:
    #    return redirect(url_for('index'))
    db = get_db()

    if request.method == 'POST':
        db.execute('update questions set answer_text = ? where id = ? ',[request.form['answer'], question_id])
        db.commit()
        return redirect(url_for('unanswered'))

    question_cur = db.execute('select id, question_text from questions where id = ?', [question_id])
    question = question_cur .fetchone()
    return render_template('answer.html',user = user,question = question)
# ask question and dispaly in the home page
@app.route('/ask',methods = ['POST','GET'])
def ask():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    db = get_db()
    if request.method == 'POST':
        db.execute('''insert 
                      into questions 
                      (question_text, asked_by_id, expert_id) values(?,?,?)''',
                      [request.form['question'],user['id'],request.form['expert']])
        db.commit()
        redirect(url_for('index'))

    expert_cur = db.execute('select id, name from users where expert = 1')
    expert_results = expert_cur.fetchall()
    return render_template('ask.html',user = user,experts= expert_results)
# display unanswred question into home page
@app.route('/unanswered/')
def unanswered():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    #if user['expert'] == 0:
    #   return redirect(url_for('index'))
    db = get_db()
    question_cur = db.execute('''select 
                                 questions.id, 
                                 questions.question_text, 
                                 users.name from questions 
                                 join users on users.id = questions.asked_by_id 
                                 where questions.answer_text is null and questions.expert_id = ?''', [user['id']])
    questions = question_cur.fetchall()
    return render_template('unanswered.html',user = user,questions = questions)
# users info display in users page
@app.route('/users')
def users():
    user = get_current_user()
    db = get_db()
    if not user:
        return redirect(url_for('login'))
    #if user['admin'] == 0:
     #   return redirect(url_for('index'))

    user_cur = db.execute('select id, name, expert, admin from users')
    users_result = user_cur.fetchall()

    return render_template('users.html',user = user,users= users_result)

@app.route('/promote/<user_id>')
def promote(user_id):
    user = get_current_user()
    db = get_db()
    if not user:
        return redirect(url_for('login'))
    if user['admin'] == 0:
        return redirect(url_for('index'))

    db.execute('update users set expert = 1 where id = ? ',[user_id])
    db.commit()
    return redirect(url_for('users'))
# logout page
@app.route('/logout')
def logout():
    session.pop('user',None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
