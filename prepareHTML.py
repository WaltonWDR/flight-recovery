# -*- coding: utf-8 -*-
"""
Created on Tue Mar  6 10:00:00 2018

@author: xmlon
"""
import pandas as pd
import os
from data_prep import get_flights2,get_flight_seq2

def writeHTMLtable2():
    ## load and prepare data
    # Get prepared flights from csv or txt data file
    # set file_path to the data file location in your computer
    #需要改动的文件路径
    file_path = 'C:/Users/wdr78/Desktop/ceair_simulation/simulation/recovery_result.csv'
    #################################################################################
    flights = get_flights2(file_path)
    #flights_ID = flights.航班日期 + flights.航班号 + flights.起飞场
    
    airplanes_info = get_flight_seq2(flights)
    airplanes_ID = airplanes_info['airplanes_ID']
    start_idx = airplanes_info['start_idx']
    len_airplanes_flights = airplanes_info['len_airplanes_flights']
    
    N_airplanes = len(airplanes_ID)
    del airplanes_info # delete airplanes_info
    
    ## calculate the css style values
    # .flight {position: relative;}
    # style = "right:dt; width:ft"
    
    N_flights = len(flights)
    N = N_flights
#    bt = pd.Timestamp(2018,7,1,0,0,0) # bt: base time
    bt=pd.Timestamp(min(flights.航班日期))
    dt = [flights.计飞[i] - bt for i in range(N) ] # dt: delta time
    ft = [flights.计到[i]-flights.计飞[i] for i in range(N) ] # ft: fly timespan
    # warning: flights.计到[i] < flights.计飞[i] for some i, i.e., cancelled flights
    
    c_idx = [ 24*dt[i].components.days + dt[i].components.hours for i in range(N)]
    c_residual_minutes = [dt[i].components.minutes for i in range(N)]
    c_fly_timespan = [ft[i].seconds/60 for i in range(N)]
    c_dep_time = [str(flights.计飞[i].hour)+':'+str(flights.计飞[i].minute) for i in range(N)]
    c_arr_time = [str(flights.计到[i].hour)+':'+str(flights.计到[i].minute) for i in range(N)]
    
    flights['td_index'] = pd.Series(c_idx,index = flights.index)
    flights['residual_minutes'] = pd.Series(c_residual_minutes,index = flights.index)
    flights['fly_timespan'] = pd.Series(c_fly_timespan,index = flights.index)
    flights['dep_time'] = pd.Series(c_dep_time,index = flights.index)
    flights['arr_time'] = pd.Series(c_arr_time,index = flights.index)
    
    # prepare HTML table
    # td: table data for HTML table element <td></td>
    td = []
    for i in range(N_airplanes):
        td.append([])
        for j in range(72):
            # 72 is for 72 hours of three days
            td[i].append('<td></td>' )
    
    for i in range(N_airplanes):
        # find the corresponding cell index
        # <script>
        #  document.getElementById('flights_table').rows[i].cells[jj]
        # </script>
        #
        # the starting index for each flights sequence by airplane
        s = start_idx[i] 
        # be aware of the definition of idx_fs
        n = len_airplanes_flights[i]
        
        for j in range(n):
            # jj for the col index of the presenting html table
            jj = flights.td_index[s+j]
            
            txt = '<div class="flight to-fly" style="left:'
            
            align_left = (flights.residual_minutes[s+j]/60)*100
            
            txt = txt + str(align_left) + 'px;'
            
            width = (flights.fly_timespan[s+j]/60)*100
            
            txt = txt + 'width:' + str(width) + 'px;">'
            
            txt = txt + '<div class="plan-dep">'
            txt = txt + flights.dep_time[s+j]
            txt = txt + '</div>'
            txt = txt + '<div class="flight-no">'
            txt = txt + flights.航班号[s+j]
            txt = txt + '</div>'
            txt = txt + '<div class="plan-arr">'
            txt = txt + flights.arr_time[s+j]
            txt = txt + '</div>'
            txt = txt + '</div>'
            td[i][jj] = '<td>' + txt + '</td>'
        
    table_html ='<table id = "flight_table">'
    for i in range(N_airplanes):
        table_html = table_html + '<tr>'
        for j in range(72):
            table_html = table_html + td[i][j]
        table_html = table_html + '</tr>'
    table_html = table_html + '</table>'
    
#    tablefile = open("table_html2.txt","w")
#    tablefile.write(table_html)
#    tablefile.close()
    
    return(table_html)

table_html2 = writeHTMLtable2()

html_part1=open('html_part1.txt',encoding='gbk')
html_part2=open('html_part2.txt',encoding='gbk')
os.remove('gante_simulation.html')
f=open('gante_simulation.html','w')
for line in html_part1:
    f.writelines(line)
f.write('\n')
f.write('      ')
f.writelines(table_html2)
for line in html_part2:
    f.writelines(line)
f.close()