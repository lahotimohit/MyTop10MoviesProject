from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests

URL = "https://api.themoviedb.org/3/search/movie"
api_key = "0ad7a2dc9832221f348972b06f4ef903"

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///user_movies.db"

db = SQLAlchemy()
db.init_app(app)


class Movies(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), unique=True,nullable=False)
    year = db.Column(db.Integer,nullable=False)
    description = db.Column(db.String(600),nullable=False)
    rating = db.Column(db.Float,nullable=True)
    ranking = db.Column(db.Float,nullable=True)
    review = db.Column(db.String(200),nullable=True)
    image_url = db.Column(db.String(200),nullable=False)


Bootstrap5(app)


class RatingForm(FlaskForm):
    rating = StringField("Give rating out of 10")
    review = StringField("Give your review")
    submit = SubmitField("Done")


class AddForm(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField("Add Movie")

with app.app_context():
    db.create_all()


@app.route("/")
def home():
    movie_list = db.session.execute(db.select(Movies).order_by(Movies.rating)).scalars().all()
    for i in range(len(movie_list)):
        movie_list[i].ranking = len(movie_list) - i
    db.session.commit()
    return render_template("index.html", movies=movie_list)


@app.route("/edit", methods=["GET", "POST"])
def edit():
    form = RatingForm()
    movie_id = request.args.get("id")
    movie = db.get_or_404(Movies, movie_id)
    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", movie=movie, form=form)


@app.route('/delete')
def delete():
    delete_movie_id = request.args.get("id")
    delete_movie = db.get_or_404(Movies, delete_movie_id)
    db.session.delete(delete_movie)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/add", methods=["GET", "POST"])
def add_movie():
    add_form = AddForm()
    if add_form.validate_on_submit():
        parameters = {
            "api_key":api_key,
            "query":add_form.title.data
        }
        response = requests.get(url=URL, params=parameters)
        data = response.json()["results"]
        return render_template("select.html", options=data)
    return render_template("add.html", form=add_form)


@app.route("/find")
def find_movie():
    movie_api_id = request.args.get("id")
    if movie_api_id:
        movie_url = f"https://api.themoviedb.org/3/movie/{movie_api_id}"
        response = requests.get(url=movie_url, params={"api_key": api_key})
        data = response.json()
        new_movie = Movies(
            title=data["title"],
            year=data["release_date"].split("-")[0],
            description=data["overview"],
            image_url= f"http://image.tmdb.org/t/p/w500/{data['poster_path']}"
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for('edit', id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
