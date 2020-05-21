import logging
from datetime import datetime

from accordion import compress

from backend.pipelines.calltouch.base import BaseCalltouchGetter, d_range, timing

COLUMN_CONFIGS = [
    ("date", "timestamp", "date"),
    ("city", "text", "city"),
    ("hostname", "text", "hostname"),
    ("callid", "integer", "callId"),
    ("utmSource", "text", "utmSource"),
    ("utmMedium", "text", "utmMedium"),
    ("utmCampaign", "text", "utmCampaign"),
    ("utmContent", "text", "utmContent"),
    ("utmTerm", "text", "utmTerm"),
    ("uniqueCall", "boolean", "uniqueCall"),
    ("uniqTargetCall", "boolean", "uniqTargetCall"),
    ("targetCall", "boolean", "targetCall"),
    ("source", "text", "source"),
    ("medium", "text", "medium"),
    ("keyword", "text", "keyword"),
    ("sessionId", "integer", "sessionId"),
    ("sessionDate", "timestamp", "sessionDate"),
    ("ya_campaignid", "integer", "yandexDirect.campaignId"),
    ("ya_adgroupid", "numeric", "yandexDirect.adGroupId"),
    ("yaclientId", "numeric", "yaClientId"),
    ("ga_campaignid", "numeric", "googleAdWords.campaignId"),
    ("ga_adgroupid", "numeric", "googleAdWords.adGroupId")
]


class CalltouchGetter(BaseCalltouchGetter):
    columns = [
        (column_config[0], column_config[1],)
        for column_config in COLUMN_CONFIGS
    ]

    @timing
    def rows(self):
        logger = logging.getLogger('luigi-interface')

        results = []

        for single_date in d_range(dateFrom, dateTo):
            logger.info(single_date)

            date_from = single_date.strftime('%d/%m/%Y')
            date_to = single_date.strftime('%d/%m/%Y')

            data = self.call_touch_grabber(date_from, date_to)

            single_date_result = []

            for row in data:
                logger.info(row['date'])
                logger.info(row['uniqTargetCall'])

                new_row = []
                row = compress(row)

                for destination, data_type, source in COLUMN_CONFIGS:
                    value = row.get(source)

                    if data_type == 'timestamp':
                        value = datetime.strptime(value, '%d/%m/%Y %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')

                    new_row.append(value)

                logger.info(new_row)

                single_date_result.append(new_row)

            results += single_date_result

        return results
