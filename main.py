from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField,FloatField
from wtforms.validators import DataRequired
import requests
import os
from dotenv import load_dotenv


app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
Bootstrap5(app)

# CREATE DB
class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')

db = SQLAlchemy(model_class=Base)
db.init_app(app)

load_dotenv()

# CREATE TABLE
class Movies(db.Model):
    id : Mapped[Integer] = mapped_column(Integer,primary_key=True, nullable=False)
    title : Mapped[String] = mapped_column(String(250),unique=True,nullable=False)
    year : Mapped[Integer] = mapped_column(Integer, nullable=False)
    description : Mapped[String] = mapped_column(String(255),nullable=False)
    ranking : Mapped[Integer] = mapped_column(Integer)
    rating : Mapped[Float] = mapped_column(Float)
    review : Mapped[String] = mapped_column(String(250))
    image_url : Mapped[String] = mapped_column(String(255))


with app.app_context():
    db.create_all()


#bforms
class MyForm(FlaskForm):
    rating = FloatField('Your rating out of 10 e.g 4.3')
    review = StringField('Give your review')
    submit = SubmitField('Done')

class AddForm(FlaskForm):
    movie_name = StringField('Enter the Title',validators=[DataRequired(message="Enter the Movie Title")])
    submit = SubmitField('Add Movie')

# routes  
def get_movies(movie_name: str):
    API_TOKEN = os.getenv('API_TOKEN')
    url = f"https://api.themoviedb.org/3/search/movie"
    params = {"query": movie_name}
    header = {"Authorization": f"Bearer {API_TOKEN}", "Content-Type": "application/json"}

    response = requests.get(url=url, headers=header, params=params)
    response.raise_for_status()
    
    return response.json()


@app.route("/")
def home():
    db_data = db.session.execute(db.select(Movies).order_by(Movies.rating)) 
    db_data_list = db_data.scalars().all()
    for rank in range(len(db_data_list)):
        db_data_list[rank].ranking = len(db_data_list) - rank
    db.session.commit()    
    return render_template("index.html",data = db_data_list)

@app.route('/edit',methods = ['GET','POST'])
def Edit():
    form = MyForm()
    movie_id = request.args.get('id')
    check_in_db = db.get_or_404(Movies,movie_id)
    
    if form.validate_on_submit():
        check_in_db.rating = form.rating.data       # type: ignore
        check_in_db.review = form.review.data       # type: ignore
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html",movie = check_in_db, form=form)

@app.route('/delete')
def Delete():
    movie_id = request.args.get('id')
    movie_to_delete = db.session.execute(db.select(Movies).where(Movies.id==movie_id)).scalar()
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/add',methods=["POST","GET"])
def Add():
    form = AddForm()
    if form.validate_on_submit():
        movies = get_movies(form.movie_name.data)                                   # type: ignore
        return render_template('select.html', movies=movies)
    return render_template('add.html',form= form)

@app.route('/find_movie/<int:id>',methods=["POST","GET"])
def Find_Movie(id):
    API_TOKEN =os.getenv('API_TOKEN')
    movie_url = f"https://api.themoviedb.org/3/movie/{id}"
    header = {
    "accept": "application/json",
    "Authorization": f"Bearer {API_TOKEN} "
}
    response = requests.get(url=movie_url,headers=header,params={'language':'en-US'} )
    data =  response.json()
    new_movies = Movies(
        title = data['original_title'],                                             # type: ignore
        year = data['release_date'].split('-')[0],                                  # type: ignore
        image_url = f"https://image.tmdb.org/t/p/original/{data['poster_path']}",   # type: ignore
        description = data['overview']                                              # type: ignore
    )
    db.session.add(new_movies)
    db.session.commit()
    
    return redirect(url_for('Edit',id=new_movies.id))


if __name__ == '__main__':
    app.run(debug=True)
