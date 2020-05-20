from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mail import Mail, Message
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
from itsdangerous import URLSafeTimedSerializer
from helpfunctions import *
import numpy as np
import string, random

app = Flask(__name__)
app.secret_key = "iel18siker"
app.permanent_session_lifetime = timedelta(days=1)

app.config.update(dict(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = 465,
    MAIL_USE_TLS = False,
    MAIL_USE_SSL = True,
    MAIL_USERNAME = 'bugunneyapsam.authenticate@gmail.com',
    MAIL_PASSWORD = 'iel18sikererenege',
))

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
app.config['SQLALCHEMY_BINDS'] = {
	'users': 'sqlite:///users.db'
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
ADMIN_PASSWORD = "iel18siker"

mail = Mail(app)
s = URLSafeTimedSerializer("iel18fenasiker")
db = SQLAlchemy(app)

class Post(db.Model):
	_id = db.Column("id", db.Integer, primary_key=True)
	text = db.Column("text", db.String())
	category = db.Column("category", db.String())
	ups = db.Column("ups", db.Integer)
	downs = db.Column("downs", db.Integer)
	points = db.Column("points", db.Integer)

	def __init__(self, text, category):
		self.text = text
		self.category = category
		self.ups = 0
		self.downs = 0
		self.points = 0

class User(db.Model):
	__bind_key__ = 'users'
	_id = db.Column("id", db.Integer, primary_key=True)
	name = db.Column("name", db.String(100))
	email = db.Column("email", db.String(100))
	password = db.Column("password", db.String())
	categories = db.Column("categories", db.String())
	authenticated = db.Column("authenticated", db.Boolean())
	ups = db.Column("ups", db.String())
	downs = db.Column("downs", db.String())

	def __init__(self, name, email, password, categories):
		self.name = name
		self.email = email
		self.password = password
		self.categories = categories
		self.authenticated = False
		self.ups = ""
		self.downs = ""

	

@app.route("/", methods=["POST", "GET"])
@app.route("/home", methods=["POST", "GET"])
def home():
	if request.method == "POST":
		return get_home_requests()
	else:
		session.permanent = True
		if "order" not in session:
			session["order"] = "points"
		content = get_posts(by = session["order"])
		length = len(content)
		if 'user' in session:
			return render_template("index_usr.html", content = content, length = length, categories = CATS)
		return render_template("index.html", content = content, length = length, categories = CATS)

@app.route("/<category>", methods=["POST", "GET"])
def show_category(category):
	if request.method == "POST":
		return get_home_requests()
	else:
		session.permanent = True
		if "order" not in session:
			session["order"] = "points"
		content = get_posts(category = category, by = session["order"])
		length = len(content)
		if 'user' in session:
			return render_template("index_usr.html", content = content, length = length, categories = CATS)
		return render_template("index.html", content = content, length = length, categories = CATS)

@app.route("/post:<post_id>", methods=["POST", "GET"])
def show_post(post_id):
	if request.method == "POST":
		return get_home_requests()
	else:
		content = db.session.query(Post).filter_by(_id = post_id).first()
		if 'user' in session:
			return render_template("post_usr.html", content = content)
		return render_template("post.html", content = content)


@app.route("/view")
def view():
	# Tum kullanicilarin bilgilerini gösterir
	if "user" in session.keys():
		if session["user"] == "admin":
			return render_template("view.html", values=User.query.all())
	#return render_template("view.html", values=User.query.all())
	return redirect(url_for("home"))

@app.route("/register", methods=["POST", "GET"])
def register():
	categories = CATS

	if request.method == "POST":

		name = request.form['name']
		email = request.form['email']
		
		found_user = User.query.filter_by(name=name).first()
		found_email = User.query.filter_by(email=email).first()
		if found_user:
			if name == found_user.name:
				flash("Bu kullanıcı adı zaten alınmış :( Lütfen başka bir kullanıcı adıyla tekrar dene!", "info")
				return redirect(url_for("register"))
		if found_email:
			if email == found_email.email:
				flash("Bu eposta zaten kullanılıyor.", "info")
				return redirect(url_for("register"))
		
		cat_ids = request.form.getlist("cat_list")
		pw = request.form["pass"]
		new_user = User(request.form['name'], request.form['email'], pw, encodeToString(cat_ids))
		db.session.add(new_user)
		db.session.commit()
		# Authenticate
		email = new_user.email
		send_email(email)
		flash("Başarıyla kaydoldunuz şimdi lütfen hesabınızı aktive ediniz!")
		return redirect(url_for("home"))
	else:
		if "user" in session:
			flash("Zaten giriş yaptınız!")
			return redirect(url_for("home"))
		else:
			return render_template("register.html", categories=categories)

@app.route("/login", methods=["POST", "GET"])
def login():
	if request.method == "POST":
		if 'passreset' in request.form:
			return redirect(url_for("forget"))
		session.permanent = True
		username = request.form["name"]
		password = request.form["pass"]
		found_user = User.query.filter_by(name=username).first()
		if found_user:
			psw = found_user.password
			if password == psw:
				if found_user.authenticated == False:
					flash("Lütfen e-postanıza gelen link ile profilinizi aktive ediniz!")
					return redirect(url_for("authenticate"))
				session["user"] = found_user.name
				session["email"] = found_user.email
				flash("Başarıyla giriş yaptınız!", "info")
				return redirect(url_for("home"))
			else:
				flash("Kullanıcı adı veya parola yanlış!")
				return redirect(url_for("login"))
		else:
			flash("Böyle bir kullanıcı bulunamadı!")
			return redirect(url_for("login"))		
	else:
		if "user" in session:
			flash("Zaten giriş yaptınız!")
			return redirect(url_for("home"))
		else:
			return render_template("login.html")

@app.route("/forget", methods=["POST", "GET"])
def forget():
	if request.method == "POST":
		if "user" in session:
			return redirect(url_for("home"))
		username = request.form["name"]
		user = User.query.filter_by(name=username).first()
		email = user.email
		psw = randomString()
		user.password = psw
		db.session.commit()
		msg = Message("Bugün Ne Yapsam Geçici Şifreniz", sender=("Bugun Ne Yapsam","bugunneyapsam.authenticate@gmail.com"), recipients=[email])
		msg.body = "Geçici şifrenizle giriş yapabilirsiniz: {}".format(psw)
		mail.send(msg)
		flash("Şifreniz başarıyla sıfırlanmıştır. Yeni şifrenizi kayıtlı e-posta adresinize gönderdik. Şifrenizi daha sonra profil bölümünden değiştirebilirsiniz.")
		return redirect(url_for("home"))

	else:
		return render_template("forget.html")

@app.route("/authenticate", methods=["POST", "GET"])
def authenticate():
	if request.method == "POST":
		username = request.form['name']
		found_user = User.query.filter_by(name=username).first()
		if found_user:
			if found_user.authenticated == True:
				flash("Hesabınız zaten aktive edilmiş!")
				return redirect(url_for("home"))
			email = found_user.email
			if send_email(email):
				flash("Aktivasyon kodunuz başarıyla yollandı!")
			else:
				flash("Aktivasyon kodu yollanamadı")
			return redirect(url_for("home"))
		else:
			flash("Boyle bir kullanıcı bulunamadı. Lütfen kullanıcı adınızı doğru girdiğinize emin olunuz!")
			return render_template("authenticate.html")

	else:
		return render_template("authenticate.html")

@app.route('/confirm_email/<token>')
def confirm_email(token):
	try:
		email = s.loads(token, salt='email-confirm', max_age=300)
	except SignatureExpired:
		flash("Linkin suresi geçmiş lütfen yeni link ile tekrar deneyiniz :(")
		return redirect(url_for("authenticate"))
	found_user = User.query.filter_by(email=email).first()
	found_user.authenticated = True
	db.session.commit()
	session["user"] = found_user.name
	session["email"] = found_user.email
	flash("Hesabınızı başarıyla aktive ettiniz ve giriş yaptınız!", "info")
	return redirect(url_for("home"))


@app.route("/user", methods=["POST", "GET"])
def user():
	if request.method == "POST":
		user = User.query.filter_by(name=session["user"]).first()
		if 'name_change' in request.form:
			name = request.form['name']
			found_user = User.query.filter_by(name=name).first()
			if found_user:
				if name == found_user.name:
					flash("Bu kullanıcı adı zaten alınmış :( Lütfen başka bir kullanıcı adıyla tekrar dene!", "info")
					return redirect(url_for("user"))
			user.name = name
			db.session.commit()
			session.pop("user", None)
			session["user"] = name
			flash('Kullanıcı adınız başariyla değiştirildi!')
			return redirect(url_for('user'))
		elif 'email_change' in request.form:
			email = request.form['email']
			found_email = User.query.filter_by(email=email).first()
			if found_email:
				if email == found_email.email:
					flash("Bu e-posta zaten kullanılıyor.", "info")
					return redirect(url_for("user"))
			user.email = email
			user.authenticated = False
			db.session.commit()
			session.pop("email", None)
			session["email"] = email
			send_email(email)
			flash("Lütfen hesabınızı tekrar aktive ediniz!")
			return redirect(url_for("home"))
		elif 'pass_change' in request.form:
			password = request.form['parola']
			user.password = password
			db.session.commit()
			flash('Şifreniz başariyla değiştirildi!')
			return redirect(url_for('user'))
		elif 'cats_change' in request.form:
			cat_ids1 = request.form.getlist("cat_list1")
			cat_ids2 = request.form.getlist("cat_list2")
			cat_ids = cat_ids1+cat_ids2
			user.categories = encodeToString(cat_ids)
			db.session.commit()
			flash('Kategorileriniz başarıyla değiştirildi!')
			return redirect(url_for('user'))
		else:
			return redirect(url_for('user'))

	else:
		if "user" in session:
			user = User.query.filter_by(name=session["user"]).first()
			values = decodeToList(user.categories)
			return render_template("user.html", user=user, values=values, categories=CATS)
		else:
			flash("Giriş yapmadınız!")
			return redirect(url_for("login"))


@app.route("/logout")
def logout():
	if "user" in session:
		flash("Başarıyla çıkış yaptınız!", "info")
		session.pop("user", None)
		session.pop("email", None)
	return redirect(url_for("home"))

@app.route("/get_advice")
def get_advice():
	has_valid_text = False
	chars = ['a', 'e', 'ı', 'i', 'o', 'ö', 'u', 'ü', 'A', 'E', 'I', 'İ', 'O', 'Ö', 'U', 'Ü']
	for c in chars:
		if c in session["advicetext"]:
			has_valid_text = True
	if has_valid_text:
		db.session.add(Post(session["advicetext"], session["category"]))
		db.session.commit()
	return redirect(session["last_url"])

@app.route("/delete", methods=["POST", "GET"])
def delete():
	# Herhangi bir sorun olursa kullanici silmek icin kullanilabilir
	if "user" in session.keys():
		if session["user"] == "admin":
			if request.method == "POST":
				username = request.form["username"]
				psw = request.form["pass"]
				if psw == ADMIN_PASSWORD:
					User.query.filter_by(name=username).delete()
					db.session.commit()
					flash("Kullanici başarıyla silindi")
					return render_template("delete.html")
				else:
					flash("Parola yanlış")
					return render_template("delete.html")
			else:
				return render_template("delete.html")
	return redirect(url_for("home"))

# Sends authentication email
def send_email(email:str)->bool:
	token = s.dumps(email, salt='email-confirm')
	msg = Message("Bugun Ne Yapsam Aktivasyon", sender=("Bugun Ne Yapsam","bugunneyapsam.authenticate@gmail.com"), recipients=[email])
	link = url_for('confirm_email', token=token, _external=True)
	msg.body = 'Aktivasyon linkinizi lütfen kopyalayıp tarayıcnıza yapıştırınız: {}'.format(link)
	mail.send(msg)
	return True

def randomString(stringLength=12):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))

@app.route("/delete_post:<id>")
def delete_post(id):
	if "user" in session:
		if session["user"] == "admin":
			db.session.query(Post).filter_by(_id=id).delete()
			db.session.commit()
			flash("Sectiginiz post basariyla silindi!")	
	return redirect(url_for("home"))

@app.route("/memo")
def about_us():
	if 'user' in session:
		return render_template("about_us_usr.html")
	return render_template("about_us.html")

if __name__ == "__main__":
	db.create_all()
	'''
	admin = User('admin', 'bugunneyapsam.authenticate@gmail.com', 'iel18siker', '11111111')
	admin.authenticated = True
	db.session.add(admin)
	db.session.commit()
	'''
	app.run(debug = True)




