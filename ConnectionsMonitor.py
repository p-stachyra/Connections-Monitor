import datetime
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import re
import sqlite3
import sys
import time
import win32gui, win32con
import matplotlib.colors as mcolors
import random
from fpdf import FPDF

from monitor import Monitor
from monitor import Colors as color

monitor = Monitor()

def collect_data(save=True):
    monitor.add_process()
    monitor.remote_connections()
    if save:
        monitor.local_connections(monitor.connector, save)
        monitor.lookup(monitor.connector, save)
        return None
    else:
        local_connections = monitor.local_connections(monitor.connector, save)
        remote_connections = monitor.lookup(monitor.connector, save)
        return [local_connections, remote_connections]

def load_remote():
    try:
        df = pd.read_sql_query('SELECT * FROM connections;', monitor.connector)
    except:
        print('{}{}Could not load the data from connections table.{}'.format(color.BOLD, color.RED, color.END))
        raise SystemExit
    return df

def load_local():
    try:
        df2 = pd.read_sql_query('SELECT * FROM local_connections;', monitor.connector)
    except:
        print('{}{}Could not load the data from connections table.{}'.format(color.BOLD, color.RED, color.END))
        raise SystemExit
    return df2

def select_info_about(df):
    while True:
        column = input("Provide column name.\nType 'quit' to exit to the main menu.\n > ")
        if column.lower() == 'quit':
            output = column = name_to_filter = None
            break
        else:
            try:
                print("Available values:")
                print(str(len(df[column].unique())) + ' ' + 'results. Would you like to display them?')
                display = input("yes/no: ").lower()
                if display.startswith("y"):
                    options_display = df[column].unique()
                    options_display.sort()
                    for option in options_display:
                        print(f"{option}, ", end=" ")
                    print()
                name_to_filter = input("\nProvide the searched value or multiple values using comma as the separator\nExample: value1, value2, value3\n > ")
                if "," in name_to_filter:
                    replacement = re.sub(", ", "----", name_to_filter)
                    values = replacement.split("----")
                    output = pd.DataFrame()
                    for value in values:
                        temp = df[df[column] == value]
                        output = output.append(temp)
                else:
                    output = df[df[column] == name_to_filter].drop(columns=['index'])
                return output, column, name_to_filter
            except:
                print("{}{}Incorrect column name or value. Please try again.{}".format(color.BOLD, color.RED, color.END))
                continue
         
    
    

def get_grouped(df, column, element):
    """Requires a column parameter which must be of a list type and an element parameter - tuple which consists of value(s) included within the column(s)."""
    if isinstance(column, list):
        grouped = df.groupby(column)
        grouped_by_element = grouped.get_group(element)
        return grouped_by_element
    else:
        return []

def prepare_grouped(dataframe):
    while True:
        entry1 = input("{}{}\n[ ! ] Enter columns' names to filter using comma as a separator.\n{}Example: column1, column2, column3\nType 'quit' to quit to main menu\n > ".format(color.BOLD, color.CYAN, color.END))
        if entry1.lower() == 'quit':
            return []
            break
        print("\nSelected columns:", entry1)
        replacement = re.sub(" ", "_", entry1)
        replacement1 = re.sub(",_", "----", replacement)
        replacement2 = re.sub("_", " ", replacement1)

        columns = replacement2.split("----")

        count = {}
        for column in columns:
            if column in count:
                count[column] += 1
            else:
                count[column] = 1

        duplicated = None
        for k,v in count.items():
            if v > 1:
                print("{}{}Duplicated column detected! Please provide unique columns' names{}".format(color.BOLD, color.RED, color.END))
                duplicated = 1
            else:
                duplicated = 0

        if duplicated == 1:
            continue

        if len(columns) < 2:
            print("{}{}Please provide more than one column.{}".format(color.BOLD, color.RED, color.END))
            continue
        else:
            try:
                for column in columns:
                    print("Available values for column '{}':\n".format(column))
                    values_df = pd.DataFrame(dataframe[column].unique())
                    values_df.columns = ["Available Values to Filter"]
                    pd.set_option("display.max_rows", len(values_df))
                    print(values_df)
            except:
                print("{}{}Invalid column name! Try again.{}".format(color.BOLD, color.RED, color.END))
                continue
            while True:
                entry2 = input("{}{}\n[ ! ] Enter columns' values to apply filtering using comma as a separator.\n{}Example: value1, value2, value3\n > ".format(color.BOLD, color.CYAN, color.END))
                print("\nSelected values:", entry2)
                replacement3 = re.sub(", ","++", entry2)
                elements = tuple(replacement3.split("++"))
                if len(columns) != len(elements):
                    print("{}{}The number of provided values is not corresponding to the number of specified columns. Please try again.{}".format(color.BOLD, color.RED, color.END))
                    continue
                else:
                    #try:
                    grouped = get_grouped(dataframe, columns, elements)
                    if len(grouped) < 1:
                        error_type2()
                        break
                    else:
                        return grouped
                        break
                    #except:
                        #print("{}{}Invalid value! Try again.{}".format(color.BOLD, color.RED, color.END))
                        #continue
            #break
    

def times_run(timestamp):
    amount_of_runs = len(timestamp.unique())
    return amount_of_runs

def delete_database(dataframe_foreign):
    dataframe_foreign['timestamp'] = pd.to_datetime(dataframe_foreign['timestamp'])
    timedelta = dataframe_foreign['timestamp'].max() - dataframe_foreign['timestamp'].min()
    if (timedelta.days >= 150) & (len(dataframe_foreign) > 1000):
        return True
    else:
        return False

def select_dataframe_column(dataframe):
    print("\nSelect the column using its name (not the number):\nType quit to exit to menu.")
    while True:
        try:
            column = input(" > ")
            column.strip()
            if column == 'quit':
                values = None
                break
            else:
                values = dataframe[column].value_counts()
                break
            
        except:
            print("{}{}Invalid column name! Try again.{}".format(color.BOLD, color.RED, color.END))
            continue
    return column, values

def display_columns(dataframe):
    print("Available columns' names:")
    for index, col_name in enumerate(dataframe.columns):
        print(f"[{index}] {col_name}")

def export_to_excel(data):
    while True:
        try:
            print(f"{color.CYAN}")
            filename = input("Enter Excel file's name (or 'q' to quit): ")
            print(f"{color.END}")

            if (filename.lower() == 'q') or (filename.lower() == 'quit'):
                break
            elif filename[-5:] == '.xlsx':
                pass
            elif filename[-4:] =='.xls':
                temp = filename.split(".")
                filename = temp[0] + '.xlsx'
            else:
                filename = filename + '.xlsx'
            data.to_excel(filename)
            print("{}{}File saved successfully as: {}{}".format(color.BOLD, color.GREEN, filename, color.END))
            break
        except:
            print("{}{}The file could not be saved. Please try again or type 'q' to quit.{}".format(color.BOLD, color.RED, color.END))
            continue

def export_to_csv(data):
    while True:
        try:
            print(f"{color.CYAN}")
            filename = input("Enter CSV file's name (or 'q' to quit): ")
            print(f"{color.END}")

            if (filename.lower() == 'q') or (filename.lower() == 'quit'):
                break
            elif (filename[-4:] == '.csv'):
                pass
            else:
                filename = filename + '.csv'
            data.to_csv(filename)
            print("{}{}File saved successfully as: {}{}".format(color.BOLD, color.GREEN, filename, color.END))
            break
        except:
            print("{}{}The file could not be saved. Please try again or quit.{}".format(color.BOLD, color.RED, color.END))
            continue

def export_to_json(data):
    while True:
        try:
            print(f"{color.CYAN}")
            filename = input("Enter JSON file's name (or 'q' to quit): ")
            print(f"{color.END}")

            if (filename.lower() == 'q') or (filename.lower() == 'quit'):
                break
            data.to_json(filename)
            print("{}{}File saved successfully as: {}{}".format(color.BOLD, color.GREEN, filename, color.END))
            break
        except:
            print("{}{}The file could not be saved. Please try again or quit.{}".format(color.BOLD, color.RED, color.END))
            continue

#method overloading possible, but not that convenient
def advanced_export(export_type, dataframe_local, dataframe_foreign):
    while True:
        print(f"Which dataset would you like to save to {export_type.upper()} file?")
        print("1 - Foreign connections\n2 - Local connections\n3 - Quit to main menu")
        inp1 = select_option()
        if inp1 not in [1,2,3]:
            error_type1()
            continue
        elif inp1 == 1:
            while True:
                #print("Which dataset would you like to save to EXCEL file?")
                print("1 - The whole foreign connections table\n2 - Single column filter\n3 - Multiple columns filter\n4 - Back")
                inp2 = select_option()
                if inp2 not in [1,2,3,4]:
                    error_type1()
                    continue
                elif inp2 == 1:
                    if export_type == 'excel':
                        export_to_excel(dataframe_foreign)
                    elif export_type == 'csv':
                        export_to_csv(dataframe_foreign)
                    else:
                        error_type2()
                    break
                elif inp2 == 2:
                    display_columns(dataframe_foreign)
                    output = select_info_about(dataframe_foreign)
                    if output == None:
                        print("{}{}Quitting...{}".format(color.BOLD, color.RED, color.END))
                        break
                    else:
                        output = output[0]
                        if export_type == 'excel':
                            export_to_excel(output)
                        elif export_type == 'csv':
                            export_to_csv(output)
                    
                elif inp2 == 3:
                    display_columns(dataframe_foreign)
                    try:
                        output = prepare_grouped(dataframe_foreign)
                        print(output)
                        if len(output) < 1:
                            print("Nothing to save!")
                            break
                        elif export_type == 'excel':
                            export_to_excel(output)
                        elif export_type == 'csv':
                            export_to_csv(output)
                    except:
                        print("{}{}Quitting...{}".format(color.BOLD, color.RED, color.END))
                        break
                else:
                    break
        elif inp1 == 2:
            while True:
                #print("Which dataset would you like to save to EXCEL file?")
                print("1 - The whole foreign connections table\n2 - Single column filter\n3 - Multiple columns filter\n4 - Back")
                inp2 = select_option()
                if inp2 not in [1,2,3,4]:
                    error_type1()
                    continue
                elif inp2 == 1:
                    if export_type == 'excel':
                        export_to_excel(dataframe_local)
                    elif export_type == 'csv':
                        export_to_csv(dataframe_local)
                    else:
                        error_type2()
                    break
                elif inp2 == 2:
                    display_columns(dataframe_local)
                    output = select_info_about(dataframe_local)
                    if output == None:
                        print("{}{}Quitting...{}".format(color.BOLD, color.RED, color.END))
                        break
                    else:
                        output = output[0]
                        if export_type == 'excel':
                            export_to_excel(output)
                        elif export_type == 'csv':
                            export_to_csv(output)
                    
                elif inp2 == 3:
                    display_columns(dataframe_local)
                    try:
                        output = prepare_grouped(dataframe_local)
                        if len(output) < 1:
                            break
                        elif export_type == 'excel':
                            export_to_excel(output)
                        elif export_type == 'csv':
                            export_to_csv(output)
                    except:
                        print("{}{}Quitting...{}".format(color.BOLD, color.RED, color.END))
                        break
                else:
                    break
        else:
            break


def filtering(dataframe):
    display_columns(dataframe)
    try:
        filtered, column, value_to_filter = select_info_about(dataframe)
    except:
        print("{}{}Please try again.{}".format(color.BOLD, color.RED, color.END))
        return None
    print("Selected column:", column)
    print("Selected value:", value_to_filter)
    if len(filtered) > 0:

        print(filtered)
        print("{}Would you like to save the filtered rows to a file?\nType: yes/no\n{}".format(color.BOLD, color.END))
        print(f"{color.CYAN}")
        option = input(" > ").lower()
        print(f"{color.END}")


        if option.startswith("y"):
            print("Which format do you prefer?")
            print("1 - Excel\n2 - CSV\n3 - JSON\n4 - quit")
            while True:
                try:
                    print(f"{color.CYAN}")
                    option = int(input(" > "))
                    print(f"{color.END}")
                except:
                    error_type1()
                if option == 1:
                    export_to_excel(filtered)
                    break
                elif option == 2:
                    export_to_csv(filtered)
                    break
                elif option == 3:
                    export_to_json(filtered)
                    break
                elif option == 4:
                    break
                else:
                    error_type1()
                    continue
        else:
            print("{}{}Not saving.{}".format(color.BOLD, color.RED, color.END))
    else:
        print("{}{}\nNo results found! Check the provided values. Filtering is case-sensitive.\n{}".format(color.BOLD, color.RED, color.END))

def backdoor_examination(local_connections, foreign_connections, timestamp):
    ports_counts = local_connections.query('Interface == "0.0.0.0"')['Port 1'].value_counts()
    unique_ports = local_connections.query('Interface == "0.0.0.0"')['Port 1'].unique()
    repeated_ports = []
    for port in unique_ports:
       if port in foreign_connections['Local Port']:
           repeated_ports.append(port)
    if len(repeated_ports) > 0:
        suspicious_cons = foreign_connections[foreign_connections['Local Port'].isin(repeated_ports)]
    else:
        suspicious_cons = []
    percent_of_all_checks = round((ports_counts / times_run(timestamp)) * 100, 2)
    return ports_counts, unique_ports, percent_of_all_checks, repeated_ports, suspicious_cons

def error_type1():
    print("{}{}Error! Please provide a valid integer corresponding to one of the available options.{}".format(color.BOLD, color.RED, color.END))

def error_type2():
    print("{}{}Error! Something went wrong.{}".format(color.BOLD, color.RED, color.END))

def select_option():
    while True:
        try:
            print(f"{color.CYAN}")
            option = int(input(" > "))
            print(f"{color.END}")
        except:
            error_type1()
            continue
        break
    return option

def approximated_datetime(dataframe, column):
    while True:
        date_time = pd.to_datetime(dataframe[column])
        print("{}Provide the searched date, hour, date and hour or datetime interval{}".format(color.BOLD, color.END))
        print("{}1 - Date\n2 - Time\n3 - Date and time\n4 - Datetime interval\n5 - Return to menu{}".format(color.BOLD, color.END))
        try:
            print(f"{color.CYAN}")
            inp1 = int(input(" > "))
            print(f"{color.END}")
        except:
            error_type1()
            continue
        try:
            if inp1 == 1:
                print("Use the format:\nYYYY/MM/DD")
                print(f"{color.CYAN}")
                inp2 = input(" > ")
                print(f"{color.END}")
                start = pd.to_datetime(inp2)
                end = start + datetime.timedelta(days=1)
                return dataframe[(date_time > start) & (date_time < end)]
            elif inp1 == 2:
                dataframe[column] = dataframe[column].astype(str)
                print("{}Provide the searched time:{}".format(color.BOLD, color.END))
                print(f"{color.CYAN}")
                inp2 = input(" > ")
                print(f"{color.END}")
                return dataframe[dataframe[column].str.contains("\.*\s{}".format(inp2))]
            elif inp1 == 3:
                print("Use the format:\nYYYY/MM/DD hh:mm:ss")
                print(f"{color.CYAN}")
                inp2 = input(" > ")
                print(f"{color.END}")
                start = pd.to_datetime(inp2)
                end = start + datetime.timedelta(hours=1)
                return dataframe[(date_time > start) & (date_time < end)]
            elif inp1 == 4:
                print("{}Use one of the formats:\n\nYYYY/MM/DD,YYYY/MM/DD\nExample: 2021/04/01,2021/04/03\n\nYYYY/MM/DD hh:mm:ss,YYYY/MM/DD hh:mm:ss\nExample: 2021/04/02 18:01:00,2021/04/02 18:59:00{}".format(color.BOLD, color.END))
                print(f"{color.CYAN}")
                inp2 = input(" > ")
                print(f"{color.END}")
                if "," in inp2:
                    data = inp2.split(",")
                    start = pd.to_datetime(data[0])
                    end = pd.to_datetime(data[1])
                    return dataframe[(date_time > start) & (date_time < end)]
                else:
                    print("{}{}No comma detected!{}".format(color.BOLD, color.RED, color.END))
                    continue
            elif inp1 == 5:
                return pd.DataFrame()
            else:
                error_type1()
                continue
        except:
            print("{}{}Invalid value!{}".format(color.BOLD, color.RED, color.END))
            continue

    #### BARS/PLOTS

def ipv4_bar_plots(series, imagename=None, save=False):
    try:
        connections_count = series.value_counts()
        upper_limit = int(0.3 * max(connections_count))
        middle_limit = int(0.2 * max(connections_count))
        lower_limit = int(0.1 * max(connections_count))

        #The most common IPs
        most_common = connections_count[connections_count >= upper_limit]

        #2nd group
        middle_group = connections_count[(connections_count < upper_limit) & (connections_count >= middle_limit)]

        #Last 2 groups
        lower_group = connections_count[(connections_count < middle_limit) & (connections_count > 1)]
        equal_1 = connections_count[connections_count == 1]

        fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(15,5))
        axes[0].set_title("IPv4 Addresses:\n> {} connections".format(str(upper_limit)))
        axes[0].set_xlabel("IPv4 Address", fontsize=8)
        axes[1].set_title("IPv4 Addresses:\nBetween {} and {} connections".format(str(middle_limit), str(upper_limit)))
        axes[1].set_xlabel("IPv4 Address", fontsize=8)
        most_common.plot.bar(ax = axes[0])
        middle_group.plot.bar(ax = axes[1], color='orange')
        plt.gcf().subplots_adjust(bottom=0.3)
        if save:
            plt.savefig(f"{imagename}")
            plt.close()
        else:
            plt.show()
        return most_common, middle_group, lower_group, equal_1
    except:
        error_type2()

def create_pie_chart(series, title, imagename=None, save=False):
    percentage_country = series.value_counts() / len(series) * 100
    colors = []
    for number in range(len(percentage_country)):
        rgb = (random.random(), random.random(), random.random())
        colors.append(rgb)
    labels = percentage_country.index
    labels=['%s, %1.1f %%' % (l, p) for l, p in zip(labels, percentage_country)]
    patches, texts = plt.pie(percentage_country, colors=colors, startangle=90) 
    if save:
        plt.legend(patches, labels, loc=2, prop={'size': 7})
    else:
        plt.legend(patches, labels, loc="best")
    plt.axis('equal')
    plt.title(title)
    plt.tight_layout()
    if save:
        plt.savefig(imagename)
        plt.close()
    else:
        plt.show()

def date_time_bar(dataframe, connections):
    while True:
        print("{}Select the time period:\n1 - Selected day\n2 - Selected week\n3 - Whole dataset\n4 - back{}".format(color.BOLD, color.END))
        data = dataframe.groupby(dataframe['Date/Time'])[connections].count()
        inp2 = select_option()
        if inp2 == 1:
            date = input("Enter required date:\nFormat: YYYY-MM-DD\n > ")
            try:
                data.index = data.index.astype(str)
                display = data[data.index.str.contains('{}'.format(date))]
                display.plot(kind='bar',figsize=(10,5),legend=None)
                plt.tight_layout()
                plt.show()
            except:
                error_type2()
                continue
        elif inp2 == 2:
            try:
                start_date = pd.to_datetime(input("Enter the first day's date:\nFormat: YYYY-MM-DD\n > "))
                step = datetime.timedelta(days=7)
                end = start_date + step
                display = data[(data.index >= start_date) & (data.index <= end)]
                display.plot(kind='bar',figsize=(10,5),legend=None)
                plt.tight_layout()
                plt.show()
            except:
                error_type2()
                continue
        elif inp2 == 3:
            try:
                data.plot(kind='bar',figsize=(10,5),legend=None)
                plt.tight_layout()
                plt.show()
            except:
                error_type2()
                continue
        else:
            break

def generate_report(timestamp, df1, df2):

    def pie_chart(page_title, chart_title, image_file_name, series, general_width):
        pdf.add_page()

        pdf.set_font('Arial', '', 16)
        pdf.write(4, page_title)
        create_pie_chart(series, chart_title, image_file_name, save=True)
        pdf.image(image_file_name, 5, 50, general_width - 25)
        os.system(f"del {image_file_name}")
    
    width = 210
    height = 297
    date_time = datetime.datetime.now().replace(second=0, microsecond=0)
    random_letters = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P']

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', '', 24)  
    pdf.ln(10)
    pdf.cell(20,10, f"Connections Evaluation Report", "C")
    pdf.ln(15)
    pdf.set_font('Arial', '', 12)
    pdf.write(4, f'{str(date_time)}')
    
    pdf.ln(30)

    filename = str(int(random.randint(1,100000))) + random_letters[random.randint(0,15)] + "-IPV4.png"
    ipv4_bar_plots(df2['Foreign IPv4 Address'], filename, save=True)
    pdf.ln(12)
    pdf.set_font('Arial', '', 16)
    pdf.write(4, "Foreign IPv4 Addresses")
    pdf.set_font('Arial', '', 14)
    pdf.ln(7)
    pdf.image(filename, 5, 70, width - 15)
    os.system(f"del {filename}")

    pie_chart("Processes", "Registered Processes: Foreign Connections", str(int(random.randint(1,100000))) + random_letters[random.randint(0,15)] + "-proc-foreign.png", df2['Process Name'], width)
    pie_chart("Processes", "Registered Processes: Local Connections", str(int(random.randint(1,100000))) + random_letters[random.randint(0,15)] + "-proc-local.png", df1['Process Name'], width)
    pie_chart("Countries", "Connections: Countries of Source/Destination", str(int(random.randint(1,100000))) + random_letters[random.randint(0,15)] + "-countries.png", df2['Country'], width)
    pie_chart("Foreign Connections State", "Foreign Connections: State", str(int(random.randint(1,100000))) + random_letters[random.randint(0,15)] + "-state.png", df2['State'], width)
    pie_chart("Local Connections State", "Local Connections: State", str(int(random.randint(1,100000))) + random_letters[random.randint(0,15)] + "-state-local.png", df1['State'], width)


    pdf.add_page()

    pdf.set_font('Arial', '', 16)
    pdf.write(4, "Connections over Time")

    filename_dt = str(int(random.randint(1,100000))) + random_letters[random.randint(0,15)] + "-datetime.png"
    (df2['Date/Time'][df2['Date/Time'] > (datetime.datetime.now() - datetime.timedelta(days=7))]).value_counts().plot(kind='bar',figsize=(10,5),legend=None)
    plt.title("Amount of Connections: Last 7 days")
    plt.tight_layout()
    plt.savefig(filename_dt)
    plt.close()
    pdf.image(filename_dt, 5, 70, width - 15)
    os.system(f"del {filename_dt}")

    pdf.add_page()

    pdf.set_font('Arial', '', 16)
    pdf.write(4, "Connections over Time")

    filename_dt2 = str(int(random.randint(1,100000))) + random_letters[random.randint(0,15)] + "-datetime-months.png"
    datetime_df = pd.DataFrame(pd.to_datetime(df2['Date/Time']).dt.to_period('M'))
    datetime_df.columns = ['Month']
    counted_by_month = datetime_df['Month'].value_counts()
    counted_by_month.plot(kind='bar',figsize=(10,5),legend=None)
    plt.title("Amount of Connections: All Months")
    plt.tight_layout()
    plt.savefig(filename_dt2)
    plt.close()
    pdf.image(filename_dt2, 5, 70, width - 15)
    os.system(f"del {filename_dt2}")

    pdf.add_page()

    pdf.set_font('Arial', '', 16)
    pdf.write(4, "Most Common IPv4 Foreign Addresses: Last 3 days")

    last_3_days = df2[df2['Date/Time'] > (datetime.datetime.now() - datetime.timedelta(days=3))]
    addresses = last_3_days.drop_duplicates(subset=['Foreign IPv4 Address'])
    pdf.ln(7)
    pdf.set_font('Arial', '', 9)
    pdf.ln(7)
    pdf.cell(50, 10, '%s' % ('Foreign IPv4 Address'), 1, 0, 'C')
    pdf.cell(40, 10, '%s' % ('Server Name'), 1, 0, 'C')
    pdf.cell(40, 10, '%s' % ('Process Name'), 1, 2, 'C')
    pdf.cell(-90)
    for i in range(len(addresses)):
        pdf.cell(50, 7, '%s' % (addresses['Foreign IPv4 Address'].iloc[i]), 1, 0, 'C')
        pdf.cell(40, 7, '%s' % (addresses['Server Name'].iloc[i]), 1, 0, 'C')
        pdf.cell(40, 7, '%s' % (addresses['Process Name'].iloc[i]), 1, 2, 'C')
        pdf.cell(-90)

    pdf.add_page()
    pdf.set_font('Arial', '', 14)
    pdf.write(4, f"Connections have been monitored: {str(times_run(timestamp))} times.")
    pdf.ln(7)
    pdf.write(4, f"Local connections table contains: {str(len(df1))} rows.")
    pdf.ln(7)
    pdf.write(4, f"Foreign connections table contains: {str(len(df2))} rows.")
    pdf.ln(10)
    ports_counts, unique_ports, percent_of_all_checks, repeated_ports, suspicious_cons = backdoor_examination(df1, df2, df1['Date/Time'])
    pdf.write(4, "Ports detected to listen on all interfaces:")
    pdf.ln(7)
    
    pdf.set_font('Arial', '', 12)
    for index,port in enumerate(unique_ports):
        pdf.write(4, f" {index + 1}. {port}")
        pdf.ln(5)
    
    pdf.add_page()

    pdf.ln(7)
    pdf.set_font('Arial', '', 14)
    pdf.write(6, "Amount of suspicious ports which were both listening locally and established a connection with foreign host:")
    pdf.ln(7)
    pdf.write(4, str(len(repeated_ports)))
    pdf.ln(7)
    if len(repeated_ports) > 0:
        pdf.write(4, "The suspicious ports:")
        for port in repeated_ports.list():
            pdf.write(4, f"{port}")
            pdf.ln(5)
        pdf.ln(7)
    pdf.write(6, "Amount of suspicious connections:")
    pdf.ln(7)
    pdf.write(6, f"{str(len(suspicious_cons))}")
    pdf.ln(7)
    if len(suspicious_cons) > 0:
        pdf.write(6, "The suspicious connections:")
        for connection in suspicious_cons:
            pdf.write(6, f"{connection}")
            pdf.ln(5)
        pdf.ln(7)
    pdf.output(f'Connections_Evaluation_Report_{str(date_time).replace(" ", "_").replace(":", "-")}.pdf', 'F')

def main():


    if len(sys.argv) > 1:
        if sys.argv[1] == "u":
            collect_data()
            sys.exit()

        elif sys.argv[1] != "u":
            print("Unrecognized option. Quitting.")
            sys.exit()


    if (os.path.exists("connections.db")) & (os.path.getsize("connections.db") > 0):
        foreign = load_remote().astype(str)
        local = load_local().astype(str)

    else:
        print("{}{}[ i ] The database file has been created.{}".format(color.BOLD, color.CYAN, color.END))
        collect_data()
        print("{}{}[ i ] Data were collected successfully.\n[ i ] The program will shut down. To proceed, please run it again.{}".format(color.BOLD, color.CYAN, color.END))
        time.sleep(5)
        sys.exit()

    delete = delete_database(foreign)
    if delete:
        print("\n{}{}[ ! ] The database is more than 150 days old.{}\nWould you like to save information in a form of a report and delete the database file or do you prefer keep it?".format(color.BOLD, color.RED, color.END))
        print("\n{}Select option:\n1 - prepare the report and delete the database file.\n2 - keep the database file.\n{}".format(color.BOLD, color.END))
        while True:
            try:
                print(f"{color.CYAN}")
                option = int(input(" > "))
                print(f"{color.END}")
                break
            except:
                error_type1()
                continue
        if option == 1:
            generate_report()
            monitor.connector.close()
            os.system("del connections.db")
            collect_data()
        elif option == 2:
            pass
        else:
            print("{}{}Invalid option! Quitting...{}".format(color.BOLD, color.RED, color.END))
            raise SystemExit
    else:
        pass

    foreign.columns = ['index', 'Interface', 'Local Port', 'Foreign IPv4 Address', 'Foreign Port', 'State', 'Process ID', 'Date/Time', 'Process Name', 'Server Name', 'Server Description', 'Country']
    local.columns = ['index', 'Interface', 'Port 1', 'Destination Address', 'Port 2', 'State', 'Process ID', 'Date/Time', 'Process Name']
    local['Date/Time'] = local['Date/Time'].str.replace("T", " ")

    while True:
        print("{}\nSelect the mode of the program:{}".format(color.BOLD, color.END))
        print("1  - {}{}[ UPDATE ]{} Update connections database file.".format(color.BOLD, color.RED, color.END))
        print("2  - {}{}[ MONITOR ]{} Output the current connections.".format(color.BOLD, color.GREEN, color.END))
        print("3  - {}{}[ SUMMARIZE ]{} Frequency distribution table based on values within a specified column.".format(color.BOLD, color.LIGHTBLUE, color.END))
        print("4  - {}{}[ SINGLE   COLUMN  FILTER ]{} Return all rows with the specified value/values within selected column.".format(color.BOLD, color.ORANGE, color.END))
        print("5  - {}{}[ MULTIPLE COLUMNS FILTER ]{} Return all rows which contain specified values.".format(color.BOLD, color.ORANGE, color.END))
        print("6  - {}{}[ SIMPLE BACKDOOR AUDIT ]{} Return all unique local ports that were listening on all interfaces.".format(color.BOLD, color.YELLOW, color.END))
        print("7  - {}{}[ EXPORT - EXCEL ]{} Save data in an Excel file.".format(color.BOLD, color.GREEN2, color.END))
        print("8  - {}{}[ EXPORT - CSV ]{} Save data in a CSV file.".format(color.BOLD, color.GREEN2, color.END))
        print("9  - {}{}[ VISUALIZATION ]{} Display the amount of connections established with a specific foreign address in a bar chart.".format(color.BOLD, color.YELLOW2, color.END))
        print("10 - {}{}[ VISUALIZATION ]{} Display the percentage of connections' country of origin in a format of a pie chart.".format(color.BOLD, color.YELLOW2, color.END))
        print("11 - {}{}[ VISUALIZATION ]{} Display the amount of connections during selected time interval.".format(color.BOLD, color.YELLOW2, color.END))
        print("12 - {}{}[ VISUALIZATION ]{} Display the percentage of processes.".format(color.BOLD, color.YELLOW2, color.END))
        print("13 - {}{}[ REPORT ]{} Generate a report.".format(color.BOLD, color.RED2, color.END))
        print("14 - {}{}[ DATE & TIME - BASED FILTER ]{} Return all rows for datetime approximated values.".format(color.BOLD, color.ORANGE, color.END))
        print("15 - {}>[ EXIT ]<{} Quit the program.".format(color.BOLD, color.END))

        while True:
            try:
                print(f"{color.CYAN}")
                mode = int(input(" > "))
                print(f"{color.END}")
                break
            except:
                #print("{}{}Error! Please provide a valid integer corresponding to one of the available options.{}".format(color.BOLD, color.RED, color.END))
                error_type1()
                continue
        modes = np.arange(1,16)
        if mode in modes:

            ### MODE 1

            if mode == 1:
                collect_data()

            ### MODE 2

            elif mode == 2:
                print("{}\n\nThe CMD Window should be maximized in order to display the results properly.\nIf it remains your foreground window, it will be maximized automatically.\n{}".format(color.BOLD, color.END))
                collected = collect_data(save=False)
                foreground = win32gui.GetForegroundWindow()
                win32gui.ShowWindow(foreground, win32con.SW_MAXIMIZE)
                print("{}{}\nLocal connections:\n{}".format(color.BOLD, color.CYAN, color.END), collected[0])
                print("{}{}\nForeign connections:\n{}".format(color.BOLD, color.CYAN, color.END), collected[1])

            ### MODE 3

            elif mode == 3:
                while True:
                    # "Select the dataframe:\n1 - local connections\n2 - foreign connections\n3 - quit to the main menu 
                    print("{}Select the dataframe:\n1 - local connections\n2 - foreign connections\n3 - quit to the main menu{}".format(color.BOLD, color.END))
                    inp1 = select_option()
                    if inp1 == 1:
                        display_columns(local)
                        column, local_count = select_dataframe_column(local)
                        if column == 'quit':
                            break
                        length = local_count.shape[0]
                        print("The dataframe contains {} rows. What would you like to do?\n1 - Display all\n2 - Save to Excel file\n3 - Save to CSV file\n4 - Back to main menu".format(length))
                        inp1_1 = select_option()
                        df_local_count = pd.DataFrame(local_count).reset_index()
                        df_local_count.columns=[str(column), 'Frequency']
                        if inp1_1 == 1:
                            pd.set_option("display.max_rows", length)
                            print(df_local_count)
                        elif inp1_1 == 2:
                            export_to_excel(df_local_count)
                        elif inp1_1 == 3:
                            export_to_csv(df_local_count)
                        elif inp1_1 == 4:
                            break
                    elif inp1 == 2:
                        display_columns(foreign)
                        column, foreign_count = select_dataframe_column(foreign)
                        if column == 'quit':
                            break
                        length = foreign_count.shape[0]
                        print("The dataframe contains {} rows. What would you like to do?\n1 - Display all\n2 - Save to Excel file\n3 - Save to CSV file\n4 - Back to main menu".format(length))
                        inp1_2 = select_option()
                        df_foreign_count = pd.DataFrame(foreign_count).reset_index()
                        df_foreign_count.columns=[str(column), 'Frequency']
                        if inp1_2 == 1:
                            pd.set_option("display.max_rows", length)
                            print(df_foreign_count)
                        elif inp1_2 == 2:
                            export_to_excel(df_foreign_count)
                        elif inp1_2 == 3:
                            export_to_csv(df_foreign_count)
                        elif inp1_2 == 4:
                            break
                    elif inp1 == 3:
                        break
                    else:
                        error_type2()
                        continue
            ### MODE 4

            elif mode == 4:
                while True:
                    # "Select the dataframe:\n1 - local connections\n2 - foreign connections\n3 - quit to the main menu"
                    print("{}Select the dataframe:\n1 - local connections\n2 - foreign connections\n3 - quit to the main menu{}".format(color.BOLD, color.END))
                    inp1 = select_option()
                    if inp1 == 1:
                        filtering(local)
                    elif inp1 == 2:
                        filtering(foreign)
                    elif inp1 == 3:
                        break
                    else:
                        error_type2()
                        continue

            ### MODE 5

            elif mode == 5:
                while True:
                    # "Select the dataframe:\n1 - local connections\n2 - foreign connections\n3 - quit to the main menu"
                    print("{}Select the dataframe:\n1 - local connections\n2 - foreign connections\n3 - quit to the main menu{}".format(color.BOLD, color.END))
                    inp1 = select_option()
                    if inp1 == 1:
                        display_columns(local)
                        prepared = prepare_grouped(local)
                        if len(prepared) < 1:
                            break
                        else:
                            print("{}{}The dataframe contains {} rows. What would you like to do?{}\n1 - Display all\n2 - Save to Excel file\n3 - Save to CSV file\n4 - Back to main menu".format(color.BOLD, color.GREEN, len(prepared), color.END))
                            if len(prepared) > 20:
                                print("{}{}[ * ] Displaying all rows is not recommended.{}".format(color.BOLD, color.CYAN, color.END))
                            inp5 = select_option()
                            if inp5 == 1:
                                pd.set_option("display.max_rows", len(prepared))
                                #pd.set_option("display.max_columns", len(prepared.columns))
                                foreground = win32gui.GetForegroundWindow()
                                win32gui.ShowWindow(foreground, win32con.SW_MAXIMIZE)
                                print(prepared)
                            elif inp5 == 2:
                                export_to_excel(prepared)
                            elif inp5 == 3:
                                export_to_csv(prepared)
                            elif inp5 == 4:
                                break
                    elif inp1 == 2:
                        display_columns(foreign)
                        prepared = prepare_grouped(foreign)
                        if len(prepared) < 1:
                            break
                        else:
                            print("{}{}The dataframe contains {} rows. What would you like to do?{}\n1 - Display all\n2 - Save to Excel file\n3 - Save to CSV file\n4 - Back to main menu".format(color.BOLD, color.GREEN, len(prepared), color.END))
                            if len(prepared) > 20:
                                print("{}{}[ * ] Displaying all rows is not recommended.{}".format(color.BOLD, color.CYAN, color.END))
                            inp5 = select_option()
                            if inp5 == 1:
                                pd.set_option("display.max_rows", len(prepared))
                                #pd.set_option("display.max_columns", len(prepared.columns))
                                foreground = win32gui.GetForegroundWindow()
                                win32gui.ShowWindow(foreground, win32con.SW_MAXIMIZE)
                                print(prepared)
                            elif inp5 == 2:
                                export_to_excel(prepared)
                            elif inp5 == 3:
                                export_to_csv(prepared)
                            elif inp5 == 4:
                                break

                    elif inp1 == 3:
                        break
                    else:
                        error_type2()
                        continue

            ### MODE 6

            elif mode == 6:
                ports_counts, unique_ports, percent_of_all_checks, repeated_ports, suspicious_cons = backdoor_examination(local, foreign, local['Date/Time'])
                print("{}{}\nPorts listening on all interfaces:{}\n".format(color.BOLD, color.GREEN, color.END))
                for port in unique_ports:
                    print(port + ',', end=' ')
                time.sleep(1)

                #Frequency distribution
                print("{}{}\nHow many times was the port observed:{}\n".format(color.BOLD, color.GREEN, color.END))
                ports_counts = ports_counts.to_frame()
                ports_counts.reset_index(inplace=True)
                ports_counts.columns = ["Port Number", "Amount of Observations"]
                print(ports_counts.to_string(index=False))
                time.sleep(1)

                #Frequency distribution - %
                print("{}{}\nIn how many scan did the port appear: [ in % ] {}\n".format(color.BOLD, color.GREEN, color.END))
                percent_of_all_checks = percent_of_all_checks.to_frame()
                percent_of_all_checks.reset_index(inplace=True)
                percent_of_all_checks.columns = ["Port Number", "Share of all observations [%]"]
                print(percent_of_all_checks.to_string(index=False))
                time.sleep(1)

                #Suspicious ports
                print("{}{}\nAmount of suspicious ports which were both listening locally and established a connection with foreign host:{}\n".format(color.BOLD, color.RED, color.END))
                print(len(repeated_ports))
                if len(repeated_ports) > 0:
                    print("{}{}\nThe suspicious ports:{}\n".format(color.BOLD, color.RED, color.END))
                    for port in repeated_ports:
                        print(port)
                time.sleep(1)

                print("{}{}\nAmount of suspicious connections:{}\n".format(color.BOLD, color.RED, color.END))
                print(len(suspicious_cons))
                if len(suspicious_cons) > 0:
                    print("{}{}\nThe suspicious connections:{}\n".format(color.BOLD, color.RED, color.END))
                    for connection in suspicious_cons:
                        print(connection)

            ### MODE 7
            elif mode == 7:
                advanced_export('excel', local, foreign)

            ### MODE 8
            elif mode == 8:
                advanced_export('csv', local, foreign)

            ### MODE 9
            elif mode == 9:
                try:
                    most_common, middle_group, lower_group, equal_1 = ipv4_bar_plots(foreign['Foreign IPv4 Address'])
                    if len(lower_group) > 20:
                        print("")
                except:
                    print("{}{}Could not obtain the required data.{}".format(color.BOLD, color.RED, color.END))

            ### MODE 10
            elif mode == 10:
                create_pie_chart(foreign['Country'], "Connections: Countries of Origin")

            ### MODE 11
            elif mode == 11:
                while True:
                    print("{}Select the dataframe:\n1 - local connections\n2 - foreign connections\n3 - quit to the main menu{}".format(color.BOLD, color.END))
                    inp1 = select_option()
                    if inp1 == 1:
                        date_time_bar(local, 'Destination Address')
                    elif inp1 == 2:
                        date_time_bar(foreign, 'Foreign IPv4 Address')
                    elif inp1 == 3:
                        break
                    else:
                        error_type1()
                        continue

            ### MODE 12
            elif mode == 12:
                create_pie_chart(foreign['Process Name'], "Registered Processes")

            ### MODE 13
            elif mode == 13:
                generate_report(foreign['Date/Time'], local, foreign)

            ### MODE 14
            elif mode == 14:
                while True:
                    print("{}Select the dataframe:\n1 - local connections\n2 - foreign connections\n3 - quit to the main menu{}".format(color.BOLD, color.END))
                    inp1 = select_option()
                    if inp1 == 1:
                        output = approximated_datetime(local, 'Date/Time')
                        if len(output) == 0:
                            print("{}{}No corresponding values found!{}".format(color.BOLD, color.RED, color.END))
                        else:
                            if len(output) > 100:
                                print("There are {} rows to display. Would you like to display them?".format(str(len(output))))
                                inp3 = input("Type yes/no\n > ").lower()
                                if inp3.startswith('y'):
                                    foreground = win32gui.GetForegroundWindow()
                                    win32gui.ShowWindow(foreground, win32con.SW_MAXIMIZE)
                                    pd.set_option("display.max_rows", len(output))
                                    print(output)
                            else:
                                foreground = win32gui.GetForegroundWindow()
                                win32gui.ShowWindow(foreground, win32con.SW_MAXIMIZE)
                                pd.set_option("display.max_rows", len(output))
                                print(output)
                            print("Would you like to save the results to a file?")
                            inp4 = input("Type yes/no\n > ").lower()
                            if inp4.startswith('y'):
                                while True:
                                    print("1 - Excel\n2 - CSV\n3 - JSON\n4 - quit")
                                    inp5 = select_option()
                                    if inp5 == 1:
                                        export_to_excel(output)
                                    elif inp5 == 2:
                                        export_to_csv(output)
                                    elif inp5 == 3:
                                        export_to_json(output)
                                    elif inp5 == 4:
                                        break
                                    else:
                                        error_type2()
                                        continue
                    elif inp1 == 2:
                        output = approximated_datetime(foreign, 'Date/Time')
                        if len(output) == 0:
                            print("{}{}No corresponding values found!{}".format(color.BOLD, color.RED, color.END))
                        else:
                            if len(output) > 100:
                                print("There are {} rows to display. Would you like to display them?".format(str(len(output))))
                                inp3 = input("Type yes/no\n > ").lower()
                                if inp3.startswith('y'):
                                    foreground = win32gui.GetForegroundWindow()
                                    win32gui.ShowWindow(foreground, win32con.SW_MAXIMIZE)
                                    pd.set_option("display.max_rows", len(output))
                                    print(output)
                            else:
                                foreground = win32gui.GetForegroundWindow()
                                win32gui.ShowWindow(foreground, win32con.SW_MAXIMIZE)
                                pd.set_option("display.max_rows", len(output))
                                print(output)
                            print("Would you like to save the results to a file?")
                            inp4 = input("Type yes/no\n > ").lower()
                            if inp4.startswith('y'):
                                while True:
                                    print("1 - Excel\n2 - CSV\n3 - JSON\n4 - quit")
                                    inp5 = select_option()
                                    if inp5 == 1:
                                        export_to_excel(output)
                                    elif inp5 == 2:
                                        export_to_csv(output)
                                    elif inp5 == 3:
                                        export_to_json(output)
                                    elif inp5 == 4:
                                        break
                                    else:
                                        error_type2()
                                        continue
                    elif inp1 == 3:
                        break
                    else:
                        error_type1()
                        continue

            ### EXIT - 15

            elif mode == 15:
                sys.exit(0)
        else:
            print("\n{}{}Invalid mode!\n{}".format(color.BOLD, color.RED, color.END))
            continue

if __name__ == '__main__':
    main()









