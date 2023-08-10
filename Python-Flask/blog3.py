from flask import Flask,render_template
app=Flask(__name__)
@app.route("/")
def index():
    return render_template("index2.html")
@app.route("/about")
def about():
    return render_template("about.html")
@app.route("/article/<string:id>")
def detail(id):
    return "Article id:" + id
if __name__=="__main__":
    app.run(debug=True)