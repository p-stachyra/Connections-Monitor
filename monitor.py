
from ipwhois import *

import datetime
import numpy as np
import os
import pandas as pd
import socket
import sqlite3
import subprocess

class Colors:
    GREEN = '\u001b[38;5;82m'
    GREEN2 = '\u001b[38;5;84m'
    RED = '\u001b[38;5;196m'
    RED2 = '\u001b[38;5;9m'
    BOLD='\033[1m'
    END = '\033[0m'
    LIGHTBLUE='\u001b[38;5;45m'
    CYAN = '\033[96m'
    MAGNETA = '\033[35m'
    YELLOW = '\u001b[38;5;227m'
    YELLOW2 = '\u001b[38;5;220m'
    LIGHTGRAY = '\033[37m'
    ORANGE = '\u001b[38;5;202m'

class Monitor:

    def __init__(self):
        #Initiating : creating a log file and enabling colors
        os.system("netstat -ano -p tcp | findstr TCP > connections.log")
        self.current_datetime = datetime.datetime.now().isoformat(timespec='seconds')
        self.connector = sqlite3.connect('connections.db')

        self.newest_connections = pd.read_csv('connections.log', sep=r'\s+', header=None, names=['Protocol', 'local_host:port', 'remote_address', 'state', 'pid'])
        self.newest_connections.drop(columns=['Protocol'], inplace=True)

        x = lambda m: m.str.split(':', expand=True)
        new_df = x(self.newest_connections['local_host:port'])
        self.newest_connections['local_host'] = new_df[0]
        self.newest_connections['local_port'] = pd.to_numeric(new_df[1])

        new_df2 = x(self.newest_connections['remote_address'])
        self.newest_connections['remote_address'] = new_df2[0]
        self.newest_connections['remote_port'] = pd.to_numeric(new_df2[1])
        self.newest_connections = self.newest_connections[['local_host', 'local_port', 'remote_address', 'remote_port', 'state', 'pid']]
        self.newest_connections['timestamp'] = self.current_datetime
        

    def add_process(self):
        """Collects information about processes related to the connections. Adds 'process_name' column to the inititated dataframe containing all connections.
The program avoids being run in an elevated context, thus searching for the processes one by one, instead of displaying them with netstat"""

        proc_dict = dict()
        total_count = len(self.newest_connections['pid'].unique())
        count = 0
        for proc in self.newest_connections['pid'].unique():
            count += 1
            percent = round((count / total_count * 100))
            print('{}{}Identifying processes in progress. Accomplished: {}%{}'.format(Colors.GREEN,Colors.BOLD,percent,Colors.END), end='\r')
            output = subprocess.run(["powershell.exe", "-Command", f'Get-Process -Id {proc} | select-object -Property ProcessName | ft -HideTableHeaders'], capture_output=True, text=True).stdout.strip()
            proc_dict[proc] = output
        print()
        processes = pd.Series(proc_dict)
        processes_df = pd.DataFrame(processes.reset_index())
        processes_df.columns = ['pid', 'process_name']
        if 'process_name' in self.newest_connections:
            self.newest_connections = pd.merge(self.newest_connections, processes_df, on=['pid', 'process_name'], how='right')
        else:
            self.newest_connections = pd.merge(self.newest_connections, processes_df, on='pid', how='right')
        return self.newest_connections

    def local_connections(self, connector, save=True):
        """Returns a dataframe containing all local connections.
By default saves the new dataframe to the database file, unless 'save' parameter is set to False."""

        local = self.newest_connections[(self.newest_connections['remote_address'] == '0.0.0.0') | (self.newest_connections['remote_address'] == '127.0.0.1')]
        if save:
            try:
                local.to_sql('local_connections', connector, if_exists='append')
            except:
                print("Saving local connections failed.")
                return None
        return local

    def remote_connections(self):
        """Returns a dataframe containing all remote connections.
By default saves the new dataframe to the database file, unless 'save' parameter is set to False."""

        self.remote = self.newest_connections[~((self.newest_connections['remote_address'] == '0.0.0.0') | (self.newest_connections['remote_address'] == '127.0.0.1'))]
        return self.remote

    def whois(self, data):
        """Collects information about: 
        server name, 
        description - usually containing company's name 
        and country basing on provided IP addresses. 
        If a scalar value is provided as the 'data' parameter, it is automatically converted into a list"""

        ip_addresses = data
        if pd.api.types.is_scalar(ip_addresses):
            ip_addresses = [ip_addresses]
        domains = pd.DataFrame()
        local_hosts = []
        total_count = len(data)
        count = 0
        for ip in ip_addresses:
            try:
                count += 1
                percent = round((count / total_count * 100))
                print("{}{}Whois lookup in progress. Accomplished: {}%{}".format(Colors.GREEN,Colors.BOLD,percent,Colors.END), end='\r')
                response = IPWhois(ip)
                output = response.lookup_whois()
                domains_df = pd.json_normalize(output['nets'])
                domains_df['remote_address'] = ip
                df_whois = domains_df[['name', 'description', 'country', 'remote_address']]
                domains = domains.append(df_whois, ignore_index=True).fillna('N/A')
            except IPDefinedError as error:
                print(f"[ ! ] Exception info: {error}")
                local_hosts.append(ip)
                continue
            except:
                print("Error. The lookup failed.")
                raise SystemExit()
        print()
        final_df = pd.DataFrame(domains)
        if len(local_hosts) > 0:
            self.local_network_hosts = pd.DataFrame(local_hosts, columns=['remote_address'])
            for ip in self.local_network_hosts['remote_address'].unique():
                try:
                    hostname, alias, ip_addr = socket.gethostbyaddr(ip)
                    self.local_network_hosts.loc[(self.local_network_hosts['remote_address'] == ip), 'name'] = hostname
                except:
                    self.local_network_hosts.loc[(self.local_network_hosts['remote_address'] == ip), 'name'] = 'N/A'
                    continue
            self.local_network_hosts['description'] = "Local Network"
            self.local_network_hosts['country'] = "N/A"
            appended = final_df.append(self.local_network_hosts)
            appended.to_excel("output.xlsx")
            return appended
        else:
            return final_df
        

    def lookup(self, connector, save=True):
        """Merges the information on connections to remote hosts acquired using whois function.
By default saves the new dataframe to the database file, unless 'save' parameter is set to False."""

        unknown_conn = self.remote['remote_address'].unique()
        discovered = Monitor.whois(self,unknown_conn)
        discovered = discovered.drop_duplicates()
        self.remote = pd.merge(self.remote, discovered, on='remote_address', how='left')
        self.remote = self.remote.drop_duplicates(subset=['remote_address', 'remote_port', 'pid']).reset_index() 
        self.remote = self.remote.drop(columns=['index'])
        if save:
            try:
                self.remote.to_sql('connections', connector, if_exists='append')
            except ValueError as e:
                raise SystemExit()
        return self.remote
            

if __name__ == '__main__':
    monitor = Monitor()
    monitor.add_process()
    monitor.remote_connections()
    monitor.local_connections(monitor.connector)
    monitor.lookup(monitor.connector)
    

 
    
    