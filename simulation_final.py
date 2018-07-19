# -*- coding: utf-8 -*-
"""
Created on Mon Jul  9 20:50:52 2018

@author: wdr78
"""
import numpy as np
import pandas as pd
from suds.client import Client

#import datetime
#import sys
#from pandas import DataFrame

##################################################################################################################
#通过API将原始排班表及过站时间导入
def get_all_methods(client):
    return [method for method in client.wsdl.services[0].ports[0].methods]

def get_method_args(client, method_name):
    method = client.wsdl.services[0].ports[0].methods[method_name]
    input_params = method.binding.input
    return input_params.param_defs(method)

url = 'http://172.20.41.58:7777/ApiFlightMessage.svc?wsdl'
client = Client(url)
methods = get_all_methods(client)
args = get_method_args(client,'GetFlightInfoData')

def get_flight_data(start_time,end_time):
    result = client.service.GetFlightInfoData(start_time,end_time)
    len_1=len(result[0])#the number of flights per day
    len_2=len(result[0][0])#the number of code per flight
    flight_data=pd.DataFrame(np.zeros(len_1*len_2).reshape(len_1,len_2), 
                             columns=['实到','实飞','降落场','上座率','取消原因','承运人','变更原因',
                                      '延误原因','延误时间','起飞场','预到','预飞','航班日期','航班信息ID',
                                      '航班号','航班性质','航班状态','营销机型','备注','计到','计飞','机号'],dtype='str')
    for i in range(len_1):
        for j in range(len_2):
            flight_data.values[i,j]=result[0][i][j]
    return flight_data
start_time=input('原始排班表的开始时间（年-月-日）：')
end_time=input('原始排班表的结束时间（年-月-日）：')
flights=get_flight_data(start_time,end_time)
#flights=get_flight_data('2018-07-01','2018-07-02')
#date_col = ['计飞','计到','实飞','实到']
#flights=pd.read_csv('C:/Users/wdr78/Desktop/ceair_simulation/simulation/2018-7-1.csv',
#                    low_memory=False,parse_dates=date_col,keep_default_na=False,encoding='gbk')

result2 = client.service.GetAcrossTime()
len_3=len(result2[0])#the number of flights per day
len_4=len(result2[0][0])#the number of code per flight
quick_passtime=pd.DataFrame(np.zeros(len_3*len_4).reshape(len_3,len_4), columns=['Order','Page','PageSize',
                            'Sort','标准过站时间','新增时间','运行机型','机场名称','所属公司','大机型','机场三字码',
                            '机场四字码','主键ID','营销机型','机号','快速过站时间','更新时间'],dtype='str')
for i in range(len_3):
    for j in range(len_4):
        quick_passtime.values[i,j]=result2[0][i][j]
quick_passtime=quick_passtime[['机号','机场名称','快速过站时间']]
############################################################################################################
#将flights数据重排
column=['航班号', '机号', '起飞场', '降落场', '营销机型', '计飞', '计到', '实飞', '实到', '航班日期','上座率']
flights=flights[column]
for i in range(len(flights)):
    if flights.loc[i,'上座率']==None:
        flights.loc[i,'上座率']='100%'
flights['航班收益']=1
flights['旅客价值']=1
flights['VIP航班']=0
#VIP航班现在是随机设定的，每隔25个就有一个VIP航班
i=0
while i<len(flights):
    flights.loc[i,'VIP航班']=1
    i+=25
flights['状态']=None
flights['实飞']=flights['计飞']
flights['实到']=flights['计到']
f=flights['上座率'].str.strip("%").astype(float)/100
#将百分比转换为float
flights['上座率']=f
flights = flights.sort_values(by=['机号','计飞'],ascending = [True,True])
N_flights = len(flights)
flights.index = np.arange(N_flights)
#价值排序方程里的系数
a1=0.2;a2=0.3;a3=0.5
flights['价值排序']=a1*flights.上座率+a2*flights.航班收益+a3*flights.旅客价值
#最快过站时间
#quick_passtime=pd.read_csv('C:/Users/wdr78/Desktop/ceair_simulation/simulation/quick_acrosstime.csv',encoding='gbk')

#########################################################################################################
#获得受影响机场状态
#例子：虹桥，杭州，浦东，北京，东营机场受影响
base_airport=['虹桥','西安','南京','兰州','成都','浦东','合肥','昆明','青岛','武汉','南昌','广州',
              '太原','石家庄','北京']
two_airport=['虹桥','浦东']#两个特殊航站
##nowtime=pd.Timestamp(2018,7,1,6,00,00)
#nowtime=pd.Timestamp(start_time)#假设开始recovery工作的时间点
##dealtime=pd.Timestamp(2018,7,1,8,00,00)
#delta=datetime.timedelta(hours=2)
##可处理任务时间窗为起飞前的两个小时
#dealtime=nowtime+delta
dealtime=input('航班可开始调动的时间：')
dealtime=pd.Timestamp(dealtime)
flights=flights[flights.计飞>dealtime]
flights.index=np.arange(len(flights))

airport_state=pd.DataFrame(index=['开始时间','结束时间','进出港速率','取消延误比'])
number=input('受影响机场数量：')
for i in range(int(number)):
    j=i+1
    name=input('第%s个受影响机场名称:'%j)
    start_time=input('开始时间（年-月-日 时:分:秒）:')
    end_time=input('结束时间:')
    rate=float(input('进出港速率:'))
    ratio=float(input('取消延误比:'))
    airport_state[name]=[pd.Timestamp(start_time),pd.Timestamp(end_time),rate,ratio]
#airport_state['虹桥']=[pd.Timestamp('2018-07-01 8:00:00'),pd.Timestamp('2018-07-01 15:30:00'),0.3,0.6]
#airport_state['杭州']=[pd.Timestamp('2018-07-01 8:20:00'),pd.Timestamp('2018-07-01 14:30:00'),0.5,0.35]
#airport_state['浦东']=[pd.Timestamp('2018-07-01 8:10:00'),pd.Timestamp('2018-07-01 16:00:00'),0.3,0.45]
#airport_state['北京']=[pd.Timestamp('2018-07-01 7:00:00'),pd.Timestamp('2018-07-01 13:30:00'),0.35,0.6]
#airport_state['重庆']=[pd.Timestamp('2018-07-01 7:30:00'),pd.Timestamp('2018-07-01 14:30:00'),0.4,0.5]
airport_state=airport_state.T
normal_num=[]
for i in airport_state.index.tolist():
    normal_num.append(len(flights[(flights.起飞场==i)&(flights.计飞>airport_state.loc[i,'开始时间'])&
                                  (flights.计飞<airport_state.loc[i,'结束时间'])])+len(flights[(flights.降落场==i)&
                                  (flights.计到>airport_state.loc[i,'开始时间'])&(flights.计到<airport_state.loc[i,'结束时间'])]))
airport_state['正常通行量']=normal_num
airport_state=airport_state.sort_values(by='开始时间')

#####################################################################################################
#时间t时所有受影响的航班状态
def f_effectairport(t):
    effect_airportstate=airport_state[airport_state.开始时间<=t]
    #现阶段受影响的航站状态
    effect_airportstate=effect_airportstate[effect_airportstate.结束时间>t]
    effect_airport=effect_airportstate.index.tolist()
    return effect_airport

######################################################################################################
#取消规则
##A
def f_AB(effect_flights,flights):
    #因规则AB而取消的航班索引
    IndexA=pd.DataFrame(columns=['dep','arr'])
    IndexB_SHA=pd.DataFrame(columns=['dep','arr'])
    IndexB_PVG=pd.DataFrame(columns=['dep','arr'])
    for i in range(len(effect_flights)):
        tailnum=effect_flights.values[i][1]
        deptime=effect_flights.values[i][7]
        #受影响那个飞机的所有航班
        theairplane=flights[flights.机号==tailnum]
        #一个飞机航班串里受到影响的那个航班
        theflight=theairplane[theairplane.实飞==deptime]
        arrairport=theflight.values[0][3]
        #受到影响航班的索引
        theindex=theflight.index.tolist()[0]
        try:
            depairport=theairplane.loc[theindex-1,'起飞场']
            #VIP航班不取消
            if theairplane.loc[theindex-1,'VIP航班']==1:
                continue
        except:
            continue
        else:
            if arrairport in base_airport and arrairport==depairport:
                IndexA.loc[theindex-1]=[theindex-1,theindex]
            if arrairport=='浦东' and depairport=='虹桥':
                IndexB_SHA.loc[theindex-1]=[theindex-1,theindex]
            if arrairport=='虹桥' and depairport=='浦东':
                IndexB_PVG.loc[theindex-1]=[theindex-1,theindex]
    return IndexA,IndexB_SHA,IndexB_PVG

####################################################################################################
##CD
def f_CD(effect_flights,flights):
    IndexC=pd.DataFrame(columns=['dep','arr'])
    IndexD_SHA=pd.DataFrame(columns=['dep','arr'])
    IndexD_PVG=pd.DataFrame(columns=['dep','arr'])
    for i in range(len(effect_flights)):
        tailnum=effect_flights.values[i][1]
        deptime=effect_flights.values[i][7]
        #受影响那个飞机的所有航班
        theairplane=flights[flights.机号==tailnum]
        #一个飞机航班串里受到影响的那个航班
        theflight=theairplane[theairplane.实飞==deptime]
        depairport=theflight.values[0][2]
        arrairport=theflight.values[0][3]
        #受到影响航班的索引
        theindex=theflight.index.tolist()[0]
        try:
            arrairport2=theairplane.loc[theindex+1,'降落场']
            if theairplane.loc[theindex+1,'VIP航班']==1:
                continue
        except:
            continue
        else:
            if arrairport2==depairport and arrairport not in base_airport:
                IndexC.loc[theindex]=[theindex,theindex+1]
            if depairport=='虹桥' and arrairport2=='浦东' and arrairport not in base_airport:
                IndexD_SHA.loc[theindex]=[theindex,theindex+1]
            if depairport=='浦东' and arrairport2=='虹桥' and arrairport not in base_airport:
                IndexD_PVG.loc[theindex]=[theindex,theindex+1]
    return IndexC,IndexD_SHA,IndexD_PVG

####################################################################################################
##EF
def f_EF(effect_flights,flights):
    IndexE=pd.DataFrame(columns=['dep','mid','arr'])
    IndexF_SHA=pd.DataFrame(columns=['dep','mid','arr'])
    IndexF_PVG=pd.DataFrame(columns=['dep','mid','arr'])
    for i in range(len(effect_flights)):
        tailnum=effect_flights.values[i][1]
        deptime=effect_flights.values[i][7]
        #受影响那个飞机的所有航班
        theairplane=flights[flights.机号==tailnum]
        #一个飞机航班串里受到影响的那个航班
        theflight=theairplane[theairplane.实飞==deptime]
        depairport=theflight.values[0][2]
        arrairport=theflight.values[0][3]
        #受到影响航班的索引
        theindex=theflight.index.tolist()[0]
        try:
            arrairport2=theairplane.loc[theindex+1,'降落场']
            arrairport3=theairplane.loc[theindex+2,'降落场']
            if theairplane.loc[theindex+1,'VIP航班']==1 or theairplane.loc[theindex+2,'VIP航班']==1:
                continue
        except:
            continue
        else:
            if arrairport3==depairport and arrairport not in base_airport and  arrairport2 not in base_airport:
                IndexE.loc[theindex]=[theindex,theindex+1,theindex+2]
            if depairport=='虹桥' and arrairport3=='浦东' and arrairport not in base_airport and arrairport2 not in base_airport:
                IndexF_SHA.loc[theindex]=[theindex,theindex+1,theindex+2]
            if depairport=='浦东' and arrairport3=='虹桥' and arrairport not in base_airport and arrairport2 not in base_airport:
                IndexF_PVG.loc[theindex]=[theindex,theindex+1,theindex+2]
    return IndexE,IndexF_SHA,IndexF_PVG

####################################################################################################
##G
def f_G(effect_flights,flights):
    IndexG=pd.DataFrame(columns=['dep','arr'])
    for i in range(len(effect_flights)):
        tailnum=effect_flights.values[i][1]
        deptime=effect_flights.values[i][7]
        #受影响那个飞机的所有航班
        theairplane=flights[flights.机号==tailnum]
#        theairplane=theairplane[theairplane.计飞>=t]
        #一个飞机航班串里受到影响的那个航班
        theflight=theairplane[theairplane.实飞==deptime]
        arrairport=theflight.values[0][3]
        #受到影响航班的索引
        theindex=theflight.index.tolist()[0]
        try:
            depairport=theairplane.loc[theindex-1,'起飞场']
            if theairplane.loc[theindex-1,'VIP航班']==1:
                continue
        except:
            continue
        else:
            if arrairport==depairport and depairport not in base_airport :
                IndexG.loc[theindex-1]=[theindex-1,theindex]
    return IndexG

####################################################################################################
#用于后面航班价值的排序
def f_index_value(index_matrix):
    xxx=0
    index_value=pd.Series([])
    for i in index_matrix.index.tolist():
        for j in list(index_matrix.loc[i]):
            xxx+=flights.loc[j,'价值排序']
        index_value[i]=xxx
    return index_value

#####################################################################################################
#汇总模型
for airport in airport_state.index.tolist():
    cancel_num=int(airport_state.loc[airport,'正常通行量']*(1-airport_state.loc[airport,'进出港速率'])*airport_state.loc[airport,'取消延误比'])
    #需要取消的数量
    effect_flights=flights[(flights.起飞场==airport)&(flights.VIP航班!=1)&(flights.状态!='C')]
    effect_flights=effect_flights[(effect_flights.实飞>airport_state.loc[airport,'开始时间']) & (
            effect_flights.实飞<airport_state.loc[airport,'结束时间'])]
    #这个航站里受影响的起飞航班
    effect_flights2=flights[(flights.降落场==airport)&(flights.VIP航班!=1)&(flights.状态!='C')]
    effect_flights2=effect_flights2[(effect_flights2.实到>airport_state.loc[airport,'开始时间']) & (
            effect_flights2.实到<airport_state.loc[airport,'结束时间'])]
    #这个航站里受影响的降落航班
    effect_flights_index=effect_flights.index.tolist()+effect_flights2.index.tolist()
    #受影响的航班索引（起飞和降落）
    IndexA,IndexB_SHA,IndexB_PVG=f_AB(effect_flights,flights)
    IndexC,IndexD_SHA,IndexD_PVG=f_CD(effect_flights,flights)
    IndexE,IndexF_SHA,IndexF_PVG=f_EF(effect_flights,flights)
    IndexG=f_G(effect_flights,flights)
    cancelable_num=2*len(IndexA)+2*len(IndexB_SHA)+2*len(IndexB_PVG)+2*len(IndexC)+len(IndexD_SHA)+len(
            IndexD_PVG)+2*len(IndexE)+len(IndexF_SHA)+len(IndexF_PVG)+2*len(IndexG)
    #可取消的航班index
    #如果需要取消的大于可取消的，就把可取消的全部cancle
    if cancel_num>=cancelable_num:
        Index=list(IndexA.dep)+list(IndexA.arr)+list(IndexB_SHA.dep)+list(IndexB_SHA.arr)+list(IndexB_PVG.dep)+list(
                IndexB_PVG.arr)+list(IndexC.dep)+list(IndexC.arr)+list(IndexD_SHA.dep)+list(IndexD_SHA.arr)+list(
                        IndexD_PVG.dep)+list(IndexD_PVG.arr)+list(IndexE.dep)+list(IndexE.mid)+list(IndexE.arr)+list(
                                IndexF_SHA.dep)+list(IndexF_SHA.mid)+list(IndexF_SHA.arr)+list(IndexF_PVG.dep)+list(
                                        IndexF_PVG.mid)+list(IndexF_PVG.arr)+list(IndexG.dep)+list(IndexG.arr)
        flights.loc[Index,'状态']='C'
        delay_num=airport_state.loc[airport,'正常通行量']*(1-airport_state.loc[airport,'进出港速率'])-cancelable_num
        I=[]
        for i in effect_flights_index:
            if i not in Index:
                I.append(i)
        delay_index=flights.loc[I,:].sort_values(by=['价值排序','VIP航班'],ascending = [True,True]).index.tolist()
        flights.loc[delay_index,'状态']='D'
        #延误后的状态转移，该飞机的后续航班按照最小过站时间延误，直到恢复正常排班或时刻表内无后续航班
        delayed_index=[]
        for index in delay_index:
            if index not in delayed_index:
                tailnum=flights.loc[index,'机号']
                release_time=airport_state.loc[airport,'结束时间']
                time_gap=flights.loc[index,'实到']-flights.loc[index,'实飞']
                #如果该航班是在受影响机场起飞的，那他只能在该机场取消流控后起飞
                if flights.loc[index,'起飞场']==airport:
                    flights.loc[index,'实到']=release_time+time_gap
                    flights.loc[index,'实飞']=release_time
                else:#如果该航班是在受影响机场降落的，那他可以提前起飞，在该机场取消流控后降落
                    flights.loc[index,'实到']=release_time
                    flights.loc[index,'实飞']=release_time-time_gap
                #包括受影响航班的后续航班
                theflight1=flights[(flights.机号==tailnum)&(flights.index>=index)&(flights.状态!='C')]
                theflight2=flights[(flights.机号==tailnum)&(flights.index>index)&(flights.状态!='C')]
                #受影响飞机的后续航班索引(不包括他自己)
                theflight_index=theflight2.index.tolist()
                airportlist=quick_passtime[quick_passtime.机号==tailnum]['机场名称']
                j=0
                for i in theflight_index:
                    if flights.loc[i]['起飞场'] in airportlist:#求快速过站时间
                        passtime=quick_passtime[(quick_passtime.机号==tailnum)&(quick_passtime.机场名称==flights.loc[i]['起飞场'])].values[0,2]
                    else:
                        passtime=quick_passtime[(quick_passtime.机号==tailnum)&(quick_passtime.机场名称=='其他')].values[0,2]
                    if theflight1.values[j,8]+pd.Timedelta(minutes=passtime)>flights.loc[i]['实飞']:
                        time_gap=flights.loc[i,'实到']-flights.loc[i,'实飞']
                        flights.loc[i,'实到']=theflight1.values[j,8]+pd.Timedelta(minutes=passtime)+time_gap
                        flights.loc[i,'实飞']=theflight1.values[j,8]+pd.Timedelta(minutes=passtime)
                        j+=1
                        flights.loc[i,'状态']='D'
                        delayed_index.append(i)
                    else:
                        continue

    else:#需要取消的小于可取消的，按照价值排序来取消
        index_value=f_index_value(IndexA).append(f_index_value(IndexB_SHA)).append(f_index_value(IndexB_PVG)).append(
                f_index_value(IndexC)).append(f_index_value(IndexD_SHA)).append(f_index_value(IndexD_PVG)).append(
                        f_index_value(IndexE)).append(f_index_value(IndexF_SHA)).append(f_index_value(IndexF_PVG)).append(f_index_value(IndexG))
        index_value=index_value.sort_values()
        Index=[]
        lenth=0
        for i in index_value.index.tolist():
            if i in IndexA.index.tolist():
                Index+=list(IndexA.loc[i,:])
                lenth+=2
            elif i in IndexB_SHA.index.tolist():
                Index+=list(IndexB_SHA.loc[i,:])
                lenth+=2
            elif i in IndexB_PVG.index.tolist():
                Index+=list(IndexB_PVG.loc[i,:])
                lenth+=2
            elif i in IndexC.index.tolist():
                Index+=list(IndexC.loc[i,:])
                lenth+=2
            elif i in IndexD_SHA.index.tolist():
                Index+=list(IndexD_SHA.loc[i,:])
                lenth+=1
            elif i in IndexD_PVG.index.tolist():
                Index+=list(IndexD_PVG.loc[i,:])
                lenth+=1
            elif i in IndexE.index.tolist():
                Index+=list(IndexE.loc[i,:])
                lenth+=2
            elif i in IndexF_SHA.index.tolist():
                Index+=list(IndexF_SHA.loc[i,:])
                lenth+=1
            elif i in IndexF_PVG.index.tolist():
                Index+=list(IndexF_PVG.loc[i,:])
                lenth+=1
            else:
                Index+=list(IndexG.loc[i,:])
                lenth+=2
            if lenth>=cancel_num:
                continue
        flights.loc[Index,'状态']='C'
        
        #需要被延误的航班数
        delay_num=int(airport_state.loc[airport,'正常通行量']*(1-airport_state.loc[airport,'进出港速率']))-cancel_num
        I=[]
        for i in effect_flights_index:
            if i not in Index:
                I.append(i)
        delay_index=flights.loc[I,:].sort_values(by=['价值排序','VIP航班'],ascending = [True,True]).index.tolist()[:delay_num]
        flights.loc[delay_index,'状态']='D'
        #延误后的状态转移，该飞机的后续航班按照最小过站时间延误，直到恢复正常排班或时刻表内无后续航班
        delayed_index=[]
        for index in delay_index:
            if index not in delayed_index:
                tailnum=flights.loc[index,'机号']
                release_time=airport_state.loc[airport,'结束时间']
                #该航班的飞行时间
                time_gap=flights.loc[index,'实到']-flights.loc[index,'实飞']
                #如果该航班是在受影响机场起飞的，那他只能在该机场取消流控后起飞
                if flights.loc[index,'起飞场']==airport:
                    flights.loc[index,'实到']=release_time+time_gap
                    flights.loc[index,'实飞']=release_time
                else:#如果该航班是在受影响机场降落的，那他可以提前起飞，在该机场取消流控后降落
                    flights.loc[index,'实到']=release_time
                    flights.loc[index,'实飞']=release_time-time_gap
                #包括受影响航班的后续航班
                theflight1=flights[(flights.机号==tailnum)&(flights.index>=index)&(flights.状态!='C')]
                #不包括受影响航班的后续航班
                theflight2=flights[(flights.机号==tailnum)&(flights.index>index)&(flights.状态!='C')]
                #受影响飞机的后续航班索引
                theflight_index=theflight2.index.tolist()
                airportlist=quick_passtime[quick_passtime.机号==tailnum]['机场名称']
                j=0
                for i in theflight_index:
                    #求快速过站时间
                    if flights.loc[i,'起飞场'] in airportlist:
                        passtime=quick_passtime[(quick_passtime.机号==tailnum)&(
                                quick_passtime.机场名称==flights.loc[i,'起飞场'])].values[0,2]
                    else:
                        passtime=quick_passtime[(quick_passtime.机号==tailnum)&(quick_passtime.机场名称=='其他')].values[0,2]
                    if theflight1.values[j,8]+pd.Timedelta(minutes=passtime)>flights.loc[i,'实飞']:
                        time_gap=flights.loc[i,'实到']-flights.loc[i,'实飞']
                        flights.loc[i,'实到']=theflight1.values[j,8]+pd.Timedelta(minutes=passtime)+time_gap
                        flights.loc[i,'实飞']=theflight1.values[j,8]+pd.Timedelta(minutes=passtime)
                        j+=1
                        flights.loc[i,'状态']='D'
                        delayed_index.append(i)
                    else:
                        continue

flights.loc[flights.状态=='C','实飞']=None
flights.loc[flights.状态=='C','实到']=None

#####################################################################################################
#运行结果的输出
#取消航班量
Cn=len(flights[flights.状态=='C'])
#延误航班量
Dn=len(flights[flights.状态=='D'])
delay_gap=flights[flights.状态=='D'].实飞-flights[flights.状态=='D'].计飞
flights['延误时间']=delay_gap
#总延误时间
all_delay=pd.Timedelta(minutes=0)
for i in delay_gap.index:
    all_delay+=delay_gap[i]

seconds_gap=[]
for i in delay_gap.index.tolist():
    seconds_gap.append(delay_gap[i].total_seconds()/60)
#总价值损失
total_cost=sum(flights[flights.状态=='C'].价值排序)+1/360*sum(flights[flights.状态=='D'].价值排序*seconds_gap)
#结果存为csv文件
flights.to_csv('recovery_result.csv',encoding='gbk')

result=pd.DataFrame([])
result['取消航班量']=[Cn]
result['延误航班量']=[Dn]
result['总延误时间']=[all_delay]
result['总价值损失']=[total_cost]
#结果存为csv文件
result.to_csv('statistics.csv',encoding='gbk')