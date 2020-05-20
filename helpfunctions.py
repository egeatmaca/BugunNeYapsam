from webapp import *

# Categories
# Herhangi bir ekleme veya cikarma yapilirsa enc list indede ayni islemi uygulayin!
CATS = [
		"Sinema", 					# 0
		"Spor ve Saglikli Yasam",	# 1
		"Oyunlar",					# 2
		"Kitap",					# 3
		"Kisisel Gelisim",			# 4
		"Egitim",					# 5
		"Mutfak",					# 6
		"Diger"						# 7
	]

# Encodes categories into a byte String
def encodeToString(categories:list) ->str:
	enc = ['0','0','0','0','0','0','0','0']
	for idx, cat in enumerate(CATS):
		if cat in categories:
			enc[idx] = '1'
	if "Spor" in categories:
		enc[1] = '1'
	if "Kisisel" in categories:
		enc[4] = '1'

	return "".join(enc)


# Decodes byte String into categories list
def decodeToList(enc:str) ->list:
	dec = []
	length = len(CATS)
	for idx, char in enumerate(enc):
		if char == '1' and idx < length:
			dec.append(CATS[idx])
	return dec


#postlari farkli sekillerde siralar (en yeni, en cok begenilen vs.) daha yazilacak
def get_posts(category = "all", by = "points"):
	content = []
	by_params = {"points": Post.points, "date": Post._id}
	if category == "all":
		if by == "date":
			if "user" in session.keys():
				user_categories = decodeToList(db.session.query(User.categories).filter(User.name == session["user"]).first()[0])
				for user_category in user_categories:
					content = content + db.session.query(Post._id, Post.text, Post.ups, Post.downs, Post.points).filter(Post.category == user_category).order_by(Post._id.desc()).all()
				content = sort_posts(content, by = "id")
			else:
				content = db.session.query(Post._id, Post.text, Post.ups, Post.downs, Post.points).order_by(Post._id.desc()).all()
		elif by == "points":
			if "user" in session.keys():
				user_categories = decodeToList(db.session.query(User.categories).filter(User.name == session["user"]).first()[0])
				for user_category in user_categories:
					content = content + db.session.query(Post._id, Post.text, Post.ups, Post.downs, Post.points).filter(Post.category == user_category).order_by(Post._id.desc()).all()
				content = sort_posts(content, by = "points")
			else:
				content = db.session.query(Post._id, Post.text, Post.ups, Post.downs, Post.points).order_by(Post.points.desc()).all()
		elif by == "points_mixedcats":
			if "user" in session.keys():
				categorized = []
				categorized_lengths = []
				user_categories = decodeToList(
					db.session.query(User.categories).filter(User.name == session["user"]).first()[0])
				for user_category in user_categories:
					categorized.append(db.session.query(Post._id, Post.text, Post.ups, Post.downs, Post.points).filter(
						Post.category == user_category).order_by(Post.points.desc()).all())
				for arr in categorized:
					categorized_lengths.append(len(arr))
				for i in range(np.asarray(categorized_lengths).max()):
					for j in range(len(categorized)):
						if i < len(categorized[j]):
							content.append(categorized[j][i])
			else:
				content = db.session.query(Post._id, Post.text, Post.ups, Post.downs, Post.points).order_by(Post.points.desc()).all()
	else:
		content = db.session.query(Post._id, Post.text, Post.ups, Post.downs, Post.points).filter_by(category = category).order_by(by_params[by].desc()).all()
	return content

def sort_posts(arr, by = "points"):
	if by == "id":
		if len(arr) < 2:
			return arr
		p = len(arr) - 1
		left = []
		right = []
		border = []
		for i in range(0, len(arr)):
			if arr[i]._id > arr[p]._id:
				left.append(arr[i])
			elif arr[i]._id < arr[p]._id:
				right.append(arr[i])
			else:
				border.append(arr[i])
		left = sort_posts(left, by = "id")
		right = sort_posts(right, by = "id")
		return left + border + right
	elif by == "points":
		if len(arr) < 2:
			return arr
		p = len(arr) - 1
		left = []
		right = []
		border = []
		for i in range(0, len(arr)):
			if arr[i].points > arr[p].points:
				left.append(arr[i])
			elif arr[i].points < arr[p].points:
				right.append(arr[i])
			else:
				border.append(arr[i])
		left = sort_posts(left)
		right = sort_posts(right)
		return left + border + right

def get_home_requests():
	if "oneri" in request.form:
		session.permanent = True
		session["advicetext"] = request.form["oneri"]
		session["category"] = request.form["kategori"]
		session["last_url"] = request.url
		return redirect(url_for("get_advice"))
	elif "order" in request.form:
		if request.form["order"] == "En Yeni":
			session["order"] = "date"
		else:
			session["order"] = "points"
	else:
		if "up" in request.form:
			if "user" in session.keys():
				founded_user = db.session.query(User).filter_by(name=session["user"]).first()
				founded_post = db.session.query(Post).filter_by(_id=request.form["id"]).first()
				if request.form["id"] not in founded_user.ups.split(","):
					if request.form["id"] in founded_user.downs.split(","):
						founded_user.downs = founded_user.downs.replace(request.form["id"] + ",", "")
						founded_post.downs = founded_post.downs - 1
					founded_user.ups = founded_user.ups + request.form["id"] + ","
					founded_post.ups = founded_post.ups + 1
					founded_post.points = founded_post.ups - founded_post.downs
					db.session.commit()
				else:
					flash("Bu oneriye zaten yukari dediniz!", "info")
			else:
				flash("Yukari demek icin lutfen giris yapiniz!")
		elif "down" in request.form:
			if "user" in session.keys():
				founded_user = db.session.query(User).filter_by(name=session["user"]).first()
				founded_post = db.session.query(Post).filter_by(_id=request.form["id"]).first()
				if request.form["id"] not in founded_user.downs.split(","):
					if request.form["id"] in founded_user.ups.split(","):
						founded_user.ups = founded_user.ups.replace(request.form["id"] + ",", "")
						founded_post.ups = founded_post.ups - 1
					founded_user.downs = founded_user.downs + request.form["id"] + ","
					founded_post.downs = founded_post.downs + 1
					founded_post.points = founded_post.ups - founded_post.downs
					db.session.commit()
				else:
					flash("Bu oneriye zaten asagi dediniz!", "info")
			else:
				flash("Asagi demek icin lutfen giris yapiniz!", "info")
	return redirect(request.url)


# For testing:
#print(encodeToString(["Oyunlar", "Kitap"]))
#print(decodeToList("010100000"))
