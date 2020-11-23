#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
import numpy as np
from sqlalchemy import create_engine 
from sqlalchemy import func
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config') #also connects to database
db = SQLAlchemy(app)
session = db.session()

# Cursors are slower, but I am really not familiar with SQLAlchemy, yet. 

migrate=Migrate(app,db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    genres = db.Column(db.String(120)) #Stored as a list
    address = db.Column(db.String(120))
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    website=db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    seeking_talent=db.Column(db.Boolean, default=True)
    image_link = db.Column(db.String(500))
    seeking_description=db.Column(db.String(500))
    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120)) #Stored as a list
    image_link = db.Column(db.String(500))
    website=db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default=True)
    seeking_description=db.Column(db.String(120))

    # TODO: implement any missing fields, as a database migration using Flask-Migrat0e

class Show(db.Model):
    __tablename__ = 'Show'
    id=db.Column(db.Integer, primary_key=True)
    artist_id=db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
    venue_id=db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
    start_time=db.Column(db.DateTime, nullable=False)



#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  #
  try:
    date = dateutil.parser.parse(value) #Time entered as a string
  except:
    date=value #Pre-parsed datetime format
  
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  #Our table name is "Venue"
  #data=mycursor('SELECT State, City, Count(ID) from "Venue" group by State, City')
  data=session.query(Venue.state, Venue.city, func.count(Venue.id)).group_by(Venue.state, Venue.city).all()
  lenData=len(data)
  print(data, 'try state ', len(data), ' is the mo fo length ', data[0][1], ', ',  data[0][0])
  dataObj=[]

  for ii in range(lenData):
    city = data[ii][1]
    state= data[ii][0]
    venuesBase=session.query(Venue.id, Venue.name).filter_by(city=city, state=state)
    venuesList=venuesBase.all()
    print('These foos is my venues ', venuesList)
    numVens=len(venuesList)
    venuesArray=[]
    for jj in range(numVens):
      venuesObj={
        "id": venuesList[jj][0],
        "name": venuesList[jj][1],
        "num_upcoming_shows": 79,
      }
      venuesArray.append(venuesObj)
      print('Then this dude over herr got this venues array ', venuesArray)
    #End venuesArray Construction

    if ii==0: #start
      dataObj=[]   
      dataObj=[{
        "city": city,
        "state": state,
        "venues": venuesArray
      }]
      print('First TIMERS! ')
    else:
      dataObj.append({
        "city": city,
        "state": state,
        "venues": venuesArray
      })
      print('Take Two! ')

  test=len(dataObj)
  print('Please for the love of God, print! ', dataObj, ' is this for real??? ', data)


  return render_template('pages/venues.html', areas=dataObj);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  #SELECT State, City, Count(ID) from "Venue" group by State, City
  #asd Venue Query
  searchTerm=request.form.get('search_term', '')
  names=session.query(Venue.id, Venue.name).filter(Venue.name.ilike('%'+ searchTerm + '%')).all()
  data=[0]*len(names)
  
  for ii in range(len(names)):
    data[ii]={
      "id" : names[ii][0],
      "name" : names[ii][1]
    }

  response={
    "count": len(names),
    "data": data
  }
  
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  #session.query(Venue.state, Venue.city, func.count(Venue.id)).group_by(Venue.state, Venue.city).all()
  data=Venue.query.get(venue_id) #asd Venue Query
  data.genres=parseGenres(data.genres)
  showsAll=findShows(venue_id,2)
  data.past_shows=showsAll[1]
  data.upcoming_shows=showsAll[0]

  return render_template('pages/show_venue.html', venue=data)


def findShows(id,option): #given a single ID and a boolean to toggle between Artist (True) and Venue (False)
  searchTime=datetime.now()
  print('Search Time is: ', searchTime)
  print(' THe artists ID is: ', id)
  print(' The MFing option is: ', option)
  if option==1: #Artist shows
    #join show with venue, query artist_id, return show.start_time, venue.id, venue.image
    futureShowList=session.query(Venue.id, Venue.name, Venue.image_link, Show.start_time).filter(Show.artist_id==id, Show.venue_id==Venue.id, Show.start_time>=searchTime).all()
    pastShowList=session.query(Venue.id, Venue.name, Venue.image_link, Show.start_time).filter(Show.artist_id==id, Show.venue_id==Venue.id, Show.start_time<searchTime).all()
  elif option==2: #Venue shows
    futureShowList=session.query( Artist.id, Artist.name, Artist.image_link, Show.start_time).filter(Show.venue_id==id, Artist.id==Show.artist_id, Show.start_time>=searchTime).order_by(Show.start_time).all()
    pastShowList=session.query(Artist.id, Artist.name,  Artist.image_link, Show.start_time).filter(Show.venue_id==id, Artist.id==Show.artist_id, Show.start_time<searchTime).order_by(Show.start_time).all()
  else: #Show shows
    futureShowList=session.query(Venue.id, Venue.name, Artist.id, Artist.name, Artist.image_link, Show.start_time).filter(Venue.id==Show.venue_id, Artist.id==Show.artist_id).order_by(Show.start_time).all()
    pastShowList=[] #doesn't matter
  
  print('Pre-parse analysis: Artist ID is ', id, ' option is ', option, ' the future show length is ', len(futureShowList), ' and the past show length is ', len(pastShowList))
  #print('Future Shows are: ', futureShowList)
  #print('Past Shows are: ', pastShowList)

  futureShowArray=parseShows(futureShowList, option)
  pastShowArray=parseShows(pastShowList, option)

  showsAll=[futureShowArray, pastShowArray]

  print(showsAll)
  return showsAll

def parseShows(showList, option): # Option 1: Artist, Option 2: Venue, Option 3: Show Home

  showArray=[]
  print('Print of length of show list: ', len(showList))
  print('Print of show list:', showList)
  if option==1:
    for ii in showList:
      showArray.append({
        'venue_id': ii[0],
        'venue_name': ii[1],
        'venue_image_link': ii[2],
        'start_time': ii[3]
      })
  elif option == 2:
    for ii in showList:
      showArray.append({
        'artist_id': ii[0],
        'artist_name':ii[1],
        'artist_image_link':ii[2],
        'start_time':  ii[3]
      })
  else: 
    for ii in showList: #show screen
      showArray.append({
        'venue_id': ii[0],
        'venue_name':ii[1],
        'artist_id':ii[2],
        'artist_name':ii[3],
        'artist_image_link':ii[4],
        'start_time':  ii[5]
      })

  return showArray

def parseGenres(data_in):
  array=[]
  data_in=data_in.replace('{',"")
  data_in=data_in.replace('}',"")
  data_in=data_in.replace('"',"")

  found = data_in.find(",")

  while found>-1:
    strTemp=data_in[0:found]
    array.append(strTemp)
    data_in=data_in[found+1:]
    found=data_in.find(",")

  array.append(data_in) 
  return array


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  try:
    name = request.form['name']
    city = request.form['city']
    state= request.form['state']
    address = request.form['address']
    phone = request.form['phone']
    image_link=request.form['image_link']
    genres=request.form.getlist('genres')
    facebook_link = request.form['facebook_link']
    website=request.form['website']
    seeking_talent=request.form['seeking_talent']
    if seeking_talent=="Yes":
      seeking_talent=True
    else:
      seeking_talent=False

    seeking_description=request.form['seeking_description']

    newVenue=Venue(name=name, city=city, 
      state=state,address=address, phone=phone, 
      genres=genres, image_link=image_link, 
      facebook_link=facebook_link, website=website, 
      seeking_talent=seeking_talent, 
      seeking_description = seeking_description),
    db.session.add(newVenue)
    db.session.commit()
    flash('Venue ' + name +  ' was successfully created!')
  except:
    error=True
    db.session.rollback()
    flash('An error occurred. Venue ' + name + ' could not be listed.')
  finally:
    db.session.close()
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data=session.query(Artist.id, Artist.name).all()
  print('The Artists data is: ', data)
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  #Gets "search_term" from the search bar, searches database for term, returns object "response" of results
  searchTerm=request.form.get('search_term', '')
  names=session.query(Artist.id, Artist.name).filter(Artist.name.ilike('%'+ searchTerm + '%')).all()
  data=[0]*len(names)

  for ii in range(len(names)):
    data[ii]={
      "id" : names[ii][0],
      "name" : names[ii][1]
    }

  response={
    "count": len(names),
    "data": data
  }

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):

  data=Artist.query.get(artist_id)
  data.genres=parseGenres(data.genres)
  showsAll=findShows(artist_id,1)
  data.past_shows=showsAll[1] #showsAll returns an array of two objects [upcomingShows, pastShows]
  data.upcoming_shows=showsAll[0]
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()

  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue={
    "id": 1,
    "name": "The Musical Hop",
    "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
    "address": "1015 Folsom Street",
    "city": "San Francisco",
    "state": "CA",
    "phone": "123-123-1234",
    "website": "https://www.themusicalhop.com",
    "facebook_link": "https://www.facebook.com/TheMusicalHop",
    "seeking_talent": True,
    "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
    "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
  }
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  try:
    name = request.form['name']
    city = request.form['city']
    state= request.form['state']
    phone = request.form['phone']   
    genres=request.form.getlist('genres')
    image_link=request.form['image_link']
    facebook_link = request.form['facebook_link']
    genreLength=str(len(genres))
    newArtist=Artist(name=name, city=city, state=state, phone=phone, genres=genres, image_link=image_link, facebook_link=facebook_link)
    db.session.add(newArtist)
    db.session.commit()
    flash('The artist page  ' + name + ' was successfully listed!')
  except:
    error=True
    db.session.rollback()
    flash('An error occurred. Artist ' + name + ' could not be listed.')
  finally:
    db.session.close()
  
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  
  showsArray=findShows(1,3) 
  data=showsArray[0]
  
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  try:
    venue_id = request.form['venue_id']
    artist_id=request.form['artist_id']
    start_time=request.form['start_time']
    newShow=Show(venue_id=venue_id, artist_id=artist_id, start_time=start_time)
    db.session.add(newShow)
    db.session.commit()
    flash('Show was successfully listed!')
 
  except:
    error=True
    db.session.rollback()
    flash('An error occurred. Artist ' + name + ' could not be listed.')
  finally:
    db.session.close()
  
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
