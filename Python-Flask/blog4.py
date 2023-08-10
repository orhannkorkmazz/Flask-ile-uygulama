from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators,EmailField
from passlib.hash import sha256_crypt
from functools import wraps # decoratorler için kullanılan bir yapı

app=Flask(__name__)
app.secret_key="okblog"
app.config["MYSQL_HOST"]="localhost"
app.config["MYSQL_USER"]="root"
app.config["MYSQL_PASSWORD"]=""
app.config["MYSQL_DB"]="okblog"
app.config["MYSQL_CURSORCLASS"]="DictCursor"
mysql=MySQL(app) # yapılan bu işlemlerde flask ile mysql arasında ki işlemleri kurmuş olduk 
#WT formlarını kullanarak hazır formları kullandıgğımız için daha az kodla işimizi halledebiliriz
#diğer yandan formları kendimizde oluşturabiliriz biz burada wt kullanarak işlemlerimizi yapıcaz
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash ("Bu sayfayı görüntülemek için lüten giriş yapın","danger")
            return redirect(url_for("login"))
    return decorated_function
#kullanıcı kayıt formu için;
class RegisterForm(Form):
    name=StringField("İsim Soyisim:",validators=[validators.length(min=4,max=25)])
    username=StringField("Kullanıcı Adı:",validators=[validators.length(min=5,max=30)])
    email=StringField("Email:",validators=[validators.Email(message="Email adresinizi doğru giriniz")])
    password=PasswordField("Parola:",validators=[validators.DataRequired(message="Lütfen bir parola beliirleyiniz."),validators.EqualTo(fieldname="confirm",message="Parolanız uyuşmuyor")])
    confirm=PasswordField("Parolanızı doğrulayınız")
class LoginForm(Form):
    username=StringField("Kullanıcı Adı:")
    password=PasswordField("Parola:")

@app.route("/")
def index():
    return render_template("index2.html")
@app.route("/about")
def about():
    return render_template("about.html")
@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()

    sorgu = "Select * From article "

    result = cursor.execute(sorgu)

    if result > 0:
        articles = cursor.fetchall()
        return render_template("articles.html",articles = articles)
    else:
        return render_template("articles.html")
#@app.route("/article/<string:id>")
#def detail(id):
 #   return "Article id:" + id
@app.route("/register",methods=["GET","POST"])
def register():
    form=RegisterForm(request.form)
    if request.method== "POST" and form.validate():
        name=form.name.data
        username=form.username.data
        email=form.email.data
        password=sha256_crypt.encrypt(form.password.data) #sha256 modülünün içindeki fonksiyonu kullanarak parolayı şifreleme işlemi yaptık.
        cursor=mysql.connection.cursor()
        sorgu="insert into users(name,username,email,password) VALUES (%s,%s,%s,%s)"
        cursor.execute(sorgu,(name,username,email,password))
        
        mysql.connection.commit()
        cursor.close()
        flash("Başarıyla kayıt oldunuz","success")
        return redirect(url_for('register'))
    
    else:
        return render_template("register.html",form=form)
#flaska requestin get mi post mu olduğunu belirtmezsek hata alırız bunu belirtmk için de requests modülünü ekledik
@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()

    sorgu = "Select * From article where author = %s"

    result = cursor.execute(sorgu,(session["username"],))

    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html",articles = articles)
    else:
        return render_template("dashboard.html")
@app.route("/login",methods = ["GET","POST"])
def login():
    form=LoginForm(request.form)
    if request.method== "POST":
        
        username=form.username.data
        password=form.password.data
        cursor=mysql.connection.cursor()
        sorgu= "Select * From users where username=%s"
        result=cursor.execute(sorgu,(username,))
        if result>0 :
            data=cursor.fetchone()
            real_password=data["password"]
            if sha256_crypt.verify(password,real_password): # burada yapılan işlem paralo şifrelendiği için girilen parolanın doğruluğunu kontrol etmek
                flash("Başarıyla giriş yaptınız","success")
                session["logged_in"]=True# session giriş yapıldığında kullanıcıyı aktif etme işlemi gibi düşünülebilir
                session["username"]=username
                
                return redirect(url_for('index'))
            else:
                flash("Parolanızı yanlış girdiniz...","danger")
                return redirect(url_for('login'))
        else:
            flash("Böyle bir kullanıcı bulunmuyor","danger")
            return redirect(url_for('login'))
    return render_template("login.html",form = form)
# Detay Sayfası
@app.route("/article/<string:id>")
def article(id):
    cursor = mysql.connection.cursor()
    
    sorgu = "Select * from article where id = (%s)"

    result = cursor.execute(sorgu,(id,))

    if result > 0:
        article = cursor.fetchone()
        return render_template("article.html",article = article)
    else:
        return render_template("article.html")
#makale silme
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()

    sorgu = "Select * from article where author = %s and id = %s"

    result = cursor.execute(sorgu,(session["username"],id))

    if result > 0:
        sorgu2 = "Delete from article where id = %s"

        cursor.execute(sorgu2,(id,))

        mysql.connection.commit()

        return redirect(url_for("dashboard"))
    else:
        flash("Böyle bir makale yok veya bu işleme yetkiniz yok","danger")
        return redirect(url_for("index"))
@app.route("/edit/<string:id>",methods = ["GET","POST"])
@login_required
def update(id):
   if request.method == "GET":
       cursor = mysql.connection.cursor()

       sorgu = "Select * from article where id = %s and author = %s"
       result = cursor.execute(sorgu,(id,session["username"]))

       if result == 0:
           flash("Böyle bir makale yok veya bu işleme yetkiniz yok","danger")
           return redirect(url_for("index"))
       else:
           article = cursor.fetchone()
           form = ArticleForm()

           form.title.data = article["title"]
           form.content.data = article["content"]
           return render_template("update.html",form = form)

   else:
       # POST REQUEST
       form = ArticleForm(request.form)

       newTitle = form.title.data
       newContent = form.content.data

       sorgu2 = "Update article Set title = %s,content = %s where id = %s "

       cursor = mysql.connection.cursor()

       cursor.execute(sorgu2,(newTitle,newContent,id))

       mysql.connection.commit()

       flash("Makale başarıyla güncellendi","success")

       return redirect(url_for("dashboard"))

       pass
   # Arama URL
@app.route("/search",methods = ["GET","POST"])
def search():
   if request.method == "GET":
       return redirect(url_for('index'))
   else:
       keyword = request.form.get("keyword")

       cursor = mysql.connection.cursor()

       sorgu = "Select * from article where title like '%" + keyword + "%' "

       result = cursor.execute(sorgu)

       if result == 0:
           flash("Aranan kelimeye uygun makale bulunamadı...","warning")
           return redirect(url_for('articles'))
       else:
           articles = cursor.fetchall()

           return render_template("articles.html",articles = articles)
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('index'))
@app.route("/addarticle",methods=["GET","POST"])   
def addarticle():
    form=ArticleForm(request.form)
    if request.method== "POST" and form.validate():
        title=form.title.data
        content=form.content.data
        cursor=mysql.connection.cursor()
        sorgu   ="insert into article(title,author,content) VALUES (%s,%s,%s)"
        cursor.execute(sorgu,(title,session["username"],content))
        mysql.connection.commit()
        cursor.close()
        flash ("Makale başarıyla eklendi","success")
        return redirect(url_for('dashboard'))
    return render_template("/addarticle.html",form=form)
class ArticleForm(Form):
    title=StringField("Makale Başlığı",validators=[validators.length(min=5,max=100)])
    content=TextAreaField("Makale içeriği",validators=[validators.length(min=10)])
    
if __name__=="__main__":
    app.run(debug=True)