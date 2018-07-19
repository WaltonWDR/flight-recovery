# -*- coding: utf-8 -*-
"""
Created on Wed Jan 31 22:08:40 2018

@author: xmlon
"""
import numpy as np
import pandas as pd
# pandas introduction please refer to
# http://pandas.pydata.org/pandas-docs/stable/10min.html

## load data from recovery_result (by DeRui Wang)
def get_flights2(file_path):
    # file_path: the data file location
    # date_col: the columns that need to be parsed as dates (from string to date)
    # encoding: 'gbk' and other possible encodings 'UTF-16 LE','chinese', 'gb2312'
    date_col = ['计飞','实飞','计到','实到']
    # read a DataFrame from csv data file: flights
    flights = pd.read_csv(file_path,
                          parse_dates=date_col,
                          encoding='gbk')
    ## sort the Flights and delete nulls
    # Warning: the index in python starts from 0 (not 1)!
    # N_flights: the number of flights
    flights = flights.sort_values(by=['机号','计飞'],
                                     ascending = [True,True])
    flights = flights[flights.机号.notnull()]
#    flights = flights[flights.实飞.notnull()]
    N_flights = len(flights)
    # set the index of flight_seq as from 0 to N_flights-1
    flights.index = np.arange(N_flights)
    return(flights)

def get_flight_seq2(flights):
    # get flights sequence for each individual airplane
    flights_ID = flights.航班日期 + flights.航班号 + flights.起飞场
    N_flights = len(flights)
    # airplanes_ID: the ID for each airplane
    # N_airplanes: the number of distinct airplanes
    airplanes_tailNo = flights.机号
    airplanes_ID = airplanes_tailNo.drop_duplicates()
    N_airplanes = len(airplanes_ID)
    airplanes_ID.index = np.arange(N_airplanes)
    #
    # determing the flights sequence for each airplane
    i = 0
    airplanes_flights = {}
    for id in airplanes_ID:
        m = i
        while flights.机号[i] == id:
            i = i + 1
            if i > (N_flights - 1):
                break
        n = i
        airplanes_flights[id] = flights_ID[m:n]
        # be aware of m:n denotes m,m+1,...,n-2,n-1
    #
    len_airplanes_flights=[len(airplanes_flights[id]) for id in airplanes_ID]
    # start_idx: the starting index for each airplane's flights sequence 
    # assuming each airplane has at least one flight to fly
    start_idx = np.cumsum(len_airplanes_flights) 
    start_idx = start_idx.tolist()
    start_idx.insert(0,0) # insert 0 as the first index of start_idx
    #
    return({'airplanes_ID': airplanes_ID,
            'airplanes_flights': airplanes_flights,
            'start_idx': start_idx,
            'len_airplanes_flights': len_airplanes_flights})
