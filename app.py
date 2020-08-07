#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
import sys
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import func
from flask_migrate import Migrate
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)


migrate = Migrate(app, db) 

# DONE : connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    genres = db.Column(ARRAY(db.String), nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String)
    shows = db.relationship('Show', backref='venue', cascade="all,delete", lazy=True) #cascade delete so when you delete a venue it deletes all shows for that venue
    
    def __repr__(self):
      return f"VENue('{self.id}', '{self.name}', '{self.genres}', '{self.city}', '{self.state}', '{self.address}', '{self.phone}', '{self.image_link}', '{self.facebook_link}')"

    # DONE: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'Artist'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    genres = db.Column(ARRAY(db.String))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String)
    shows = db.relationship('Show', backref='artist', lazy=True)

    def __repr__(self):
      return f"ARtist('{self.name}')"

class Show(db.Model):
    __tablename__ = 'Show'
    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f"<Show('{self.id}', '{self.venue_id}'>"

# DONE Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
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
  #DONE: replace with real venues data.
  #      num_shows should be aggregated based on number of upcoming shows per venue.
  data = []
  city_state = Venue.query.with_entities(Venue.city, Venue.state).group_by(Venue.city, Venue.state).all()

  #build out the venues list, grouped by city/state
  for loc in city_state:
    cityvenue = Venue.query.filter_by(state=loc.state).filter_by(city=loc.city).all()
    venue_names = []
    for v in cityvenue:
      upcoming_shows = Show.query.filter_by(venue_id=v.id).filter(Show.start_time > datetime.now()).all()
      venue_names.append({
        "id" : v.id,
        "name" : v.name,
        "num_upcoming_shows" : len(upcoming_shows)
      })
    data.append({
      "city" : loc.city,
      "state" : loc.state,
      "venues" : venue_names
    })
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # DONE: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_term = request.form.get('search_term', '').upper() #case insesitive 
  venues = Venue.query.all() 
  results = []
  count = 0
  for ven in venues:
    current_name = ven.name.upper()
    if (current_name.find(search_term) != -1):
      count += 1
      results.append(ven)

  response = {
   "count" : count,
   "data" : results 
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
   
  data_v = Venue.query.get(venue_id)
  shows = Show.query.filter_by(venue_id=venue_id)
  upcoming_shows = []
  past_shows_list = []

  for show in shows:
    if (datetime.now() > show.start_time): # must be a past show
      past_shows_list.append({
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": format_datetime(str(show.start_time))
      })
    else: # add to upcoming shows
      upcoming_shows.append({
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": format_datetime(str(show.start_time))  
      })

  data = {
    "id": data_v.id,
    "name": data_v.name,
    "genres": data_v.genres,
    "address": data_v.address,
    "city": data_v.city,
    "state": data_v.state,
    "phone": data_v.phone,
    "website": data_v.website,
    "facebook_link": data_v.facebook_link,
    "seeking_talent": data_v.seeking_talent,
    "seeking_description": data_v.seeking_description,
    "image_link": data_v.image_link,
    "past_shows" : past_shows_list,
    "past_shows_count": len(past_shows_list),
    "upcoming_shows": upcoming_shows,
    "upcoming_shows_count": len(upcoming_shows)
  }
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # DONE: insert form data as a new Venue record in the db, instead
  # DONE: modify data to be the data object returned from db insertion
  
  try:
    seeking_artist = request.form.get('seeking_artist', None)
    venue = Venue(  #Try to create a new Venue object and add to the db
      name = request.form['name'],
      genres = request.form.getlist('genres'),
      address = request.form['address'],
      city = request.form['city'],
      state = request.form['state'],
      phone = request.form['phone'],
      facebook_link = request.form['facebook_link'],
      website = request.form['website'],
      image_link = request.form['image_link'],
      seeking_talent = True if seeking_artist != None else False,
      seeking_description = request.form['seeking_description']
    )
    db.session.add(venue)
    db.session.commit()
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    # DONE: on unsuccessful db insert, flash an error instead.
    db.session.rollback()
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
    print(sys.exc_info())
  finally:
    db.session.close()
  
  return render_template('pages/home.html')

#@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
@app.route('/venues/<int:venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # DONE: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  # DONE
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return render_template('layouts/main.html')

@app.route('/venues/<int:venue_id>/delete', methods=['GET'])
def delete_venue_submission(venue_id):
  try:
    venue = Venue.query.get(venue_id)
    
    db.session.delete(venue)
    db.session.commit()
    flash('The Venue has been successfully deleted!')
    #Redirect back to home page
    return render_template('pages/home.html')
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash('Delete was unsuccessful. Try again!')
  finally:
    db.session.close()
  return render_template('layouts/main.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # DONE: replace with real data returned from querying the database
  data = Artist.query.all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # DONE: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".

  search_term = request.form.get('search_term', '').upper()
  artists = Artist.query.all() 
  results = []
  count = 0
  for art in artists:
    current_name = art.name.upper()
    if (current_name.find(search_term) != -1):
      count += 1
      results.append(art)

  response = {
   "count" : count,
   "data" : results 
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # DONE: replace with real venue data from the venues table, using venue_id

  data_v = Artist.query.get(artist_id)
  
  shows = Show.query.filter_by(artist_id=artist_id)

  upcoming_shows = []
  past_shows_list = []

  past_shows_count = 0
  for show in shows:
    if (datetime.now() > show.start_time): #must be in the past
      past_shows_list.append({
      "artist_id": show.artist_id,
      "venue_id" : show.venue_id,
      "venue_name": show.venue.name,
      "venue_image_link": show.venue.image_link,
      "start_time": format_datetime(str(show.start_time))
      })
      past_shows_count += 1
    else: # future show
      upcoming_shows.append({
      "artist_id": show.artist_id,
      "venue_id" : show.venue_id,
      "venue_name": show.venue.name,
      "venue_image_link": show.venue.image_link,
      "start_time": format_datetime(str(show.start_time))
      })
  data = {
    "id": data_v.id,
    "name": data_v.name,
    "genres": data_v.genres,
    "city": data_v.city,
    "state": data_v.state,
    "phone": data_v.phone,
    "website" : data_v.website,
    "facebook_link": data_v.facebook_link,
    "seeking_venue": data_v.seeking_venue,
    "seeking_description": data_v.seeking_description,
    "image_link": data_v.image_link,
    "past_shows" : past_shows_list,
    "past_shows_count": past_shows_count,
    "upcoming_shows": upcoming_shows
  }

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):

  form = ArtistForm()
  artist = Artist.query.get(artist_id)

  form.name.data = artist.name
  form.city.data = artist.city
  form.state.data = artist.state
  form.phone.data = artist.phone
  form.genres.data = artist.genres
  form.seeking_venue.data = artist.seeking_venue
  form.seeking_description.data = artist.seeking_description
  form.website.data = artist.website
  form.image_link.data = artist.image_link
  form.facebook_link.data = artist.facebook_link
  
  # DONE: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # DONE: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  artist = Artist.query.get(artist_id)

  try:
    seeking_venue = request.form.get('seeking_venue', None) # creating a velue to check whether the seeking venue box was checked
    
    artist.name = request.form['name']
    artist.genres = request.form.getlist('genres')
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    artist.facebook_link = request.form['facebook_link']
    artist.website = request.form['website']
    artist.image_link = request.form['image_link']
    artist.seeking_venue = True if seeking_venue != None else False
    artist.seeking_description = request.form['seeking_description']
    db.session.add(artist)
    db.session.commit()
    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully updated!')
  except:
    # DONE: on unsuccessful db insert, flash an error instead.
    db.session.rollback()
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.')
    print(sys.exc_info())
  finally:
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)

  form.name.data = venue.name
  form.city.data = venue.city
  form.state.data = venue.state
  form.address.data = venue.address
  form.phone.data = venue.phone
  form.genres.data = venue.genres
  form.seeking_artist.data = venue.seeking_talent
  form.seeking_description.data = venue.seeking_description
  form.website.data = venue.website
  form.image_link.data = venue.image_link
  form.facebook_link.data = venue.facebook_link

  # DONE: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # DONE: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  
  venue = Venue.query.get(venue_id)

  try:
    seeking_artist = request.form.get('seeking_artist', None)
    
    venue.name = request.form['name']
    venue.genres = request.form.getlist('genres')
    venue.address = request.form['address']
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.phone = request.form['phone']
    venue.facebook_link = request.form['facebook_link']
    venue.website = request.form['website']
    venue.image_link = request.form['image_link']
    venue.seeking_talent = True if seeking_artist != None else False
    venue.seeking_description = request.form['seeking_description']
    db.session.add(venue)
    db.session.commit()
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    # DONE: on unsuccessful db insert, flash an error instead.
    db.session.rollback()
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated.')
    print(sys.exc_info())
  finally:
    db.session.close()

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # DONE: insert form data as a new Venue record in the db, instead
  # DONE: modify data to be the data object returned from db insertion
  try:
    seeking_venue = request.form.get('seeking_venue', None)
    artist = Artist(  #Try to create a new Artist object and add to the db
      name = request.form['name'],
      genres = request.form.getlist('genres'),
      city = request.form['city'],
      state = request.form['state'],
      phone = request.form['phone'],
      facebook_link = request.form['facebook_link'],
      website = request.form['website'],
      image_link = request.form['image_link'],
      seeking_venue = True if seeking_venue != None else False,
      seeking_description = request.form['seeking_description']
    )
    db.session.add(artist)
    db.session.commit()
    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
    # DONE: on unsuccessful db insert, flash an error instead.
    db.session.rollback()
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
    print(sys.exc_info())
  finally:
    db.session.close()
  return render_template('pages/home.html')

#  Shows
#  ----------------------------------------------------------------
@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # DONE: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  all_shows = Show.query.all()
  data=[]
  
  for show in all_shows: 
    data.append({
      "venue_id" : show.venue_id,
      "venue_name": show.venue.name, 
      "artist_id": show.artist_id, 
      "artist_name": show.artist.name, 
      "artist_image_link": show.artist.image_link,
      "start_time": format_datetime(str(show.start_time))
    })
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # DONE: insert form data as a new Show record in the db, instead

  try:
    show = Show(  #Try to create a new Show object and add to the db
      venue_id = request.form['venue_id'],
      artist_id = request.form['artist_id'],
      start_time = request.form['start_time']
    )
    db.session.add(show)
    db.session.commit()
    # on successful db insert, flash success
    flash('Show was successfully listed!')
  except:
    # DONE: on unsuccessful db insert, flash an error instead.
    db.session.rollback()
    flash('An error occurred, the show could not be listed.')
    print(sys.exc_info())
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
