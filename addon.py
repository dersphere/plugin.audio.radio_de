#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2012 Tristan Fischer (sphere@dersphere.de)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
import os
import simplejson as json

from xbmcswift2 import Plugin, xbmc

from resources.lib.api import RadioApi, RadioApiError

__addon_name__ = 'Radio'
__id__ = 'plugin.audio.radio_de'

STRINGS = {
    'editorials_recommendations': 30100,
    'top_100_stations': 30101,
    'browse_by_genre': 30102,
    'browse_by_topic': 30103,
    'browse_by_country': 30104,
    'browse_by_city': 30105,
    'browse_by_language': 30106,
    'local_stations': 30107,
    'my_stations': 30108,
    'search_for_station': 30200,
    'enter_name_country_or_language': 30201,
    'add_to_my_stations': 30400,
    'remove_from_my_stations': 30401,
}


plugin = Plugin(__addon_name__, __id__, __file__)


@plugin.route('/')
def show_root_menu():
    items = (
        {'label': _('local_stations'),
         'path': plugin.url_for('show_local_stations')},
        {'label': _('editorials_recommendations'),
         'path': plugin.url_for('show_recommendation_stations')},
        {'label': _('top_100_stations'),
         'path': plugin.url_for('show_top_stations')},
        {'label': _('browse_by_genre'),
         'path': plugin.url_for('show_station_categories',
                                category_type='genre')},
        {'label': _('browse_by_topic'),
         'path': plugin.url_for('show_station_categories',
                                category_type='topic')},
        {'label': _('browse_by_country'),
         'path': plugin.url_for('show_station_categories',
                                category_type='country')},
        {'label': _('browse_by_city'),
         'path': plugin.url_for('show_station_categories',
                                category_type='city')},
        {'label': _('browse_by_language'),
         'path': plugin.url_for('show_station_categories',
                                category_type='language')},
        {'label': _('search_for_station'),
         'path': plugin.url_for('search')},
        {'label': _('my_stations'),
         'path': plugin.url_for('show_mystations')},
    )
    return plugin.finish(items)


@plugin.route('/local_stations/')
def show_local_stations():
    stations = radio_api.get_local_stations()
    items = __format_stations(stations)
    return plugin.finish(items)


@plugin.route('/recommendation_stations/')
def show_recommendation_stations():
    stations = radio_api.get_recommendation_stations()
    items = __format_stations(stations)
    return plugin.finish(items)


@plugin.route('/top_stations/')
def show_top_stations():
    stations = radio_api.get_top_stations()
    items = __format_stations(stations)
    return plugin.finish(items)


@plugin.route('/stations_by_category/<category_type>/')
def show_station_categories(category_type):
    __log('show_station_categories started with category_type=%s'
          % category_type)
    categories = radio_api.get_categories(category_type)
    items = []
    for category in categories:
        category = category.encode('utf-8')
        items.append({
            'label': category,
            'path': plugin.url_for(
                'show_stations_by_category',
                category_type=category_type,
                category=category,
            ),
        })
    return plugin.finish(items)


@plugin.route('/stations_by_category/<category_type>/<category>/')
def show_stations_by_category(category_type, category):
    __log(('show_stations_by_category started with '
           'category_type=%s, category=%s') % (category_type, category))
    stations = radio_api.get_stations_by_category(category_type,
                                                  category)
    items = __format_stations(stations)
    return plugin.finish(items)


@plugin.route('/search_station/')
def search():
    keyboard = xbmc.Keyboard('', _('enter_name_country_or_language'))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        search_string = keyboard.getText()
        url = plugin.url_for('search_result', search_string=search_string)
        plugin.redirect(url)


@plugin.route('/search_station/<search_string>')
def search_result(search_string):
    __log('search_result started with: %s' % search_string)
    stations = radio_api.search_stations_by_string(search_string)
    items = __format_stations(stations)
    return plugin.finish(items)


@plugin.route('/my_stations/')
def show_mystations():
    items = __format_stations([s['data'] for s in __get_my_stations()])
    return plugin.finish(items)


@plugin.route('/my_stations/add/<station_id>/')
def add_station_mystations(station_id):
    __log('add_station_mystations started with station_id=%s' % station_id)
    my_stations = __get_my_stations()
    if not station_id in [s['station_id'] for s in my_stations]:
        station = radio_api.get_station_by_station_id(station_id)
        my_stations.append({
            'station_id': station_id,
            'data': station,
        })
        __set_my_stations(my_stations)
    __log('add_station_mystations ended with %d items' % len(my_stations))


@plugin.route('/my_stations/del/<station_id>/')
def del_station_mystations(station_id):
    __log('del_station_mystations started with station_id=%s' % station_id)
    my_stations = __get_my_stations()
    if station_id in [s['station_id'] for s in my_stations]:
        my_stations = [s for s in my_stations if s['station_id'] != station_id]
        __set_my_stations(my_stations)
    __log('del_station_mystations ended with %d items' % len(my_stations))


@plugin.route('/station/<station_id>')
def get_stream(station_id):
    __log('get_stream started with station_id=%s' % station_id)
    station = radio_api.get_station_by_station_id(station_id)
    stream_url = station['streamURL'].strip()
    __log('get_stream end with stream_url=%s' % stream_url)
    return plugin.set_resolved_url(stream_url)


def __format_stations(stations):
    __log('__format_stations start')
    items = []
    my_station_ids = [s['station_id'] for s in __get_my_stations()]
    for station in stations:
        if not station:
            continue
        if station['picture1Name']:
            thumbnail = station['pictureBaseURL'] + station['picture1Name']
        else:
            __log('ERROR: Station has no thumb! %s' % station)
            thumbnail = ''
        if not 'genresAndTopics' in station:
            station['genresAndTopics'] = ','.join(station['genres']
                                                  + station['topics'])
        if not str(station['id']) in my_station_ids:
            my_station_label = _('add_to_my_stations')
            my_station_url = plugin.url_for(
                'add_station_mystations',
                station_id=str(station['id']),
            )
        else:
            my_station_label = _('remove_from_my_stations')
            my_station_url = plugin.url_for(
                'del_station_mystations',
                station_id=str(station['id']),
            )
        items.append({
            'label': station['name'],
            'thumbnail': __thumb(thumbnail),
            'info': {
                'Title': station['name'],
                'rating': float(station['rating']),
                'genre': station['genresAndTopics'],
                'Size': station['bitrate'],
                'tracknumber': station['id'],
                'comment': station['currentTrack'],
            },
            'context_menu': [(
                my_station_label,
                'XBMC.RunPlugin(%s)' % my_station_url,
            )],
            'path': plugin.url_for(
                'get_stream',
                station_id=str(station['id']),
            ),
            'is_playable': True,
        })
    return items


def __thumb(thumbnail):
    return thumbnail.replace('_1', '_4')


def __get_my_stations():
    __log('__get_my_stations start')
    __migrate_my_stations()
    my_stations = []
    profile_path = xbmc.translatePath(plugin._addon.getAddonInfo('profile'))
    ms_file = os.path.join(profile_path, 'mystations.json')
    if os.path.isfile(ms_file):
        my_stations = json.load(open(ms_file, 'r'))
    __log('__get_my_stations ended with %d items' % len(my_stations))
    return my_stations


def __set_my_stations(stations):
    __log('__set_my_stations start')
    profile_path = xbmc.translatePath(plugin._addon.getAddonInfo('profile'))
    if not os.path.isdir(profile_path):
        os.makedirs(profile_path)
    ms_file = os.path.join(profile_path, 'mystations.json')
    json.dump(stations, open(ms_file, 'w'), indent=1)


def __get_language():
    if not plugin.get_setting('not_first_run'):
        xbmc_language = xbmc.getLanguage().lower()
        __log('__get_language has first run with xbmc_language=%s'
              % xbmc_language)
        if xbmc_language.startswith('english'):
            plugin.set_setting('language', '0')
        elif xbmc_language.startswith('german'):
            plugin.set_setting('language', '1')
        elif xbmc_language.startswith('french'):
            plugin.set_setting('language', '2')
        else:
            plugin.open_settings()
        plugin.set_setting('not_first_run', '1')
    lang_id = plugin.get_setting('language')
    return ('english', 'german', 'french')[int(lang_id)]


def __migrate_my_stations():
    if not plugin.get_setting('my_stations'):
        __log('__migrate_my_stations nothing to migrate')
        return
    my_stations = plugin.get_setting('my_stations').split(',')
    __log('__migrate_my_stations start migration mystations: %s' % my_stations)
    stations = []
    for station_id in my_stations:
        station = radio_api.get_station_by_station_id(station_id)
        if station:
            stations.append({'station_id': station_id,
                             'data': station})
    __set_my_stations(stations)
    plugin.set_setting('my_stations', '')
    __log('__migrate_my_stations migration done')


def __log(text):
    xbmc.log('%s plugin: %s' % (__addon_name__, repr(text)))


def __log_api(text):
    xbmc.log('%s api: %s' % (__addon_name__, repr(text)))


def _(string_id):
    if string_id in STRINGS:
        return plugin.get_string(STRINGS[string_id])
    else:
        __log('String is missing: %s' % string_id)
        return string_id

if __name__ == '__main__':
    language = __get_language()
    radio_api = RadioApi(language=language)
    radio_api.log = __log_api
    try:
        plugin.run()
    except RadioApiError:
        __log('ERROR!!!!')
