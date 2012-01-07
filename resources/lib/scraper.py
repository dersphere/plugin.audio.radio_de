#!/usr/bin/python

import simplejson as json
from urllib import urlencode
from urllib2 import urlopen, Request

MAIN_URL = 'http://radio.de/info'
USER_AGENT = 'radio.de 1.9.1 rv:37 (iPhone; iPhone OS 5.0; de_DE)'
VALID_CATEGORY_TYPES = ('genre', 'topic', 'country', 'city', 'language')


def get_recommendation_stations():
    """returns a list of 11 editor recommended stations"""
    __log('get_recommendation_stations start')
    path = 'broadcast/editorialreccomendationsembedded'
    gets = {}
    stations = __get_json(path, gets)
    __log('get_recommendation_stations end')
    return stations


def get_top_stations():
    """returns a list of the 100 most listened radio stations"""
    __log('get_top_stations started')
    path = 'menu/broadcastsofcategory'
    gets = {'category': '_top'}
    stations = __get_json(path, gets)
    __log('get_top_stations end')
    return stations


def get_most_wanted(num_entries=25):
    __log('get_most_wanted started with num_entries=%d' % num_entries)
    path = 'account/getmostwantedbroadcastlists'
    gets = {'sizeoflists': num_entries}
    stations_lists = __get_json(path, gets)
    # stations_lists['topBroadcasts']
    # stations_lists['bookmarkedBroadcasts']
    # stations_lists['recommendedBroadcasts']
    # stations_lists['localBroadcasts']
    # stations_lists['historyBroadcasts']
    __log('get_most_wanted end')
    return stations_lists


def get_category_types():
    """returns a list of possible values of category_types for
    get_categories_by_category_type(category_type)
    and get_stations_by_category(category_type, category_value)
    """
    __log('get_category_types end')
    return VALID_CATEGORY_TYPES


def get_categories_by_category_type(category_type):
    """returns a list of possible values of category for a given category_type
    usable for get_stations_by_category(category_type, category)
    """
    __log('get_categories_by_category_type started with category_type=%s'
          % category_type)
    path = 'menu/valuesofcategory'
    if not category_type in get_category_types():
        raise
    gets = {'category': '_%s' % category_type}
    categories = __get_json(path, gets)
    __log('get_categories_by_category_type end')
    return categories


def get_stations_by_category(category_type, category_value):
    """returns a list of stations for a given category of category_type"""
    __log(('get_stations_by_category started with category_type=%s,'
           'category_value=%s') % (category_type, category_value))
    path = 'menu/broadcastsofcategory'
    if not category_type in get_category_types():
        raise
    if not category_value:
        raise
    gets = {'category': '_%s' % category_type,
            'value': category_value}
    stations = __get_json(path, gets)
    __log('get_stations_by_category end')
    return stations


def search_stations_by_string(search_string):
    """returns a list of stations for a given search_string.
    search in genresAndTopics, name, country"""
    __log('search_stations_by_string started with search_string=%s'
          % search_string)
    path = 'index/searchembeddedbroadcast'
    if not search_string:
        raise
    gets = {'q': search_string,
            'start': 0,
            'rows': 10000}
    stations = __get_json(path, gets)
    __log('search_stations_by_string started')
    return stations


def get_station_by_station_id(station_id):
    """returns detailed informations (including stream url) of a given station
    by station_id
    """
    __log('get_station_by_station_id started with station_id=%s' % station_id)
    path = 'broadcast/getbroadcastembedded'
    if not station_id:
        raise
    gets = {'broadcast': station_id}
    station = __get_json(path, gets)
    __log('get_station_by_station_id end')
    return station


def __get_json(path, gets=None, posts=None):
    __log('__get_json started with path=%s, gets=%s, posts=%s'
          % (path, gets, posts))
    if gets:
        full_url = '%s/%s?%s' % (MAIN_URL, path, urlencode(gets))
    else:
        full_url = '%s/%s' % (MAIN_URL, path)
    if posts:
        req = Request(full_url, urlencode(posts))
    else:
        req = Request(full_url)
    req.add_header('User-Agent', USER_AGENT)
    __log('__get_json opening url=%s' % full_url)
    response = urlopen(req).read()
    __log('__get_json ended with %d bytes result' % len(response))
    return json.loads(response)


def __log(text):
    print 'Radio.de scraper: %s' % text
