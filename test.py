import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
from datetime import date

database_path = "./database/data.db"

def get_db():
    conn = sqlite3.connect(database_path)
    conn.row_factory = sqlite3.Row
    return conn

class_name="10a3"
class_started_year=2025
db=get_db()
grade_sample=db.execute("select grade from student_to_classes where class_name=? and started_year=?",(class_name,int(class_started_year))).fetchone()
if grade_sample:
	grade_sample=json.loads(grade_sample['grade'])
else:
	grade_sample={}
grades_column_relation={}
group_leader_col=db.execute("select col_list from group_leader_col where class_name=? and started_year=?",(class_name,class_started_year)).fetchone()
if group_leader_col:
	group_leader_col=json.loads(group_leader_col['col_list'])
	group_leader_col=group_leader_col['list']
else:
	group_leader_col=[]

col_weight=db.execute("select col_weight from column_weight where class_name=? and started_year=?",(class_name,int(class_started_year))).fetchone()
if col_weight:
	col_weight=json.loads(col_weight['col_weight'])
for key in grade_sample:
	bonus_to=db.execute("select to_col from bonus_point_relation where from_col=?",(key,)).fetchall()
	if bonus_to:
		bonus_to=[score['to_col'] for score in bonus_to]
	else:
		bonus_to=[]
	grades_column_relation[key]={'bonus_to':bonus_to}
	grades_column_relation[key]['is_group_leader_col']=True if key in group_leader_col else False 
	print(col_weight[key] if key in col_weight else 0)
	grades_column_relation[key]['col_weight']=float(col_weight[key]) if key in col_weight else 0
print(grades_column_relation)
db.close()

for i in []:
	print('halu')

