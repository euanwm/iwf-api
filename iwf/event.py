from typing import Union

import requests

from bs4 import BeautifulSoup

from .core import eBase, eHeaders, eEvents, is_event, eCatYears


class Event(object):
    def __init__(self, keywords=[], *args):
        self.keywords = keywords

    @staticmethod
    def _craft_url(old_bw_cat=False, year=None, nation=None, event_type=None, age_group=None) -> str:
        """Generates the URL required to pull the events list"""
        filters = []
        if old_bw_cat:
            search_url = eBase.URL + eEvents.OLD_BW_URL
        else:
            search_url = eBase.URL + eEvents.URL

        # TODO: Combine years results with other filters
        if year:
            search_url += eEvents.YEAR_URL + year
        else:
            if event_type:
                if " " in event_type:
                    event_type_new = event_type.replace(" ", "+")
                    filters.append(eEvents.TYPE_URL + event_type_new)
            if age_group:
                filters.append(eEvents.AGE_URL + age_group)
            if nation:
                filters.append(eEvents.NATION_URL + nation)

        if len(filters) >= 1:
            search_url += "/?" + filters[0]
            for i in range(1, len(filters)):
                search_url += "&" + filters[i]
        return search_url

    def __load_event_page(self, search_url=None, old_bw_cat=False, year=None, nation=None, event_type=None,
                          age_group=None) -> BeautifulSoup:
        """Loads the event page results"""
        if search_url and is_event(search_url):
            r = requests.get(search_url, headers=eHeaders.PAYLOAD)
        else:
            new_url = self._craft_url(old_bw_cat, year, nation, event_type, age_group)
            r = requests.get(new_url, headers=eHeaders.PAYLOAD)

        html = r.text
        return BeautifulSoup(html, "lxml")

    @staticmethod
    def __scrape_event_info(soup_data) -> list[dict]:
        """Parses page data into a list of dicts"""
        result = []
        cards = soup_data.findAll("a", {"class": "card"})
        for card in cards:
            data = {}
            data["name"] = card.find("span", {"class": "text"}).string
            data["result_url"] = card["href"]
            data["location"] = card.find("strong").string
            data["date"] = card.find("p", {"class": "normal__text"}).string.strip()
            result.append(data)
        return result

    def get_events(self, search_url=None, year=None, old_bw_cat=False, nation=None, event_type=None,
                   age_group=None) -> list[dict]:
        """Fetches events list based upon the specified filters"""
        event_page_data = self.__load_event_page(search_url, old_bw_cat, year, nation, event_type, age_group)
        result_data = self.__scrape_event_info(event_page_data)
        if result_data:
            return result_data

    def get_events_by_year(self, year: Union[int, str]) -> list[dict]:
        """Simplified function to fetch results by year"""
        if int(year) <= eCatYears.OLD_BW_CAT:
            event_page_data = self.__load_event_page(year=str(year), old_bw_cat=True)
            result_data = self.__scrape_event_info(event_page_data)
        elif int(year) >= eCatYears.NEW_BW_CAT:
            event_page_data = self.__load_event_page(year=str(year), old_bw_cat=True)
            result_data = self.__scrape_event_info(event_page_data)
        elif int(year) == eCatYears.MIXED_CAT_YEAR:
            old_bw_event_page_data = self.__load_event_page(year=str(year), old_bw_cat=True)
            old_bw_result_data = self.__scrape_event_info(old_bw_event_page_data)
            event_page_data = self.__load_event_page(year=str(year), old_bw_cat=False)
            result_data = self.__scrape_event_info(event_page_data)
            combined_data = old_bw_result_data + result_data
            return combined_data
        if result_data:
            return result_data
