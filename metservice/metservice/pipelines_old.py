# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import csv
import os
import datetime
import pandas as pd
from scrapy.exporters import CsvItemExporter


class PreviousWeatherPipeline:

    def __init__(self):
        self.yesterday_info = []
        self.last_30_days_info = []
        self.historical_info = []

    def process_item(self, item, spider):
        previous_weather_info = item['layout']['primary']['slots']['main']['modules'][0]
        previous_weather_tabs = previous_weather_info['tabs']

        processed_tabs = [
            self.process_yesterday_tab(previous_weather_tabs[0]),
            self.process_last_30_days_tab(previous_weather_tabs[1]),
            #self.process_historical_data_tab(previous_weather_tabs[2])
        ]

        out_folder = os.path.join("previous weather")
        subfolders = ["most recent", "ongoing"]
        for subfolder in subfolders:
            subpath = os.path.join(out_folder, subfolder)
            if not os.path.exists(subpath):
                os.makedirs(subpath)

        for tab_name, processed_tab, dt_format, dt_freq in processed_tabs:
            fname = tab_name + ".csv"

            # Save this retrieval as "most recent"
            most_recent_fpath = os.path.join(out_folder, "most recent", fname)
            with open(most_recent_fpath, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerows(processed_tab)

            # Update ongoing record
            ongoing_path = os.path.join(out_folder, "ongoing_test_in", fname)
            if os.path.exists(ongoing_path) and tab_name != 'historical':
                # load previous records
                with open(ongoing_path) as f:
                    ongoing_previous_info = pd.read_csv(f)

                # attach current records
                processed_tab_df = pd.DataFrame(processed_tab[1:], columns=processed_tab[0])
                ongoing_info = ongoing_previous_info.append(processed_tab_df).drop_duplicates('Date', keep='last')
                ongoing_info['Date'] = pd.to_datetime(ongoing_info['Date'], format=dt_format)
                ongoing_info.set_index('Date', inplace=True)

                # create rows for missing days (if there is any)
                ongoing_info = ongoing_info.asfreq(dt_freq)
            else:
                # No previous records to merge with
                ongoing_info = pd.DataFrame(processed_tab[1:], columns=processed_tab[0])
                ongoing_info['Date'] = pd.to_datetime(ongoing_info['Date'], format=dt_format)
                ongoing_info.set_index('Date', inplace=True)

            print(ongoing_info)
            ongoing_info.to_csv(os.path.join(out_folder, "ongoing_test_out", fname))


    @staticmethod
    def process_last_30_days_tab(last_30_days_tab):
        names = ['Date', 'Min_Temp', 'Max_Temp', 'Rainfall', 'Wind_Direction', 'Wind_Speed']
        csv_list = [names]
        current_year = datetime.datetime.now().year  # needed for date formatting

        for day in last_30_days_tab['data']:
            raw_dt = datetime.datetime.strptime(day['header'], '%d %b')  # year defaults to 1990, so need to replace
            if raw_dt.month == 12:
                dt = raw_dt.replace(year=current_year - 1)  # date is in December/previous year
            else:
                dt = raw_dt.replace(year=current_year)
            formatted_date = dt.strftime("%d-%m-%Y")

            csv_list.append([
                formatted_date,
                day['current']['minTemp'],
                day['current']['maxTemp'],
                day['current']['rainFall'],
                day['current']['wind']['direction'],
                day['current']['wind']['direction']
            ])

        return "last_30_days", csv_list, "%d-%m-%Y", 'D'

    @staticmethod
    def process_historical_data_tab(historical_tab):
        periods = ['current', 'historical', 'last']
        names = ['Date', 'Min_Temp', 'Max_Temp', 'Rainfall']
        altered_names = [names[0]] + [f"{name} ({period})"
                                      for period in periods
                                      for name in names[1:]]
        csv_list = [altered_names]

        # Retrieve months to use in for loop
        months = [month_info['header'] for month_info in historical_tab['data']]

        for month_num, month_name in enumerate(months):
            month_list = [month_name]
            for period in periods:
                period_data = historical_tab['data'][month_num][period]
                month_list += [
                    period_data['minTemp'],
                    period_data['maxTemp'],
                    period_data['rainFall']
                ]
            csv_list.append(month_list)

        print(csv_list)
        return "historical", csv_list, "", ''

    @staticmethod
    def process_yesterday_tab(yesterday_tab):
        names = ['Date', 'Max_Temp', 'Rainfall', 'Wind_Direction', 'Wind_Speed']
        out_list = [names]
        current_date = datetime.datetime.now().replace(hour=0, minute=0, second=0)
        yesterday_date = current_date.replace(day=current_date.day - 1)

        for hour in yesterday_tab['data']:
            if hour['header'] == "Midnight":
                # actually 0am today (not yesterday)
                formatted_datetime = current_date.strftime("%d-%m-%YT%H:%M:%S")
            else:
                if hour['header'] == "Noon":
                    hour_num = 12
                else:
                    hour_num = datetime.datetime.strptime(hour['header'], "%I%p").hour
                formatted_datetime = yesterday_date.replace(hour=hour_num).strftime("%d-%m-%YT%H:%M:%S")

            out_list.append([
                formatted_datetime,
                hour['current']['maxTemp'],
                hour['current']['rainFall'],
                hour['current']['wind']['direction'],
                hour['current']['wind']['direction']
            ])

        return "yesterday", out_list, "%d-%m-%YT%H:%M:%S", 'H'
