import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
from datetime import date

database_path = "./database/data.db"

app = Flask(__name__)
app.secret_key = 'dmcs'  
admin_id = "00000000"

def from_json_filter(value):
    if value:
        return json.loads(value)
    return {}

app.jinja_env.filters['from_json'] = from_json_filter

def get_db():
    conn = sqlite3.connect(database_path)
    conn.row_factory = sqlite3.Row
    return conn


def add_user(user_id,user_name):
    db=get_db()
    db.execute("insert into users(id,password,name) values(?,?,?)",(user_id,user_id,user_name))
    db.commit()
    db.close()

@app.route('/', methods=['GET','POST'])
def serve_main():
    if 'id' in session:
        if session['id'] != admin_id:
            return "may thang nhoc con"
        db = get_db()
        classes_list = db.execute("SELECT * FROM classes ORDER BY started_year DESC, class_name ASC")
        classes_list = classes_list.fetchall()
        db.close()  
        return render_template('index.html', classes_list=classes_list) 
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET','POST'])
def login():
    if 'id' in session:
        return redirect(url_for('serve_main'))
    if request.method == 'POST':
        user_id = request.form.get('id')
        user_password = request.form.get('password')
        db = get_db()
        cursor = db.execute("SELECT id,password FROM users WHERE id = ? AND password = ?", (user_id, user_password))
        result_user = cursor.fetchone()
        db.close()  
        if not result_user:
            flash('Invalid username or password', 'error')  
            return redirect(url_for('login'))
        else:
            session['id'] = user_id
            return redirect(url_for('serve_main'))
    else:
        return render_template('login.html')

@app.route('/logout', methods=['GET'])
def logout():
    session.pop('id', None)
    flash('You have been logged out successfully', 'info')  
    return redirect(url_for('login'))

@app.route('/mkclass', methods=['POST'])
def create_class():
    if 'id' in session and session['id'] == admin_id:
        classes = request.form.get('classes')
        if not classes:
            flash('Please enter class names', 'error')
            return redirect(url_for('serve_main'))
            
        classes = classes.split(' ')
        classes = [cls.strip() for cls in classes if cls.strip()]
        
        db = get_db()
        current_year = date.today().year
        created_count = 0
        duplicate_count = 0
        
        try:
            for class_name in classes:
                existing = db.execute(
                    "SELECT * FROM classes WHERE class_name = ? AND started_year = ?", 
                    (class_name, current_year)
                ).fetchone()
                
                if existing:
                    duplicate_count += 1
                else:
                    db.execute(
                        "INSERT INTO classes(class_name, started_year) VALUES(?,?)", 
                        (class_name, current_year)
                    )
                    created_count += 1
            
            db.commit()
            
            if created_count > 0:
                flash(f'Successfully created {created_count} class(es)', 'success')
            if duplicate_count > 0:
                flash(f'{duplicate_count} class(es) already existed and were skipped', 'warning')
                
        except Exception as e:
            db.rollback()
            flash(f'Error creating classes: {str(e)}', 'error')
        finally:
            db.close()
    else:
        flash('Access denied. Admin privileges required.', 'error')
    
    return redirect(url_for('serve_main'))

@app.route('/viewcl', methods=['GET'])
def view_class():
    if 'id' not in session: 
        return redirect(url_for('login'))
    
    if session['id'] != admin_id: 
        return "may thang nhoc con"
    
    class_name = request.args.get('name')
    class_started_year = request.args.get('year')
    print(class_started_year)
    
    db = get_db()
    try:
        class_exists = db.execute(
            "SELECT * FROM classes WHERE class_name = ? AND started_year = ?",
            (class_name, int(class_started_year))
        ).fetchone()
        
        if not class_exists:
            flash(f'Class "{class_name}" not found', 'error')
            return redirect(url_for('serve_main'))
        
        cursor = db.execute(
            'SELECT * FROM student_to_classes WHERE class_name=? AND started_year=?',
            (class_name, int(class_started_year))  
        )
        student_list = cursor.fetchall()
        
        return render_template("class_view.html", 
                             student_list=student_list,  
                             class_name=class_name,      
                             year=class_started_year)    
        
    except Exception as e:
        flash(f'Error loading class: {str(e)}', 'error')
        return redirect(url_for('serve_main'))
    finally:
        db.close() 


@app.route('/addstudent',methods=['POST'])
def add_student():
    if not session['id']:
        return redirect(url_for('login'))
    if(session['id'] != admin_id):
        return 'may thang nhoc con'
    class_name = request.args.get('name')
    class_started_year = request.args.get('year')
    student_array=request.json['student_array']
    db=get_db()
    for student in student_array:
        user_exist=db.execute("select * from users where id=? and name=?",(student['id'],student['name'])).fetchone()
        if not user_exist:
            db.execute("insert into users(id,password,name) values(?,?,?)",(student['id'],student['id'],student['name']))
        db.execute("insert into student_to_classes(id,student_name,class_name,started_year) values(?,?,?,?)",(student['id'],student['name'],class_name,class_started_year))
    db.commit()
    db.close()    
    return redirect(url_for("view_class")+f"?name={class_name}&year={class_started_year}")


@app.route("/updatestudent",methods=['POST'])
def update_student():
    if not session['id']:
        return redirect((url_for('login')))
    if session['id'] != admin_id:
        return 'may thang nhoc con'
    class_name = request.args.get('name')
    class_started_year = request.args.get('year')
    student_list=request.json['student_list']
    db=get_db()
    for student in student_list:
        student_exist=db.execute("select id from student_to_classes where id=? and class_name=?",(student['id'],student['class_name']))
        if student_exist:
            db.execute(
                """
                update student_to_classes
                set grade=?
                where id=? and class_name=?
                """,
                (json.dumps(student['grade']),student['id'],student['class_name']) 
            )
    db.commit()
    db.close()
    return redirect(url_for("view_class")+f"?name={class_name}&year={class_started_year}")


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)