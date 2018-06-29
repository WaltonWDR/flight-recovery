# -*- coding: utf-8 -*-
"""
Created on Mon May 21 20:32:18 2018

@author: wdr78
"""
import numpy as np
import pandas as pd
date_col = ['计飞','计到','实飞','实到']
flights = pd.read_csv('C:/Users/wdr78/Desktop/ceair_simulation/simulation/2018-01-17.csv',low_memory=False,parse_dates=date_col,keep_default_na=False,encoding='gbk')
quick_passtime=pd.read_csv('C:/Users/wdr78/Desktop/ceair_simulation/simulation/quick_acrosstime.csv',encoding='gbk')
f=flights['上座率'].str.strip("%").astype(float)/100
flights['上座率']=f#将百分比转换为float
flights = flights.sort_values(by=['机号','计飞'],ascending = [True,True])
N_flights = len(flights)
flights.index = np.arange(N_flights)
#nowTime=pd.Timestamp(2100,3,4)
#x=1
#nowTime+pd.Timedelta(hours=x)
#设定飞机初始状态
机号=[]
for name, group in flights.groupby('机号'):
    机号.append(name)
flight = dict(list(flights.groupby('机号')))
t1=[]
for tailnum in 机号:
    t1.append(flight[tailnum].values[0][7])
airplane_state=pd.DataFrame({'第几次任务':np.zeros(len(机号)),'是否正在飞行':np.zeros(len(机号)),'下次动作时间':t1},index=机号)
del flight

a1=0.5;a2=1;a3=1.5#价值排序方程里的系数
flights['价值排序']=a1*flights.上座率+a2*flights.航班收益+a3*flights.旅客价值
#虹桥，杭州，浦东，北京，东营机场受影响
base_airport=['虹桥','西安','南京','兰州','成都','浦东','合肥','昆明','青岛','武汉','南昌','广州','太原','石家庄','北京']
two_airport=['虹桥','浦东']#两个特殊航站
nowtime=pd.Timestamp(2018,1,17,4,00,00)#假设开始recovery工作的时间点
dealtime=pd.Timestamp(2018,1,17,6,00,00)#可处理任务时间窗为起飞前的两个小时
flights=flights[flights.计飞>dealtime]

airport_state=pd.DataFrame(index=['开始时间','结束时间','进出港速率','取消延误比'])
airport_state['虹桥']=[pd.Timestamp('2018-01-17 8:00:00'),pd.Timestamp('2018-01-17 15:30:00'),0.3,0.5]
airport_state['杭州']=[pd.Timestamp('2018-01-17 8:20:00'),pd.Timestamp('2018-01-17 14:30:00'),0.5,0.5]
airport_state['浦东']=[pd.Timestamp('2018-01-17 8:10:00'),pd.Timestamp('2018-01-17 16:00:00'),0.3,0.5]
airport_state['北京']=[pd.Timestamp('2018-01-17 7:00:00'),pd.Timestamp('2018-01-17 13:30:00'),0.8,0.5]
airport_state['重庆']=[pd.Timestamp('2018-01-17 7:30:00'),pd.Timestamp('2018-01-17 14:30:00'),0.4,0.5]
airport_state=airport_state.T
normal_num=[]
for i in airport_state.index.tolist():
    normal_num.append(len(flights[(flights.起飞场==i)&(flights.计飞>airport_state.loc[i]['开始时间'])&(flights.计飞<airport_state.loc[i]['结束时间'])])+len(flights[(flights.降落场==i)&(flights.计到>airport_state.loc[i]['开始时间'])&(flights.计到<airport_state.loc[i]['结束时间'])]))
airport_state['正常通行量']=normal_num
airport_state=airport_state.sort_values(by='开始时间')
def f_effectairport(t):#时间t时所有受影响的航班状态
    effect_airportstate=airport_state[airport_state.开始时间<=t]
    effect_airportstate=effect_airportstate[effect_airportstate.结束时间>t]#现阶段受影响的航站状态
    effect_airport=effect_airportstate.index.tolist()
    return effect_airport
######################################################################################################
#取消规则
##A
def f_AB(effect_flights,flights):
    IndexA=pd.DataFrame(columns=['dep','arr']);IndexB_SHA=pd.DataFrame(columns=['dep','arr']);IndexB_PVG=pd.DataFrame(columns=['dep','arr'])#因规则AB而取消的航班索引
    for i in range(len(effect_flights)):
        tailnum=effect_flights.values[i][1]
        deptime=effect_flights.values[i][7]
        theairplane=flights[flights.机号==tailnum]#受影响那个飞机的所有航班
        theflight=theairplane[theairplane.实飞==deptime]#一个飞机航班串里受到影响的那个航班
        arrairport=theflight.values[0][3]
        theindex=theflight.index.tolist()[0]#受到影响航班的索引
        try:
            depairport=theairplane.loc[theindex-1,'起飞场']
            if theairplane.loc[theindex-1,'VIP航班']==1:#VIP航班不取消
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
    IndexC=pd.DataFrame(columns=['dep','arr']);IndexD_SHA=pd.DataFrame(columns=['dep','arr']);IndexD_PVG=pd.DataFrame(columns=['dep','arr'])
    for i in range(len(effect_flights)):
        tailnum=effect_flights.values[i][1]
        deptime=effect_flights.values[i][7]
        theairplane=flights[flights.机号==tailnum]#受影响那个飞机的所有航班
        theflight=theairplane[theairplane.实飞==deptime]#一个飞机航班串里受到影响的那个航班
        depairport=theflight.values[0][2]
        arrairport=theflight.values[0][3]
        theindex=theflight.index.tolist()[0]#受到影响航班的索引
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
    IndexE=pd.DataFrame(columns=['dep','mid','arr']);IndexF_SHA=pd.DataFrame(columns=['dep','mid','arr']);IndexF_PVG=pd.DataFrame(columns=['dep','mid','arr'])
    for i in range(len(effect_flights)):
        tailnum=effect_flights.values[i][1]
        deptime=effect_flights.values[i][7]
        theairplane=flights[flights.机号==tailnum]#受影响那个飞机的所有航班
        theflight=theairplane[theairplane.实飞==deptime]#一个飞机航班串里受到影响的那个航班
        depairport=theflight.values[0][2]
        arrairport=theflight.values[0][3]
        theindex=theflight.index.tolist()[0]#受到影响航班的索引
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
    IndexG=pd.DataFrame(columns=['dep','arr']);
    for i in range(len(effect_flights)):
        tailnum=effect_flights.values[i][1]
        deptime=effect_flights.values[i][7]
        theairplane=flights[flights.机号==tailnum]#受影响那个飞机的所有航班
#        theairplane=theairplane[theairplane.计飞>=t]
        theflight=theairplane[theairplane.实飞==deptime]#一个飞机航班串里受到影响的那个航班
        arrairport=theflight.values[0][3]
        theindex=theflight.index.tolist()[0]#受到影响航班的索引
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
#while sum(airplane_state.第几次任务)<len(flights[flights.状态!='C']) or min(airplane_state.下次动作时间)<nowTime:
#    flights_nocancel=flights[flights.状态!='C']
#    t=min(airplane_state.下次动作时间)
#    effect_airportstate=f_effectairport(airport_state,t)#时间t时所有受影响的航站状态
#    effect_airportstate_fix=f_effectairport(airport_state_fix,t)#不随事件处理而更新的航站状态
#    effect_airport_fix=effect_airportstate_fix.index#不随事件处理而更新的航站
#    if len(effect_airportstate)==0:#如果该时间没有受影响的航站，按照事先的排班任务执行
#        tailnum=airplane_state[airplane_state.下次动作时间==t].index[0]
#        airplane_state.loc[tailnum,'是否正在飞行']=(airplane_state.loc[tailnum,'是否正在飞行']+1)%2
#        if airplane_state.loc[tailnum,'是否正在飞行']==1:#正在飞行
#            xxx=flights_nocancel[flights_nocancel.机号==tailnum].index.values[int(airplane_state.loc[tailnum,'第几次任务'])-1]
#            #xxx正在飞行那个航班的索引
#            flights.loc[xxx,'实飞']=t
#            airplane_state.loc[tailnum,'第几次任务']+=1
#            airplane_state.loc[tailnum,'下次动作时间']=flights_nocancel[flights_nocancel.机号==tailnum].values[int(airplane_state.loc[tailnum,'第几次任务'])-1][8]
#        else:#降落了
#            if airplane_state.loc[tailnum,'第几次任务']>=len(flights_nocancel[flights_nocancel.机号==tailnum]):
#                xxx=flights_nocancel[flights_nocancel.机号==tailnum].index.values[int(airplane_state.loc[tailnum,'第几次任务'])-1]
#                flights.loc[xxx,'实到']=t
#                airplane_state.loc[tailnum,'下次动作时间']=nowTime
#            else:
#                airplane_state.loc[tailnum,'下次动作时间']=flights_nocancel[flights_nocancel.机号==tailnum].values[int(airplane_state.loc[tailnum,'第几次任务'])][7]
#                xxx=flights_nocancel[flights_nocancel.机号==tailnum].index.values[int(airplane_state.loc[tailnum,'第几次任务']-1)]
#                flights.loc[xxx,'实到']=t

for airport in airport_state.index.tolist():
    cancel_num=int(airport_state.loc[airport]['正常通行量']*(1-airport_state.loc[airport]['进出港速率'])*airport_state.loc[airport]['取消延误比'])
    #需要取消的数量
    effect_flights=flights[(flights.起飞场==airport)&(flights.VIP航班!=1)&(flights.状态!='C')]
    effect_flights=effect_flights[(effect_flights.实飞>airport_state.loc[airport]['开始时间']) & (effect_flights.实飞<airport_state.loc[airport]['结束时间'])]
    #这个航站里受影响的起飞航班
    effect_flights2=flights[(flights.降落场==airport)&(flights.VIP航班!=1)&(flights.状态!='C')]
    effect_flights2=effect_flights2[(effect_flights2.实到>airport_state.loc[airport]['开始时间']) & (effect_flights2.实到<airport_state.loc[airport]['结束时间'])]
    #这个航站里受影响的降落航班
    effect_flights_index=effect_flights.index.tolist()+effect_flights2.index.tolist()
    #受影响的航班索引（起飞和降落）
    IndexA,IndexB_SHA,IndexB_PVG=f_AB(effect_flights,flights)
    IndexC,IndexD_SHA,IndexD_PVG=f_CD(effect_flights,flights)
    IndexE,IndexF_SHA,IndexF_PVG=f_EF(effect_flights,flights)
    IndexG=f_G(effect_flights,flights)
    cancelable_num=2*len(IndexA)+2*len(IndexB_SHA)+2*len(IndexB_PVG)+2*len(IndexC)+len(IndexD_SHA)+len(IndexD_PVG)+2*len(IndexE)+len(IndexF_SHA)+len(IndexF_PVG)+2*len(IndexG)
    #可取消的航班index
    if cancel_num>=cancelable_num:#如果需要取消的大于可取消的，就把可取消的全部cancle
        Index=list(IndexA.dep)+list(IndexA.arr)+list(IndexB_SHA.dep)+list(IndexB_SHA.arr)+list(IndexB_PVG.dep)+list(IndexB_PVG.arr)+list(IndexC.dep)+list(IndexC.arr)+list(IndexD_SHA.dep)+list(IndexD_SHA.arr)+list(IndexD_PVG.dep)+list(IndexD_PVG.arr)+list(IndexE.dep)+list(IndexE.mid)+list(IndexE.arr)+list(IndexF_SHA.dep)+list(IndexF_SHA.mid)+list(IndexF_SHA.arr)+list(IndexF_PVG.dep)+list(IndexF_PVG.mid)+list(IndexF_PVG.arr)+list(IndexG.dep)+list(IndexG.arr)
        flights.loc[Index,'状态']='C'
        delay_num=airport_state.loc[airport]['正常通行量']*(1-airport_state.loc[airport]['进出港速率'])-cancelable_num
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
                tailnum=flights.loc[index]['机号']
                release_time=airport_state.loc[airport]['结束时间']
                time_gap=flights.loc[index,'实到']-flights.loc[index,'实飞']
                if flights.loc[index,'起飞场']==airport:#如果该航班是在受影响机场起飞的，那他只能在该机场取消流控后起飞
                    flights.loc[index,'实到']=release_time+time_gap
                    flights.loc[index,'实飞']=release_time
                else:#如果该航班是在受影响机场降落的，那他可以提前起飞，在该机场取消流控后降落
                    flights.loc[index,'实到']=release_time
                    flights.loc[index,'实飞']=release_time-time_gap
                theflight1=flights[(flights.机号==tailnum)&(flights.index>=index)&(flights.状态!='C')]#包括受影响航班的后续航班
                theflight2=flights[(flights.机号==tailnum)&(flights.index>index)&(flights.状态!='C')]
                theflight_index=theflight2.index.tolist()#受影响飞机的后续航班索引(不包括他自己)
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
#延误后的状态转移,被延误后，该飞机后面的航班依次延误
#        delayed_index=[]
#        for i in delay_index:
#            if i not in delayed_index:
#                tailnum=flights.loc[i,'机号']
#                time_gap=airport_state.loc[airport]['结束时间']-flights.loc[i,'实飞']
#                yyy=flights[(flights.机号==tailnum)&(flights.index>=i)&(flights.状态!='C')].index.tolist()
#                delayed_index+=yyy
#                #该飞机的后续航班索引
#                for zzz in yyy:
#                    flights.loc[zzz,'实飞']+=time_gap
#                    flights.loc[zzz,'实到']+=time_gap
#                    flights.loc[zzz,'状态']='D'
    else:#需要取消的小于可取消的，按照价值排序来取消
        index_value=f_index_value(IndexA).append(f_index_value(IndexB_SHA)).append(f_index_value(IndexB_PVG)).append(f_index_value(IndexC)).append(f_index_value(IndexD_SHA)).append(f_index_value(IndexD_PVG)).append(f_index_value(IndexE)).append(f_index_value(IndexF_SHA)).append(f_index_value(IndexF_PVG)).append(f_index_value(IndexG))
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
        
        delay_num=int(airport_state.loc[airport]['正常通行量']*(1-airport_state.loc[airport]['进出港速率']))-cancel_num#需要被延误的航班数
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
                tailnum=flights.loc[index]['机号']
                release_time=airport_state.loc[airport]['结束时间']
                time_gap=flights.loc[index,'实到']-flights.loc[index,'实飞']#该航班的飞行时间
                if flights.loc[index,'起飞场']==airport:#如果该航班是在受影响机场起飞的，那他只能在该机场取消流控后起飞
                    flights.loc[index,'实到']=release_time+time_gap
                    flights.loc[index,'实飞']=release_time
                else:#如果该航班是在受影响机场降落的，那他可以提前起飞，在该机场取消流控后降落
                    flights.loc[index,'实到']=release_time
                    flights.loc[index,'实飞']=release_time-time_gap
                theflight1=flights[(flights.机号==tailnum)&(flights.index>=index)&(flights.状态!='C')]#包括受影响航班的后续航班
                theflight2=flights[(flights.机号==tailnum)&(flights.index>index)&(flights.状态!='C')]#不包括受影响航班的后续航班
                theflight_index=theflight2.index.tolist()#受影响飞机的后续航班索引
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
#被延误后，该飞机后面的航班依次延误
#        delayed_index=[]
#        for i in delay_index:
#            if i not in delayed_index:
#                tailnum=flights.loc[i,'机号']
#                time_gap=airport_state.loc[airport]['结束时间']-flights.loc[i,'实飞']
#                yyy=flights[(flights.机号==tailnum)&(flights.index>=i)&(flights.状态!='C')].index.tolist()
#                #该飞机的后续航班索引
#                delayed_index+=yyy
#                for zzz in yyy:
#                    flights.loc[zzz,'实飞']+=time_gap
#                    flights.loc[zzz,'实到']+=time_gap
#                    flights.loc[zzz,'状态']='D'
flights.loc[flights.状态=='C','实飞']=None
flights.loc[flights.状态=='C','实到']=None
#####################################################################################################
Cn=len(flights[flights.状态=='C'])
Dn=len(flights[flights.状态=='D'])
flights.to_csv('recovery_result.csv',encoding='gbk')
###################################################################################################
#switch case
