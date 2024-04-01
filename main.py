import requests
import datetime
import gettext
import os

from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.OpenUrlAction import OpenUrlAction

def gen_url(cityID):
    base_url = "https://openweathermap.org/city/"
    return base_url + str(cityID)

class WeatherExtension(Extension):
    def __init__(self):
        super(WeatherExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())

class KeywordQueryEventListener(EventListener):
    def add_current_weather(self, items, city):
        r = requests.get("https://api.openweathermap.org/data/2.5/weather?q=" + city +
                         "&APPID=" + self.apikey + "&units=" + self.units + "&lang=" + self.language)
        data_string = r.json()

        if 'weather' not in data_string:
            items.append(ExtensionResultItem(icon='images/error.png',
                                             name='Weather information not available',
                                             description=f'Weather information for {city.title()} is not available'))
            return

        weather = data_string["weather"][0]["description"]
        icon = data_string["weather"][0]["icon"]
        temp = data_string["main"]["temp"]
        press = data_string["main"]["pressure"]
        hum = data_string["main"]["humidity"]
        wind = data_string["wind"]["speed"]
        cloud = data_string["clouds"]["all"]
        cityID = data_string["id"]

        items.append(ExtensionResultItem(icon='images/'+icon[0:2]+'d.png',
                                         name='%s: %s, %s %s' % (
                                             city.title(), weather.title(), str(temp), self.temp_symbol),
                                         description=self.translator(
                                             "Pressure: %s Pa), (Humidity: %s%%), (Wind: %s m/s), (Cloudiness): %s%%") % (press, hum, wind, cloud),
                                         on_enter=OpenUrlAction(gen_url(cityID))))

    def on_event(self, event, extension):
        items = []
        self.apikey = extension.preferences["api_key"].strip()
        self.units = extension.preferences["units"]
        self.language = extension.preferences["language"]
        self.temp_symbol = f'{chr(176)}C' if self.units == 'metric' else f'{chr(176)}F'
        predef_cities = extension.preferences["predef_cities"].split(";")

        localedir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'locales')
        translator = gettext.translation('base', localedir=localedir, languages=[self.language])
        self.translator = translator.gettext

        city = event.get_argument()

        if city:
            self.add_current_weather(items, city)
        else:
            for iterCity in predef_cities:
                self.add_current_weather(items, iterCity)

        return RenderResultListAction(items)

if __name__ == '__main__':
    WeatherExtension().run()