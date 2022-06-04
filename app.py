#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import FlaskForm, Form
from sqlalchemy import false
from forms import *
from flask_migrate import Migrate
from models import Show, Venue, Artist, app, db
import json
import os
from datetime import datetime
from sqlalchemy.exc import IntegrityError
import jinja2


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  data=[]
  info=[]
  try:
    artist_detail = Artist.query.order_by(db.desc('id')).limit(10).all() 
    for show in artist_detail:
      artists = {}
      artists['artist_id'] = show.id
      artists['artist_name'] = show.name
      artists['artist_image_link'] = show.image_link
      data.append(artists)

    venue_detail = Venue.query.order_by(db.desc('id')).limit(10).all() 
    for show in venue_detail:
      venues = {}
      venues['venue_id'] = show.id
      venues['venue_name'] = show.name
      venues['venue_image_link'] = show.image_link
      info.append(venues) 
    print(data)
  except:
    abort(500)

  finally:
    return render_template('pages/home.html', artist=data, venue=info)

#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  data = []
  location = Venue.query.distinct(Venue.city, Venue.state).all()
  time_now =datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  try:
    for address in location:
      place={}
      venues = []
      place['city']=address.city
      place['state']=address.state
      venue_set = Venue.query.filter(
        Venue.city == address.city,
        Venue.state == address.state
      ).all()
      for venue in venue_set:
        details = {}
        details['id'] = venue.id
        details['name'] = venue.name
        details['num_upcoming shows'] = Show.query.join(Venue, Artist).filter(
          db.and_(
          Show.show_time > time_now,
          Show.venue_id == venue.id
          )).count()
        venues.append(details)
      place['venues'] = venues
      data.append(place)
      print(data)

  except:      
    flash("Sorry, we are unable to play the venues page")
    
  finally:
    return render_template('pages/venues.html', areas=data)
    

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  response = {}
  time_now =datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  try:
    search = request.form['search_term']
    if request.form['search_by'] == 'city':
      search_result = Venue.query.filter(Venue.city.ilike("%" + search + "%")).order_by('city').all()
    elif request.form['search_by'] == 'state':
       search_result = Venue.query.filter(Venue.state.ilike("%" + search + "%")).order_by('state').all()
    elif request.form['search_by'] == 'name':
      search_result = Venue.query.filter(Venue.name.ilike("%" + search + "%")).order_by('name').all()
    else:
      flash("Sorry, an error occurred")
    response['count'] = len(search_result)
    data = []
    for venue_details in search_result:
      details = {}
      details['id'] = venue_details.id
      details['name'] = venue_details.name
      details['num_upcoming_shows'] = Show.query.join(Venue, Artist).filter(
        db.and_(
        Show.show_time > time_now,
        Show.venue_id == venue_details.id
        )).count()
      data.append(details)
      response['data'] = data  
  except:
      flash("Sorry, An error occured")    
      abort(500)
  
  finally:
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

  

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  if Venue.query.filter(Venue.id == venue_id).count() == 0:
    flash("Venue of ID " + str(venue_id) + " does not exist" )
    abort(404)
    
  else:
    try:
      data={}
      time_now =datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      venue_detail = Venue.query.filter(Venue.id == venue_id).first()
      data['id'] = venue_detail.id
      data['name'] = venue_detail.name
      data['city'] = venue_detail.city
      data['state'] = venue_detail.state
      data['address'] = venue_detail.address
      data['phone'] = venue_detail.phone
      data['genres'] = venue_detail.genres
      data['image_link'] = venue_detail.image_link
      data['website'] = venue_detail.website_link
      data['facebook_link'] = venue_detail.facebook_link
      data['seeking_talent'] = venue_detail.seeking_talent
      data['seeking_description'] = venue_detail.seeking_description

      past_shows = []
      upcoming_shows = []

      past_show = Show.query.join(Artist, Venue).filter(
        db.and_(
          Show.show_time < time_now,
          Show.venue_id == venue_id
          )).all()
      for show in past_show:
        previous_show = {}
        previous_show['artist_id'] = show.artist_id
        previous_show['artist_name'] = show.artist.name
        previous_show['artist_image_link'] = show.artist.image_link
        previous_show['start_time'] = str(show.show_time)
        past_shows.append(previous_show)

      upcoming_show = Show.query.join(Artist, Venue).filter(
        db.and_(
          Show.show_time > time_now,
          Show.venue_id == venue_id
        )).all()
      for show in upcoming_show:
        pending_shows = {}
        pending_shows['artist_id'] = show.artist_id
        pending_shows['artist_name'] = show.artist.name
        pending_shows['artist_image_link'] = show.artist.image_link
        pending_shows['start_time'] = str(show.show_time)
        upcoming_shows.append(pending_shows) 
      
      data['past_shows'] = past_shows
      data['past_shows_count'] = len(past_shows)
      data['upcoming_shows'] = upcoming_shows
      data['upcoming_shows_count'] = len(upcoming_shows)
    
    except:
      flash("An error occured")
      abort(500)

    finally: 
      return render_template('pages/show_venue.html', venue=data)
      

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  # on successful db insert, flash success
  # flash('Venue ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  try:
    form = VenueForm(request.form)
    venue = Venue(
    name = form.name.data,
    city = form.city.data,
    state = form.state.data,
    address = form.address.data,
    phone = form.phone.data,
    image_link = form.image_link.data,
    genres = form.genres.data,
    facebook_link = form.facebook_link.data,
    website_link = form.website_link.data,
    seeking_talent = form.seeking_talent.data,
    seeking_description = form.seeking_description.data
    )
    db.session.add(venue)
    db.session.commit()
    flash( form.name.data + ' venue was successfully listed!')

  except:
    flash(form.name.data + " venue could not be added. It already exists.")
    db.session.rollback()
  
  finally:
    db.session.close()
    return render_template('pages/home.html')

  
@app.route('/venues<int:venue_id>/delete')
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # # clicking that button delete it from the db then redirect the user to the homepage
  #
  error = False
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
    flash("Venue deleted succesfully")
    
  except:
    error = True
    db.session.rollback()
    flash("An error occured. The venue could not be deleted")
    
  finally:
    db.session.close()
  if error:
    abort(500)
  else:
    return redirect(url_for('index'))


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  try:
    details = Artist.query.all()
    data = []
    for artist in details:
      details = {}
      details['id'] = artist.id
      details['name'] = artist.name
      data.append(details)

  except:
    flash("Sorry, we are unable to display this page")    
    abort(500)

  finally:
    return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  response = {}
  time_now =datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  try:
    search = request.form['search_term']
    if request.form['search_by'] == 'city':
      search_result = Artist.query.filter(Artist.city.ilike("%" + search + "%")).order_by('city').all()
    elif request.form['search_by'] == 'state':
       search_result = Artist.query.filter(Artist.state.ilike("%" + search + "%")).order_by('state').all()
    elif request.form['search_by'] == 'name':
      search_result = Artist.query.filter(Artist.name.ilike("%" + search + "%")).order_by('name').all()
    else:
      flash("Sorry, an error occurred")
    response['count'] = len(search_result)
    data = []
    for artist_details in search_result:
      details = {}
      details['id'] = artist_details.id
      details['name'] = artist_details.name
      details['num_upcoming_shows'] = Show.query.join(Venue, Artist).filter(
        db.and_(
        Show.show_time > time_now,
        Show.artist_id == artist_details.id
        )).count()
      data.append(details)
      response['data'] = data  
  except:
      flash("Sorry, An error occured")    
      abort(500)
  
  finally:
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  if Artist.query.filter(Artist.id == artist_id).count() == 0:
    flash("Artist of ID " + str(artist_id) + " does not exist" )
    abort(404)
    
  else:  
    try:
      data={}
      time_now =datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      artist_detail = Artist.query.filter(Artist.id == artist_id).first()
      data['id'] = artist_detail.id
      data['name'] = artist_detail.name
      data['city'] = artist_detail.city
      data['state'] = artist_detail.state
      data['phone'] = artist_detail.phone
      data['genres'] = artist_detail.genres
      data['image_link'] = artist_detail.image_link
      data['website'] = artist_detail.website_link
      data['facebook_link'] = artist_detail.facebook_link
      data['seeking_venue'] = artist_detail.seeking_venue
      data['seeking_description'] = artist_detail.seeking_description

      past_shows = []
      upcoming_shows = []

      past_show = Show.query.join(Venue, Artist).filter(
        db.and_(
          Show.show_time < time_now,
          Show.artist_id == artist_id
          )).all()
      for show in past_show:
        previous_show = {}
        previous_show['venue_id'] = show.venue_id
        previous_show['venue_name'] = show.venue.name
        previous_show['venue_image_link'] = show.venue.image_link
        previous_show['start_time'] = str(show.show_time)
        past_shows.append(previous_show)

      upcoming_show = Show.query.join(Artist, Venue).filter(
        db.and_(
          Show.show_time > time_now,
          Show.artist_id == artist_id
        )).all()
      for show in upcoming_show:
        pending_shows = {}
        pending_shows['venue_id'] = show.venue_id
        pending_shows['venue_name'] = show.venue.name
        pending_shows['venue_image_link'] = show.venue.image_link
        pending_shows['start_time'] = str(show.show_time)
        upcoming_shows.append(pending_shows) 
      
      data['past_shows'] = past_shows
      data['past_shows_count'] = len(past_shows)
      data['upcoming_shows'] = upcoming_shows
      data['upcoming_shows_count'] = len(upcoming_shows)
      #print(data)
    
    except:
      flash("An error occured")
      abort(500)

    finally: 
      return render_template('pages/show_artist.html', artist=data)
      

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.filter(Artist.id == artist_id).first()
  form = ArtistForm(
    name = artist.name,
    city = artist.city,
    state = artist.state,
    phone = artist.phone,
    image_link = artist.image_link,
    genres = artist.genres,
    facebook_link = artist.facebook_link,
    website = artist.website_link,
    seeking_venue = artist.seeking_venue,
    seeking_description = artist.seeking_description 
  )

  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  form = ArtistForm(request.form)
  if form.validate():
    try:
      data = Artist.query.filter(Artist.id == artist_id).first()
      data.name = form.name.data
      data.city = form.city.data
      data.state = form.state.data
      data.phone = form.phone.data
      data.image_link = form.image_link.data
      data.genres = form.genres.data
      data.facebook_link = form.facebook_link.data
      data.website_link = form.website_link.data
      data.seeking_venue = form.seeking_venue.data 
      data.seeking_description = form.seeking_description.data 
      db.session.commit()
      flash(form.name.data + ' has been successfully updated!')

    except:
      flash('An error occurred. Artist ' + form.name.data + ' could not be updated.')
      db.session.rollback()
      abort(500)

    finally:
      db.session.close()  
      

  else:
    flash("error")

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.filter(Venue.id == venue_id).first()
  form = VenueForm(
    name = venue.name,
    city = venue.city,
    state = venue.state,
    phone = venue.phone,
    address = venue.address,
    image_link = venue.image_link,
    genres = venue.genres,
    facebook_link = venue.facebook_link,
    website_link = venue.website_link,
    seeking_talent = venue.seeking_talent,
    seeking_description = venue.seeking_description 
  )
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  #return redirect(url_for('show_venue', venue_id=venue_id))
  form = VenueForm(request.form)
  try:
    data = Venue.query.filter(Venue.id == venue_id).first()

    data.name = form.name.data
    data.city = form.city.data
    data.state = form.state.data
    data.phone = form.phone.data
    data.image_link = form.image_link.data
    data.genres = form.genres.data
    data.address = form.address.data
    data.facebook_link = form.facebook_link.data
    data.website_link = form.website_link.data
    data.seeking_talent = form.seeking_talent.data
    data.seeking_description = form.seeking_description.data 
    db.session.commit()
    flash(form.name.data + ' has been successfully updated!')

  except:
    flash('An error occurred. Venue ' + form.name.data + ' could not be updated.')
    db.session.rollback()

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
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  try:
    form = ArtistForm(request.form)

    artist = Artist(
    name = form.name.data,
    city = form.city.data,
    state = form.state.data,
    phone = form.phone.data,
    image_link = form.image_link.data,
    genres = form.genres.data,
    facebook_link = form.facebook_link.data,
    website_link = form.website_link.data,
    seeking_venue = form.seeking_venue.data,
    seeking_description = form.seeking_description.data
    )
    db.session.add(artist)
    db.session.commit()
    # on successful db insert, flash success
    flash('Artist ' + form.name.data + ' was successfully listed!')

  except:
    flash(form.name.data + " could not be added. It already exists.")
    db.session.rollback()
    #abort(500)
  
  finally:
    db.session.close()
    return render_template('pages/home.html')

  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')

@app.route('/artists<int:artist_id>/delete')
def delete_artist(artist_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # # clicking that button delete it from the db then redirect the user to the homepage
  #
  error = False
  try:
    artist = Artist.query.get(artist_id)
    db.session.delete(artist)
    db.session.commit()
    flash("Artist deleted succesfully")
    
  except:
    error = True
    db.session.rollback()
    flash("An error occured. The artist could not be deleted")
    
  finally:
    db.session.close()
  if error:
    abort(500)
  else:
    return redirect(url_for('index'))



#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
    data = [] 
    try:
      performance = Show.query.join(Artist, Venue)
      for show in performance:
        details = {}
        details['venue_id'] = show.venue_id
        details['venue_name'] = show.venue.name
        details['artist_id'] = show.artist_id
        details['artist_image_link'] = show.artist.image_link
        details['start_time'] = str(show.show_time)
        data.append(details)
        
    except:
      flash("Sorry, we are unable to display this page")    

    finally:
      return render_template('pages/shows.html', shows=data)
  

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  try:
    form = ShowForm(request.form)
    show = Show(
    artist_id = form.artist_id.data,
    venue_id = form.venue_id.data,
    show_time = form.start_time.data
    )
    db.session.add(show)
    db.session.commit()
    # on successful db insert, flash success
    flash('Show was successfully listed!')

  except IntegrityError:
    db.session.rollback()
    flash('Invalid Artist ID or Venue ID')

  except:
    db.session.rollback()
    flash('An error occurred. Show could not be listed.')
  
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
'''
if __name__ == '__main__':
    app.run()
'''


# Or specify port manually:
if __name__ == '__main__':
    app.debug = True
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)