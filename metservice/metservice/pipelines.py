# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import os
import csv
import datetime
import pandas as pd
from xlsxwriter.workbook import Workbook


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
            self.process_historical_data_tab(previous_weather_tabs[2])
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
            ongoing_path = os.path.join(out_folder, "ongoing", fname)
            if os.path.exists(ongoing_path):
                # load previous records
                with open(ongoing_path) as f:
                    ongoing_previous_info = pd.read_csv(f, parse_dates=['Date'],
                                                        date_parser=lambda x: pd.datetime.strptime(x, dt_format))
                print(ongoing_previous_info)
                # attach current records
                processed_tab_df = pd.DataFrame(processed_tab[1:], columns=processed_tab[0])
                ongoing_info = ongoing_previous_info.append(processed_tab_df).drop_duplicates('Date', keep='last')
                ongoing_info['Date'] = pd.to_datetime(ongoing_info['Date'], format=dt_format)
                print(ongoing_info.Date)
                ongoing_info = ongoing_info.set_index('Date').sort_index()

                # create rows for missing days (if there is any)
                print(ongoing_info.index)
                ongoing_info = ongoing_info.asfreq(dt_freq)
            else:
                # No previous records to merge with
                ongoing_info = pd.DataFrame(processed_tab[1:], columns=processed_tab[0])
                ongoing_info['Date'] = pd.to_datetime(ongoing_info['Date'], format=dt_format)
                ongoing_info.set_index('Date', inplace=True)

            ongoing_info.to_csv(ongoing_path)

            # Create Excel blanket file
            self.create_blanket_excel(ongoing_info, out_folder, 2021)

    @staticmethod
    def create_blanket_excel(ongoing_info, out_folder, year):
        xlsx_path = os.path.join(out_folder, "blanket.xlsx")
        workbook = Workbook(xlsx_path)
        worksheet = workbook.add_worksheet()

        # Set various parameters
        worksheet.set_column('B:B', 9.78)
        worksheet.set_column('H:H', 14.22)
        worksheet.set_zoom(116)

        # Write weather information
        worksheet.merge_range('C1:D1', "Temperatures")
        print(ongoing_info)
        year_mask = ongoing_info['Date'].dt.year == year
        year_info = ongoing_info[year_mask]

        out_info = year_info[['Date', 'Max_Temp', 'Min_Temp']]
        out_info['Date'] = out_info['Date'].dt.strftime("%d/%m/%Y")

        # Write headers
        headers = ["Date", "High", "Low", "Colour", "Start with", "Done", "Colour Range"]
        for col, header in zip(list('BCDEFGH'), headers):
            worksheet.write(col + '2', header)

        # Write information from DataFrame
        for col_idx, col in enumerate(out_info.columns):
            worksheet.write_column(2, col_idx + 1, out_info[col])
        # Write Max_Temp to conditionally-formatted column
        worksheet.write_column(2, 4, out_info['Max_Temp'])

        # Conditional formatting for colours
        colours_info = {
            'bright red': ("#FF0000", ">=", 25),
            'dull red': ("#C00000", "between", [20, 24.9]),
            'grey': ("#BFBFBF", "between", [15, 19.9]),
            'dull blue': ("#002060", "between", [10, 14.9]),
            'bright blue': ("#00B0F0", "between", [0.1, 9.9])
        }
        for code, criteria, value in colours_info.values():
            temp_format = workbook.add_format({'bg_color': code, 'font_color': code})
            if criteria == "between":
                worksheet.conditional_format(f'E3:E{len(out_info) + 2}', {'type': 'cell',
                                                                          'criteria': criteria,
                                                                          'minimum': value[0],
                                                                          'maximum': value[1],
                                                                          'format': temp_format})
            else:
                worksheet.conditional_format(f'E3:E{len(out_info) + 2}', {'type': 'cell',
                                                                          'criteria': criteria,
                                                                          'value': value,
                                                                          'format': temp_format})

        # Write 'Start with' column
        start_with = ['K' if ((x + 1) // 2) % 2 == 0
                      else 'P'
                      for x in range(len(out_info))]
        worksheet.write_column(2, 5, start_with)

        # Write legend information
        legend_descriptions = ["Below 9.9", "Between 10-14.9", "Between 15-19.9", "Between 20-24.9", "Above 25"]
        worksheet.write_column(2, 7, legend_descriptions)

        legend_colours = ["bright blue", "dull blue", "grey", "dull red", "bright red"]
        for i, colour in enumerate(legend_colours):
            colour_code = colours_info[colour][0]
            temp_format = workbook.add_format({'bg_color': colour_code})
            worksheet.write(f'I{i + 3}', "", temp_format)

        workbook.close()

    @staticmethod
    def process_last_30_days_tab(last_30_days_tab):
        out_lists = [
            ['Date', 'Min_Temp', 'Max_Temp', 'Rainfall', 'Wind_Direction', 'Wind_Speed']
        ]
        current_year = datetime.datetime.now().year  # needed for date formatting

        for day in last_30_days_tab['data']:
            raw_dt = datetime.datetime.strptime(day['header'], '%d %b')  # year defaults to 1990, so need to replace
            if raw_dt.month == 12:
                dt = raw_dt.replace(year=current_year - 1)  # date is in December/previous year
            else:
                dt = raw_dt.replace(year=current_year)
            formatted_date = dt.strftime("%d-%m-%Y")

            out_lists.append([
                formatted_date,
                day['current']['minTemp'],
                day['current']['maxTemp'],
                day['current']['rainFall'],
                day['current']['wind']['direction'],
                day['current']['wind']['direction']
            ])

        return "last_30_days", out_lists, "%d-%m-%Y", 'D'

    @staticmethod
    def process_historical_data_tab(historical_tab):
        out_lists = [
            ['Date', 'Min_Temp', 'Max_Temp', 'Rainfall']
        ]

        # Retrieve months for the for-loops
        months = [month_info['header'] for month_info in historical_tab['data']]

        today = datetime.date.today().replace(day=1)
        current_month = today - datetime.timedelta(days=1)  # get latest month in request

        years_with_periods = [
            (1990, 'historical'),
            (current_month.year - 1, 'last'),
            (current_month.year, 'current')
        ]

        for year, period in years_with_periods:
            for month_num, month_name in enumerate(months):
                raw_dt = datetime.datetime.strptime(month_name, "%b")
                dt = raw_dt.replace(day=1, year=year)
                formatted_date = dt.strftime("%d-%m-%Y")

                period_data = historical_tab['data'][month_num][period]
                out_lists.append([
                    formatted_date,
                    period_data['minTemp'],
                    period_data['maxTemp'],
                    period_data['rainFall']
                ])

        return "historical", out_lists, "%d-%m-%Y", 'MS'

    @staticmethod
    def process_yesterday_tab(yesterday_tab):
        yesterday_format = "%Y-%m-%d %H:%M:%S"#"%d-%m-%Y %H:%M"

        out_lists = [
            ['Date', 'Max_Temp', 'Rainfall', 'Wind_Direction', 'Wind_Speed']
        ]

        current_date = datetime.datetime.now().replace(hour=0, minute=0, second=0)
        yesterday_date = current_date.replace(day=current_date.day - 1)

        for hour in yesterday_tab['data']:
            if hour['header'] == "Midnight":
                # actually 0am today (not yesterday)
                formatted_datetime = current_date.strftime(yesterday_format)
            else:
                if hour['header'] == "Noon":
                    hour_num = 12
                else:
                    hour_num = datetime.datetime.strptime(hour['header'], "%I%p").hour
                formatted_datetime = yesterday_date.replace(hour=hour_num).strftime(yesterday_format)

            out_lists.append([
                formatted_datetime,
                hour['current']['maxTemp'],
                hour['current']['rainFall'],
                hour['current']['wind']['direction'],
                hour['current']['wind']['direction']
            ])

        return "yesterday", out_lists, yesterday_format, 'H'
