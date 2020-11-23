from flask import Flask,Markup #importing markup to wrap html content in it and then pass to flash meassgae
from flask import render_template,url_for,request,session,redirect,flash
from flask_mysqldb import MySQL 
import MySQLdb.cursors 
from datetime import datetime,date

app = Flask(__name__)
app.config['SECRET_KEY']='SECREt'
#configure app to connect to MYSQL DB
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'admin_1820'
app.config['MYSQL_DB'] = 'lms'
app.config['MYSQL_HOST'] = 'localhost'
mysql = MySQL(app) #creating db instance

#index page of the web app
@app.route('/',methods=['GET','POST'])
def home():
	return render_template("home.html")

#User Login Route
@app.route('/login',methods=['GET','POST'])
def login():
	if request.method=="POST":
		name=request.form['username'] 
		pwd=request.form['password']
		#checking for empty fields
		if name=="":
			flash("Login Unsucessful! Username can't be empty",'danger')
			return redirect(url_for('login'))
		elif pwd=="":
			flash("Login Unsucessful! password can't be empty",'danger')
			return redirect(url_for('login'))
		cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

		cursor.execute("select * from user where username=%s and password=%s",(name,pwd))
		data = cursor.fetchone()
		#if user found in db set session keys and redirect to dashboard page
		if data:
			session['loggedin']=True
			session['username']=data["username"]
			flash("Logged in Successfully",'success')
			return redirect(url_for('dashboard'))
		else:
			flash("Login Unsucessful",'danger')
	return render_template("login.html")	

#User Sign Up
@app.route('/register',methods=['GET','POST'])
def register():
	try:
		if request.method=="POST":
			name=request.form['username']
			pwd=request.form['password']
			if name=="":
				flash("Registration Unsucessful! Username can't be empty",'danger')
				return redirect(url_for('register'))
			elif pwd=="":
				flash("Registration Unsucessful! password can't be empty",'danger')
				return redirect(url_for('register'))
			cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
			#check if username is already in use
			cursor.execute("select * from user where username=%s",[name])
			data = cursor.fetchone()
			if data:
				flash('Username Already Exists.Choose Another and try again','danger')
				return redirect(url_for('register'))
			else:
				#if everything went right then insert user in db and redirect to login	
				cursor.execute("insert into user values(%s,%s)",(name,pwd))
				mysql.connection.commit()
				flash("Registered Successfully",'success')
				return redirect(url_for('login'))
	except:
		flash("SignUp Unsucessful",'danger')
		return redirect(url_for('register'))
	return render_template("register.html")	

#Admin Dashboard
@app.route('/dashboard',methods=["GET","POST"])
def dashboard():
	return render_template('dashboard.html')

#Inserting a New Book in DB
@app.route('/add_book',methods=["GET","POST"])
def add_book():
	if request.method=="POST":
		try:
			bookid=request.form['bookid']
			bookname=request.form['bookname']
			authorname=request.form['authorname']
			availability=request.form['availability']
			description=request.form['description']
			if bookid=="" or bookname=="" or authorname=="" or availability=="" or description=="":
				flash("One or more fields left empty! All fields are compulsory.Fill all fields and Try Again!",'danger')
				return redirect('add_book')
			cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
			cursor.execute("select * from books where book_id=%s",[bookid])
			data = cursor.fetchone()
			if data:
				flash('Bookid already exists','danger')		
			else:
				cursor.execute("insert into books values(%s,%s,%s,NULL,%s,NULL,NULL,%s)",(bookid,bookname,authorname,availability,description))
				mysql.connection.commit()
				flash('Book Added Successfully!','success')			
		except:
			flash('Oops! Something went wrong..Couldn\'t add new book','danger')
		
	return render_template('add.html')

#Updating Book Details in DB
@app.route('/update_book<bookid>',methods=["GET","POST"])
def update_book(bookid):
	cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
	cursor.execute("select * from books where book_id=%s",[bookid])
	data=cursor.fetchone()
	try:
		if request.method=="POST":
			bookname=request.form['bookname']
			authorname=request.form['authorname']
			cursor.execute('update books set book_name=%s,author_name=%s where book_id=%s',(bookname,authorname,bookid))
			mysql.connection.commit()
			flash('Book Updated Successfully','success')
			return redirect(url_for('view_book'))
	except:
		flash('Oops something went wrong..Try Again Later!!!','danger')	
				
	
	return render_template("update.html",data=data)

#Deleting Book from DB
@app.route('/delete_book<bookid>',methods=["GET","POST"])
def delete_book(bookid):
	try:
		cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
		cursor.execute("delete from books where book_id=%s",[bookid])
		mysql.connection.commit()
		flash('Book Deleted Successfully','success')
	except:
		flash('Oops something went wrong..Try Again Later!!!','danger')
	return redirect(url_for('view_book'))	

#Viewing All the Books present from DB
@app.route('/view_book',methods=["GET","POST"])
def view_book():
	cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
	#fetching all books from database
	cursor.execute("select * from books")
	data=cursor.fetchall()
	return render_template("view.html",data=data)

#Displaying List of all books available to issue
@app.route('/issue_book',methods=["GET","POST"])
def issue_book():
	cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
	#fetching all non-issued books
	cursor.execute("select * from books where availability=%s",['available'])
	data=cursor.fetchall()
	return render_template('issue.html',data=data)

#validate user entered return date format is yyyy-mm-dd
def validate(return_date,bookid):
    try:
        datetime.strptime(return_date, '%Y-%m-%d')
    except:
        flash("Incorrect data format, should be YYYY-MM-DD",'danger')
        return redirect(url_for('issue_books',bookid=bookid))

#Issuing a book and updating its details in Db
@app.route('/issue_books',methods=["GET","POST"])
def issue_books():
	bookid=request.args.get("bookid")#acessing book id parameter from url
	try:		
		if request.method=="POST":
			issued_to=request.form['issued_to']
			return_date=request.form['return_date']
			if issued_to=="" or return_date=="": #checks if fields are left empty
				flash("One or more fields left empty! All fields are compulsory.Fill all fields and Try Again!",'danger')
				return redirect(url_for('issue_books',bookid=bookid))
			validate(return_date,bookid) #validating return date format
			issue_date = datetime.now().strftime('%Y-%m-%d')
			if(return_date<=issue_date): #checking if return date is less than todays date
				flash('Return Date must be atleast 7 days ahead of Issue Date','danger')
				return redirect(url_for('issue_books',bookid=bookid))
			cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)#if everything is right update book status to issued
			cursor.execute("update books set issued_to=%s,issue_date=%s,return_date=%s,availability='issued' where book_id=%s",(issued_to,issue_date,return_date,bookid))
			mysql.connection.commit()
			flash('Book Issued Successfully','success')
			return redirect(url_for('issue_book'))
	except:
			flash('Oops something went wrong..Try Again Later!!!','danger')	
			return redirect(url_for('issue_books',bookid=bookid))	
	return render_template("issueform.html",bookid=bookid)

#Displaying List of all issued books 
@app.route('/return_book',methods=["GET","POST"])
def return_book():
	cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
	#fetching all book whose status is issued
	cursor.execute("select * from books where availability=%s",['issued'])
	data=cursor.fetchall()
	return render_template('return.html',data=data)	

#Calculating fine to return book
@app.route('/return_books<bookid>',methods=["GET","POST"])
def return_books(bookid):
	fine=0
	cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
	cursor.execute("select * from books where book_id=%s",(bookid))
	data=cursor.fetchone()
	return_date=data["return_date"]#fetching return date from database which is in date format
	actual_return_date=date.today()#fetching todays date
	if actual_return_date<=return_date:#comparing actual return date and due return date
		fine=0 #if book return on or before return day then fine is 0
	else:
		day_overdue=(actual_return_date-return_date).days #no of days between return date and actual return date
		if day_overdue>=1 and day_overdue<=5: #if no of days lie in [1,5]
			fine=day_overdue*1
		elif day_overdue>=6 and day_overdue<=10: #if no of days lie in [6,10]
			fine=day_overdue*2
		elif day_overdue>10: #if no of days>10
			fine=day_overdue*5				
	return render_template("returnform.html",fine=fine,data=data)

#if no fine just changing book status to available in db
@app.route('/return_without_fine',methods=["GET","POST"])
def return_without_fine():
	bookid=request.args.get("bookid")#accessing bookid query parameter
	try:
		if request.method:
			cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
			cursor.execute("select * from books where book_id=%s",(bookid))
			data=cursor.fetchone()
			#setting data and cost keys in session to data to send it for invoice generation
			session['data']=data
			session['cost']={'fine':0,'change_due':0,'amt_paid':0,'date_today':date.today()}
			cursor.execute("update books set availability='available',issued_to=NULL,issue_date=NULL,return_date=NULL where book_id=%s",[bookid])
			mysql.connection.commit()
			#display invoice button in flash message
			msg=Markup("<a href='make_bill' style='background-color:white;color:green;padding:2px 15px;border-radius:12px;'>Generate Invoice</a></button")
			flash('Book Returned Successfully... '+msg,'success')
	except:
		flash('Oops! Something went wrong.. ','danger')
	return redirect(url_for('return_book'))

#making fine payment and changing book status to available in db
@app.route('/pay_fine',methods=["GET","POST"])
def pay_fine():
	bookid=request.args.get("bookid")#accessing bookid query parameter
	fine=request.args.get("fine")#accessing fine query parameter
	try:
		if request.method=="POST":
			amt_paid=request.form['paid']
			change=request.form['change_due']
			#checking if amt_paid is left empty or not
			if amt_paid=="":
				flash("Payement Unsucessful! Payement Received can't be empty",'danger')
				return redirect(url_for('pay_fine',bookid=bookid,fine=fine))
			cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
			cursor.execute("select * from books where book_id=%s",(bookid))
			data=cursor.fetchone()
			#setting data and cost keys in session to data to send it for invoice generation
			session['data']=data
			session['cost']={'fine':fine,'change_due':change,'amt_paid':amt_paid,'date_today':date.today()}
			cursor.execute("update books set availability='available',issued_to=NULL,issue_date=NULL,return_date=NULL where book_id=%s",[bookid])
			mysql.connection.commit()
			#displaying make bill button in flash message
			msg=Markup("<a href='make_bill' target='_blank' style='background-color:white;color:green;padding:1px 15px;border-radius:12px;'>Generate Invoice</a>")
			flash('Payment Successful! Book Returned Successfully... '+msg,'success')
	except:
		flash('Oops! Something went wrong.. ','danger')
	return render_template('payment.html',fine=fine)	

@app.template_filter('datetime')#adding a filter to jinja to format date
def jinja_date_filter(date): 
	date=datetime.strptime(date,'%a, %d %b %Y %H:%M:%S GMT')
	return datetime.strftime(date,'%d-%m-%Y')

#generating invoice
@app.route('/make_bill',methods=["GET","POST"])
def make_bill():
	data=session['data']#accessing data key from session
	cost=session['cost']#accessing cost key from session
	
	print(data,cost)
	return render_template('invoice.html',cost=cost,data=data)

#Logout route
@app.route('/logout')
def logout():
	#popping all keys from the session
	for key in session.keys():
		session.pop(key)
	session.clear()	#clearing session
	return redirect(url_for('home'))


if __name__ == '__main__':
 	app.run(debug=True)
