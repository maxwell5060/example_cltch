import json
from functools import reduce
from urllib.parse import urlencode

import requests


class RequestError(BaseException):
    def __init__(self, message, *args: object) -> None:
        self.message = message
        super().__init__(message, *args)


class StatType:
    CALLS_TOTAL = 'callsTotal'
    CALLS_BY_DATE = 'callsByDate'
    CALLS_SEO_BY_DATE = 'callsByDateSeoOnly'
    CALLS_SEO_BY_KEYWORDS = 'callsByKeywords'


def i_len(iterable):
    return reduce(lambda s, element: s + 1, iterable, 0)


class CalltouchGrabber:
    def __init__(self, site_id: str, token: str):
        self.site_id = site_id
        self.token = token

        self.node = ''
        self.requests_url = ''
        self.orders_url = ''
        self.calls_url = ''

        self.calls_total_count_url = ''
        self.calls_count_by_date_url = ''
        self.calls_seo_count_by_date_url = ''
        self.calls_seo_count_by_keywords_url = ''

        self.stats_urls = {}

    def detect_node(self):
        response = requests.get(f'https://api.calltouch.ru/calls-service/RestAPI/{self.site_id}/getnodeid/')

        if response.status_code == 200:
            data = json.loads(response.text)
            self.node = f"https://api-node{data['nodeId']}.calltouch.ru"
        else:
            self.node = 'http://api.calltouch.ru'

        self.requests_url = f'{self.node}/calls-service/RestAPI/requests'
        self.orders_url = f'{self.node}/calls-service/RestAPI/{self.site_id}/orders-diary/orders'
        self.calls_url = f'{self.node}/calls-service/RestAPI/{self.site_id}/calls-diary/calls'

        stats_base_url = f'{self.node}/calls-service/RestAPI/statistics/{self.site_id}/calls'

        self.calls_total_count_url = f'{stats_base_url}/total-count'
        self.calls_count_by_date_url = f'{stats_base_url}/count-by-date'
        self.calls_seo_count_by_date_url = f'{stats_base_url}/seo/count-by-date'
        self.calls_seo_count_by_keywords_url = f'{stats_base_url}/seo/count-by-keywords'

        self.stats_urls = {
            StatType.CALLS_TOTAL: self.calls_total_count_url,
            StatType.CALLS_BY_DATE: self.calls_count_by_date_url,
            StatType.CALLS_SEO_BY_DATE: self.calls_seo_count_by_date_url,
            StatType.CALLS_SEO_BY_KEYWORDS: self.calls_seo_count_by_keywords_url
        }

    @staticmethod
    def get_data(query, url, stream: bool = False, as_json: bool = True):
        response = requests.get(f"{url}/?{query}", stream=stream)

        if response.status_code == 200:
            if as_json:
                return response.json()
            else:
                return response.content
        else:
            raise RequestError(f"Problem. Response code - {response.status_code}")

    def capture_requests(self, date_from, date_to):
        if not self.requests_url:
            self.detect_node()

        query = {
            'dateFrom': date_from,
            'dateTo': date_to,
            'clientApiId': self.token
        }
        query = urlencode(query)
        return self.get_data(query, self.requests_url)

    def capture_orders(self, date_from, date_to, page: int = 1):
        if not self.orders_url:
            self.detect_node()

        result = []

        query = {
            'dateFrom': date_from,
            'dateTo': date_to,
            'clientApiId': self.token,
            'page': page,
            'limit': 1000
        }
        query = urlencode(query)

        data = self.get_data(query, self.orders_url)
        result += data['records']

        if page < data['totalPage']:
            result += self.capture_orders(date_from, date_to, page=page + 1)

        return result

    @staticmethod
    def _prepare_calls(data, date_from):
        campaigns = {
            i['utmCampaign']: []
            for i in data
        }

        results = []

        for i in data:
            campaigns[i['utmCampaign']].append(i)

        for name, records in campaigns.items():
            result = {
                'name': name,
                'date': date_from,
                'source': records[0]['source'],
                'medium': records[0]['medium'],
                'ordinaryCalls': len(records),
                'callIDs': [record['callId'] for record in records],
                'uniqCalls': i_len(filter(lambda x: x['uniqueCall'] == 'True', records)),
                'targetCalls': i_len(filter(lambda x: x['targetCall'] == 'True', records)),
                'uniqTargetCalls': i_len(filter(lambda x: x['uniqTargetCall'] == 'True', records)),
            }
            results.append(result)

        return results

    def capture_calls(self, date_from, date_to, attribution: int = 0, raw: bool = False):
        if not self.calls_url:
            self.detect_node()

        query = {
            'clientApiId': self.token,
            'dateFrom': date_from,
            'dateTo': date_to,
            'attribution': attribution,
            'withYandexDirect': True,
            'withGoogleAdwords': True
        }
        query = urlencode(query)
        data = self.get_data(query, self.calls_url)

        if not raw:
            data = self._prepare_calls(data, date_from)

        return data

    def capture_audio_records(self, call_id):
        if not self.calls_url:
            self.detect_node()

        query = {'clientApiId': self.token}
        query = urlencode(query)
        url = f"{self.calls_url}/{call_id}/download"

        try:
            data = self.get_data(query, url, stream=True, as_json=False)

            with open(f'{call_id}_record.mp3', 'wb') as f:
                f.write(data)

            return {
                'status': True,
                'message': f'Call Record Saved as: {call_id}_record.mp3'
            }

        except RequestError as e:
            return {
                'status': False,
                'message': e.message
            }

    def capture_stats(self, date_from, date_to, stat_type: str = StatType.CALLS_TOTAL):
        if not self.stats_urls:
            self.detect_node()

        query = {
            'access_token': self.token,
            'dateFrom': date_from,
            'dateTo': date_to
        }
        query = urlencode(query)
        url = self.stats_urls[stat_type]

        try:
            data = self.get_data(query, url)

            if stat_type in [StatType.CALLS_BY_DATE, StatType.CALLS_SEO_BY_DATE]:
                return [{'date': k, 'calls': v} for k, v in data.items()]
            elif stat_type == StatType.CALLS_SEO_BY_KEYWORDS:
                return [{'keyword': k, 'calls': v} for k, v in data.items()]
            else:
                return {'callsTotal': data}

        except RequestError as e:
            return {
                'status': False,
                'message': e.message
            }
