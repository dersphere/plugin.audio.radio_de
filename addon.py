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
from xbmcswift2 import Plugin, xbmc

from resources.lib.api import RadioApi, RadioApiError
from resources.lib.file_manager import FileManager

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
    'edit_custom_station': 30402,
    'please_enter': 30500,
    'name': 30501,
    'thumbnail': 30502,
    'stream_url': 30503,
    'add_custom': 30504
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
    return __add_stations(stations)


@plugin.route('/recommendation_stations/')
def show_recommendation_stations():
    stations = radio_api.get_recommendation_stations()
    return __add_stations(stations)


@plugin.route('/top_stations/')
def show_top_stations():
    stations = radio_api.get_top_stations()
    return __add_stations(stations)


@plugin.route('/stations_by_category/<category_type>/')
def show_station_categories(category_type):
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
    stations = radio_api.get_stations_by_category(category_type,
                                                  category)
    return __add_stations(stations)


@plugin.route('/search_station/')
def search():
    search_string = __keyboard(_('enter_name_country_or_language'))
    if search_string:
        url = plugin.url_for('search_result', search_string=search_string)
        plugin.redirect(url)


@plugin.route('/search_station/<search_string>')
def search_result(search_string):
    stations = radio_api.search_stations_by_string(search_string)
    return __add_stations(stations)


@plugin.route('/my_stations/')
def show_mystations():
    stations = my_stations_manager.list_elements().values()
    return __add_stations(stations, add_custom=True)


@plugin.route('/my_stations/custom/<station_id>')
def custom_mystation(station_id):
    if station_id == 'new':
        station = {}
    else:
        stations = my_stations_manager.list_elements().values()
        station = [s for s in stations if s['id'] == station_id][0]
    for param in ('name', 'thumbnail', 'stream_url'):
        heading = _('please_enter') % _(param)
        station[param] = __keyboard(heading, station.get(param, '')) or ''
    station_id = station['id'] = station.get('name', 'custom')
    station['is_custom'] = True
    if station_id:
        my_stations_manager.add_element(station_id, station)
        url = plugin.url_for('show_mystations')
        plugin.redirect(url)


@plugin.route('/my_stations/add/<station_id>')
def add_station_mystations(station_id):
    station = radio_api.get_station_by_station_id(station_id)
    my_stations_manager.add_element(station_id, station)


@plugin.route('/my_stations/del/<station_id>')
def del_station_mystations(station_id):
    my_stations_manager.del_element(station_id)


@plugin.route('/station/<station_id>')
def get_stream(station_id):
    my_stations = my_stations_manager.list_elements()
    if my_stations.get(station_id, {}).get('is_custom', False):
        stream_url = my_stations[station_id]['stream_url']
    else:
        station = radio_api.get_station_by_station_id(station_id)
        stream_url = station['stream_url']
    __log('get_stream result: %s' % stream_url)
    return plugin.set_resolved_url(stream_url)


def __keyboard(title, text=''):
    keyboard = xbmc.Keyboard(text, title)
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        return keyboard.getText()


def __add_stations(stations, add_custom=False):
    __log('__add_stations started with %d items' % len(stations))
    items = []
    my_station_ids = my_stations_manager.list_elements().keys()
    for station in stations:
        station_id = str(station['id'])
        if not station_id in my_station_ids:
            context_menu = [(
                _('add_to_my_stations'),
                'XBMC.RunPlugin(%s)' % plugin.url_for('add_station_mystations',
                                                      station_id=station_id),
            )]
        else:
            context_menu = [(
                _('remove_from_my_stations'),
                'XBMC.RunPlugin(%s)' % plugin.url_for('del_station_mystations',
                                                      station_id=station_id),
            )]
        if station.get('is_custom', False):
            context_menu.append((
                _('edit_custom_station'),
                'XBMC.RunPlugin(%s)' % plugin.url_for('custom_mystation',
                                                      station_id=station_id),
            ))
        items.append({
            'label': station.get('name', 'UNKNOWN'),
            'thumbnail': station.get('thumbnail', 'UNKNOWN'),
            'info': {
                'title': station.get('name', 'UNKNOWN'),
                'rating': float(station.get('rating', 0)),
                'genre': station.get('genres', ''),
                'size': station.get('bitrate', 0),
                'tracknumber': station.get(station['id'], 0),
                'comment': station.get('current_track', ''),
            },
            'context_menu': context_menu,
            'path': plugin.url_for(
                'get_stream',
                station_id=station_id,
            ),
            'is_playable': True,
        })
    if add_custom:
        items.append({
            'label': _('add_custom'),
            'path': plugin.url_for('custom_mystation', station_id='new'),
        })
    if plugin.get_setting('force_viewmode') == 'true':
        return plugin.finish(items, view_mode='thumbnail')
    else:
        return plugin.finish(items)


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


def __log(text):
    xbmc.log('%s plugin: %s' % (__addon_name__, repr(text)))


def __log_api(text):
    xbmc.log('%s api: %s' % (__addon_name__, repr(text)))


def __log_ms(text):
    xbmc.log('%s mystations: %s' % (__addon_name__, repr(text)))


def _(string_id):
    if string_id in STRINGS:
        return plugin.get_string(STRINGS[string_id])
    else:
        __log('String is missing: %s' % string_id)
        return string_id

if __name__ == '__main__':
    language = __get_language()
    profile_path = xbmc.translatePath(plugin._addon.getAddonInfo('profile'))
    user_agent = 'XBMC Addon Radio'
    my_stations_manager = FileManager(profile_path, 'mystations2.json')
    my_stations_manager.log = __log_ms
    radio_api = RadioApi(language=language, user_agent=user_agent)
    radio_api.log = __log_api
    try:
        plugin.run()
    except RadioApiError:
        __log('ERROR!!!!')
