#!/usr/bin/env python2.7

"""
Columbia W4111 Intro to databases
Example webserver

To run locally

    python server.py

Go to http://localhost:8111 in your browser


A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response
from flask import Flask, flash, redirect, render_template, request, session, abort


tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)



# XXX: The Database URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@<IP_OF_POSTGRE_SQL_SERVER>/<DB_NAME>
#
# For example, if you had username ewu2493, password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://ewu2493:foobar@<IP_OF_POSTGRE_SQL_SERVER>/postgres"
#
# For your convenience, we already set it to the class database

# Use the DB credentials you received by e-mail
DB_USER = "cx2225"
DB_PASSWORD = "ak7dcl93"

DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"

DATABASEURI = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/w4111"


#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)


# Here we create a test table and insert some values in it
engine.execute("""DROP TABLE IF EXISTS test;""")
engine.execute("""CREATE TABLE IF NOT EXISTS test (
  id serial,
  name text
);""")
engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")



@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request

  The variable g is globally accessible
  """
  try:
    g.conn = engine.connect()
  except:
    print "uh oh, problem connecting to database"
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to e.g., localhost:8111/foobar/ with POST or GET then you could use
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#


@app.route('/')
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """

  # DEBUG: this is debugging code to see what request looks like
  print request.args


  #
  # example of a database query
  #
  cursor = g.conn.execute("SELECT name FROM test")
  names = []
  for result in cursor:
    names.append(result['name'])  # can also be accessed using result[0]
  cursor.close()

  #
  # Flask uses Jinja templates, which is an extension to HTML where you can
  # pass data to a template and dynamically generate HTML based on the data
  # (you can think of it as simple PHP)
  # documentation: https://realpython.com/blog/python/primer-on-jinja-templating/
  #
  # You can see an example template in templates/index.html
  #
  # context are the variables that are passed to the template.
  # for example, "data" key in the context variable defined below will be 
  # accessible as a variable in index.html:
  #
  #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
  #     <div>{{data}}</div>
  #     
  #     # creates a <div> tag for each element in data
  #     # will print: 
  #     #
  #     #   <div>grace hopper</div>
  #     #   <div>alan turing</div>
  #     #   <div>ada lovelace</div>
  #     #
  #     {% for n in data %}
  #     <div>{{n}}</div>
  #     {% endfor %}
  #
  context = dict(data = names)


  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
  return render_template("index.html", **context)

#
# This is an example of a different path.  You can see it at
# 
#     localhost:8111/another
#
# notice that the functio name is another() rather than index()
# the functions for each app.route needs to have different names
#


@app.route('/home')
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return "Hello Boss!  <a href='/logout'>Logout</a>"


@app.route('/login', methods = ['GET','POST'])
def login():
  username = request.form['username']
  password = request.form['password']
  temp=[username, password]
  print(temp)
  # check if u_id and password are correct
  cmd = 'select *  from User1 where u_id = (:name1) and u_password = (:name2)' 
  cursor = g.conn.execute(text(cmd), name1 = username, name2 = password )
  result = [r for r in cursor]

  # if the u_id exists, but enter a wrong password
  cmd2 = 'select *  from User1 where u_id = (:name1) and u_password != (:name2)' 
  cursor_exist = g.conn.execute(text(cmd2), name1 = username, name2 = password)

  result_exist = [r for r in cursor_exist]
  print(result)
  if  len(result) != 0:
    return render_template('facility_search.html')
  elif len(result_exist) != 0:
    content = 'Wrong password, try again'
    return render_template('login2.html')

  else :
    return render_template('signup.html')



@app.route('/signup', methods=['GET', 'POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    display_name = request.form['name']
    
    cmd = 'select u_id from User1 where u_id = (:name1)'
    r = g.conn.execute(text(cmd), name1 = username)
    # if username already exists
    res = [re for re in r]
    if(len(res) != 0):
      return render_template('user_id_error.html')
       
    else:
      cmd = 'insert into User1 (u_name, u_id, u_password) values ( (:name1), (:name2), (:name3) )'
      g.conn.execute(text(cmd), name1 = display_name, name2 = username, name3 = password)
      return render_template('login.html')


@app.route('/restaurant/<id>')
def restaurant(id):
  #cursor = g.conn.execute('SELECT f_id, f_name, f_zip FROM Facility WHERE f_name = \'CREPE EXPRESS\'')
  #cursor = g.conn.execute('SELECT f_id, f_name, f_zip FROM Facility WHERE f_name = \'' + id + '\'')

  # basic info
  cmd_basic = 'SELECT * FROM Facility WHERE f_name = (:name1)'
  cursor_basic = g.conn.execute(text(cmd_basic), name1 = id)
  result_ls1 = []
  for result in cursor_basic:
    res = [result[0], result[1], result[2], result[3], result[4], result[5]] # reuslt[0] is f_id
    result_ls1.append(res)
  cursor_basic.close()

  # violation
  cmd_violation = 'SELECT V.v_description, V.v_code,  V.v_status FROM Facility F LEFT JOIN Inspect I LEFT JOIN Have1 H LEFT JOIN Violation V on H.v_id = V.v_id on H.serial_number = I.serial_number on F.f_id = I.f_id WHERE f_name = (:name1)'
  cursor_violation = g.conn.execute(text(cmd_violation), name1 = id)

  result_ls2 = []
  for result in cursor_violation:
    res = [result[0], result[1], result[2]]
    result_ls2.append(res)
  cursor_violation.close()
  # if there is no violation record
  if len(result_ls2) == 0:
    sentence = [['No violation records yet.']]
    result_ls2 = result_ls2 + sentence
    print result_ls2
  
  
  total_ls = result_ls1 + result_ls2 
  f_id = total_ls[0][0] # f_id 

  # owner
  cmd_owner = 'SELECT O.o_id, O.o_name FROM owner O LEFT JOIN facility_own_owner FO on O.o_id = FO.o_id WHERE FO.f_id = (:name1)';
  cursor_owner = g.conn.execute(text(cmd_owner), name1 = f_id);
  result_ls3 = []
  for result in cursor_owner:
    result_ls3.append(result)
  cursor_owner.close()
  
  # service
  cmd_service = 'select distinct S.s_description FROM service S left join provide_service PS on S.s_id = PS.s_id where PS.f_id = (:name1)';
  cursor_service = g.conn.execute(text(cmd_service), name1 = f_id);
  result_ls4 = []
  for result in cursor_service:
    result_ls4.append(result)
  cursor_service.close()

  # comment
  cmd_comment = 'select User1.u_name, Comment.content from ( (facility inner join Comment_On on facility.f_id = Comment_On.f_id ) inner join Comment ON  Comment_On.u_id =Comment .u_id inner join User1 on User1.u_id =Comment.u_id ) where facility.f_id = (:name1)';
  cursor_comment = g.conn.execute(text(cmd_comment), name1 = f_id);
  result_ls5 = []
  for result in cursor_comment:
    result_ls5.append(result)
    if len(result_ls5) < 1:
      sentence2 = 'No comment records yet.'
      result_ls5.append(sentence2)
  cursor_comment.close()
  
  # employee
  cmd_employee = 'select Employee_Do.e_id from facility inner join Inspect on facility.f_id = Inspect.f_id inner join Inspection ON Inspect.serial_number = Inspection.serial_number inner join Employee_Do ON Inspection.serial_number = Employee_Do.serial_number where facility.f_id = (:name1)';
  cursor_employee = g.conn.execute(text(cmd_employee), name1 = f_id)
  result_ls7 = []
  for result in cursor_employee:
    result_ls7.append(result)
  if len(result_ls7) < 1:
    sentence2 = 'No records yet.'
    result_ls7.append(sentence2)
  cursor_employee.close()

  # Inspection
  cmd_inspection = 'select Inspection.ins_date, Inspection.ins_score,Inspection.ins_grade from facility inner join Inspect on facility.f_id = Inspect.f_id inner join Inspection ON Inspect.serial_number = Inspection.serial_number where facility.f_id = (:name1)'
  cursor_inspection = g.conn.execute(text(cmd_inspection), name1 = f_id)
  result_ls8 = []
  for result in cursor_inspection:
    res = [result[0], result[1], result[2]]
    result_ls8.append(res)
  if len(result_ls8) < 1:
    sentence2 = 'No records yet.'
    result_ls8.append(sentence2)
  cursor_inspection.close()

  total_ls = result_ls1 + result_ls3 + result_ls4 + [result_ls2] + [result_ls5] + result_ls7 + result_ls8
  context = dict(data = total_ls)
  print context
  return render_template("restaurant.html", **context)

# search results
@app.route('/search', methods=['POST'])
def search():
  name = request.form['name']
  name = name.upper()
  pattern = '%'
  name_like = ''.join([pattern, name, pattern])

  cmd = 'Select f_name, f_zip from Facility WHERE f_name LIKE (:name1)';
  cursor = g.conn.execute(text(cmd), name1 = name_like)
  names = []
  #result_ls = []
  for result in cursor:
    #res = [result[0], result[1]]
    #result_ls.append(res)
    names.append(result['f_name'])  # can also be accessed using result[0]
  cursor.close()

  context = dict(data = names)
  # print data
  return render_template("facility_search.html", **context)


@app.route('/sub', methods=['GET', 'POST'])
def submit():
  comment = request.form['comment']
  time = request.form['time']
  u_id = request.form['u_id']
  cmd = 'select u_id from Comment where u_id =  (:name1)'
  
  cursor = g.conn.execute(text(cmd) , name1 = u_id)
  result1 = [r for r in cursor]
  if len(result1) != 0:
    cmd = 'insert into Comment (time, content, u_id) values((:name1), (:name2), (:name3))'
    g.conn.execute(text(cmd),  name1 = time, name2 = comment, name3 = u_id)
    return redirect('/fsearch')
  else :
    return render_template('fail_comment.html') 



@app.route('/signup_page')
def signup():
  return render_template('signup.html')


@app.route('/fsearch')
def another():
  return render_template("facility_search.html")



if __name__ == "__main__":
  app.secret_key = os.urandom(12)
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using

        python server.py

    Show the help text using

        python server.py --help

    """

    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
