#!/usr/bin/env python
"""Google Earth Engine python code for the SERVIR-Mekong Surface ecodash Tool"""

# This script handles the loading of the web application and its timeout settings,
# as well as the complete Earth Engine code for all the calculations.

import json
import os

import config
import ee
import jinja2
import webapp2

import socket

from google.appengine.api import urlfetch

###############################################################################
#                               Initialization.                               #
###############################################################################

# Memcache is used to avoid exceeding our EE quota. Entries in the cache expire
# 24 hours after they are added. See:
# https://cloud.google.com/appengine/docs/python/memcache/
MEMCACHE_EXPIRATION = 60 * 60 * 24


# The URL fetch timeout time (seconds).
URL_FETCH_TIMEOUT = 120

WIKI_URL = ""

# Create the Jinja templating system we use to dynamically generate HTML. See:
# http://jinja.pocoo.org/docs/dev/
JINJA2_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    autoescape=True,
    extensions=['jinja2.ext.autoescape'])

ee.Initialize(config.EE_CREDENTIALS)

ee.data.setDeadline(URL_FETCH_TIMEOUT)
socket.setdefaulttimeout(URL_FETCH_TIMEOUT)
urlfetch.set_default_fetch_deadline(URL_FETCH_TIMEOUT)

# set the collection ID
# net primary produciion
IMAGE_COLLECTION = ee.ImageCollection('JRC/GSW1_0/MonthlyHistory')

start = '2000-01-01'
end = '2012-12-31'


# Define country names
country_names = ['Myanmar (Burma)', 'Thailand', 'Laos', 'Vietnam', 'Cambodia']; 
# import the country feasture collection
countries = ee.FeatureCollection('ft:1tdSwUL7MVpOauSgRzqVTOwdfy17KDbw-1d9omPw');
# find the countries in the country list
mekongCountries = countries.filter(ee.Filter.inList('Country', country_names));
# Get the geometry of the countries
mekongRegion = mekongCountries.geometry()

###############################################################################
#                             Web request handlers.                           #
###############################################################################

class MainHandler(webapp2.RequestHandler):
    """A servlet to handle requests to load the main web page."""
    
    def get(self):
        mapid = updateMap(start, end)
        template_values = {
            'eeMapId': mapid['mapid'],
            'eeToken': mapid['token']
        }
        
        template = JINJA2_ENVIRONMENT.get_template('index.html')
        self.response.out.write(template.render(template_values))


class DetailsHandler(webapp2.RequestHandler):
    """A servlet to handle requests for details about a Polygon."""
  
    def get(self):
        """Returns details about a polygon."""
    
        start = self.request.get('refLow') + '-01-01'
        end = self.request.get('refHigh') + '-12-31'
        
        mapid = updateMap(start, end)
        
        template_values = {
            'eeMapId': mapid['mapid'],
            'eeToken': mapid['token']
            }
            
        JINJA2_ENVIRONMENT.get_template('index.html')
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(template_values))

# Download handler to download the map
# returns a url to download
class DownloadHandler(webapp2.RequestHandler):
    """A servlet to handle requests to load the main web page."""
    
    def get(self):
        
        poly = json.loads(unicode(self.request.get('polygon')))
        
        coords = []
        
        for items in poly:
            coords.append([items[0], items[1]])
        
        
        start = self.request.get('refLow') + '-01-01'
        end = self.request.get('refHigh') + '-12-31'
            
        
        print "========================================="
        print coords
        
        
        polygon = ee.FeatureCollection(ee.Geometry.Polygon(coords))
        
        downloadURL = downloadMap(polygon, coords, start, end)

        print downloadURL
        content = json.dumps(downloadURL) 
        
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(content)

    
# Define webapp2 routing from URL paths to web request handlers. See:
# http://webapp-improved.appspot.com/tutorials/quickstart.html
app = webapp2.WSGIApplication([
    ('/details', DetailsHandler),
    ('/downloadHandler', DownloadHandler),
    ('/', MainHandler),
    
])


###############################################################################
#                                   Helper Functions                          #
###############################################################################

def updateMap(startDate, endDate):


    myjrc = IMAGE_COLLECTION.filterBounds(mekongRegion).filterDate(startDate, endDate)
    
    # calculate total number of observations
    def calcObs(img):
        # observation is img > 0
        obs = img.gt(0);
        return ee.Image(obs).set('system:time_start', img.get('system:time_start'));  
    
    # calculate the number of times water
    def calcWater(img):
        water = img.select('water').eq(2);
        return ee.Image(water).set('system:time_start', img.get('system:time_start'));
        
    observations = myjrc.map(calcObs)
    
    water = myjrc.map(calcWater)
    
    # sum the totals
    totalObs = ee.Image(ee.ImageCollection(observations).sum().toFloat());
    totalWater = ee.Image(ee.ImageCollection(water).sum().toFloat());
    
    # calculate the percentage of total water
    returnTime = totalWater.divide(totalObs).multiply(100)
    
    # make a mask
    Mask = returnTime.gt(1)
    returnTime = returnTime.updateMask(Mask)
    
    # clip the result
    returnTime = returnTime.clip(mekongRegion)
    
    return returnTime.getMapId({
        'min': '0',
        'max': '100',
        'bands': 'water',
        'palette' : 'c10000,d742f4,001556,b7d2f7'
    })

  

# function to download the map
# returns a download url
def downloadMap(polygon, coords, startDate, endDate):

    
    myjrc = IMAGE_COLLECTION.filterBounds(mekongRegion).filterDate(startDate, endDate)
    
    # calculate total number of observations
    def calcObs(img):
        # observation is img > 0
        obs = img.gt(0);
        return ee.Image(obs).set('system:time_start', img.get('system:time_start'));  
    
    # calculate the number of times water
    def calcWater(img):
        water = img.select('water').eq(2);
        return ee.Image(water).set('system:time_start', img.get('system:time_start'));
        
    observations = myjrc.map(calcObs)
    
    water = myjrc.map(calcWater)
    
    # sum the totals
    totalObs = ee.Image(ee.ImageCollection(observations).sum().toFloat());
    totalWater = ee.Image(ee.ImageCollection(water).sum().toFloat());
    
    # calculate the percentage of total water
    returnTime = totalWater.divide(totalObs).multiply(100)
    
    # make a mask
    Mask = returnTime.gt(1)
    returnTime = returnTime.updateMask(Mask)
    
    # clip the result
    returnTime = returnTime.clip(polygon)
    
    return returnTime.getDownloadURL({
          'scale': 30,
          'crs': 'EPSG:4326',
          'region': coords
    })
