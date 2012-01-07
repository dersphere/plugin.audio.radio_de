from xbmcswift import Plugin, xbmc
import resources.lib.scraper as scraper

__addon_name__ = 'Radio.de'
__id__ = 'plugin.audio.radio_de'

plugin = Plugin(__addon_name__, __id__, __file__)


@plugin.route('/', default=True)
def show_root_menu():
    __log('show_root_menu start')
    items = []
    items.append({'label': plugin.get_string(30107),
                  'url': plugin.url_for('show_local_stations')})

    items.append({'label': plugin.get_string(30100),
                  'url': plugin.url_for('show_recommendation_stations')})

    items.append({'label': plugin.get_string(30101),
                  'url': plugin.url_for('show_top_stations')})

    items.append({'label': plugin.get_string(30102),
                  'url': plugin.url_for('show_station_category_types',
                                        category_type='genre')})

    items.append({'label': plugin.get_string(30103),
                  'url': plugin.url_for('show_station_category_types',
                                        category_type='topic')})

    items.append({'label': plugin.get_string(30104),
                  'url': plugin.url_for('show_station_category_types',
                                        category_type='country')})

    items.append({'label': plugin.get_string(30105),
                  'url': plugin.url_for('show_station_category_types',
                                        category_type='city')})

    items.append({'label': plugin.get_string(30106),
                  'url': plugin.url_for('show_station_category_types',
                                        category_type='language')})

    items.append({'label': plugin.get_string(30200),
                  'url': plugin.url_for('search')})

    __log('show_root_menu end')
    return plugin.add_items(items)


@plugin.route('/local_stations/')
def show_local_stations():
    __log('show_local_stations start')
    stations = scraper.get_most_wanted()
    items = _format_stations(stations['localBroadcasts'])
    __log('show_local_stations end')
    return plugin.add_items(items)


@plugin.route('/recommendation_stations/')
def show_recommendation_stations():
    __log('show_recommendation_stations start')
    stations = scraper.get_recommendation_stations()
    items = _format_stations(stations)
    __log('show_root_menu end')
    return plugin.add_items(items)


@plugin.route('/top_stations/')
def show_top_stations():
    __log('show_top_stations start')
    stations = scraper.get_top_stations()
    items = _format_stations(stations)
    __log('show_root_menu end')
    return plugin.add_items(items)


@plugin.route('/stations_by_category/<category_type>')
def show_station_category_types(category_type):
    __log('show_station_category_types started with category_type=%s'
          % category_type)
    categories = scraper.get_categories_by_category_type(category_type)
    items = []
    for category in categories:
        category = category.encode('utf-8')
        try:
            items.append({'label': category,
                          'url': plugin.url_for('show_stations_by_category',
                                                category_type=category_type,
                                                category=category)})
        except:
            __log('show_station_category_types EXCEPTION: %s' % repr(category))
    __log('show_root_menu end')
    return plugin.add_items(items)


@plugin.route('/stations_by_category/<category_type>/<category>/')
def show_stations_by_category(category_type, category):
    __log(('show_stations_by_category started with '
           'category_type=%s, category=%s') % (category_type, category))
    stations = scraper.get_stations_by_category(category_type, category)
    items = _format_stations(stations)
    __log('show_root_menu end')
    return plugin.add_items(items)


@plugin.route('/search_station/')
def search():
    __log('search start')
    search_string = None
    keyboard = xbmc.Keyboard('', plugin.get_string(30201))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        search_string = keyboard.getText().decode('utf8')
        __log('search gots a string: "%s"' % search_string)
        stations = scraper.search_stations_by_string(search_string)
        items = _format_stations(stations)
        __log('search end')
        return plugin.add_items(items)


@plugin.route('/stream/<id>/')
def stream(id):
    __log('stream started with id=%s' % id)
    station = scraper.get_station_by_station_id(id)
    stream_url = station['streamURL']  # fixme: need to resolve .pls at least
    __log('stream end with stream_url=%s' % stream_url)
    return plugin.set_resolved_url(stream_url)


def _format_stations(stations):
    __log('_format_stations start')
    items = [{'label': station['name'],
              'thumbnail': station['pictureBaseURL'] + station['picture1Name'],
              'info': {'originaltitle': '',
                       'rating': float(station['rating']),
                       'genre': station['genresAndTopics']},
              'url': plugin.url_for('stream', id=str(station['id'])),
              'is_folder': False,
              'is_playable': True,
             } for station in stations]
    __log('_format_stations end')
    return items


def __log(text):
    xbmc.log('%s addon: %s' % (__addon_name__, text))

if __name__ == '__main__':
    plugin.run()
