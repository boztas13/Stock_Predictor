#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov  6 15:36:05 2023

@author: berkoztas
"""
#backtesting.set_bokeh_output(notebook=False)
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import talib 
from backtesting import Backtest,Strategy
import backtesting
import sys
import os
import xlsxwriter
import pandas_ta as ta
import math
from binance.client import Client

def calculate_t3(data):
    
    ema1=hlcc.ewm(span=Tillson_T3.t3length, adjust = False).mean()
    ema2=ema1.ewm(span=Tillson_T3.t3length, adjust = False).mean()
    ema3=ema2.ewm(span=Tillson_T3.t3length, adjust = False).mean()
    ema4=ema3.ewm(span=Tillson_T3.t3length, adjust = False).mean()
    ema5=ema4.ewm(span=Tillson_T3.t3length, adjust = False).mean()
    ema6=ema5.ewm(span=Tillson_T3.t3length, adjust = False).mean()
    c1= -1 * Tillson_T3.a * Tillson_T3.a * Tillson_T3.a
    c2= 3 * Tillson_T3.a *Tillson_T3.a + 3 * Tillson_T3.a * Tillson_T3.a * Tillson_T3.a
    c3= -6 * Tillson_T3.a * Tillson_T3.a - 3 * Tillson_T3.a - 3 * Tillson_T3.a * Tillson_T3.a * Tillson_T3.a
    c4= 1 + 3 * Tillson_T3.a + Tillson_T3.a * Tillson_T3.a * Tillson_T3.a + 3 * Tillson_T3.a * Tillson_T3.a
    t3= c1 * ema6 + c2 * ema5 + c3 * ema4 + c4 * ema3
    return t3

def calculate_mavi(data):
    m10=talib.WMA(c,3)
    m20=talib.WMA(m10,5)
    m30=talib.WMA(m20,8)
    m40=talib.WMA(m30,13)
    m50=talib.WMA(m40,21)
    MAVW=talib.WMA(m50,34)
    return MAVW

def calculate_superTrend(data,period,multiplier):
    
    try:
       atr = talib.ATR(data.High, data.Low, data.Close, period)
    except:
        print("ATR calculation error")
        return False, False
    
    previous_final_upperband = 0
    previous_final_lowerband = 0
    final_upperband = 0
    final_lowerband = 0
    previous_close = 0
    previous_supertrend = 0
    supertrend = []
    supertrendc = 0
    
    

    for i in range(0, len(data.Close)):
       if np.isnan(data.Close[i]):
           pass
       else:
           highc = data.High[i]
           lowc = data.Low[i]
           atrc = atr[i]
           closec = data.Close[i]

           if math.isnan(atrc):
               atrc = 0

           basic_upperband = (highc + lowc) / 2 + multiplier * atrc
           basic_lowerband = (highc + lowc) / 2 - multiplier * atrc

           if basic_upperband < previous_final_upperband or previous_close > previous_final_upperband:
               final_upperband = basic_upperband
           else:
               final_upperband = previous_final_upperband

           if basic_lowerband > previous_final_lowerband or previous_close < previous_final_lowerband:
               final_lowerband = basic_lowerband
           else:
               final_lowerband = previous_final_lowerband

           if previous_supertrend == previous_final_upperband and closec <= final_upperband:
               supertrendc = final_upperband
           elif previous_supertrend == previous_final_upperband and closec >= final_upperband:
               supertrendc = final_lowerband
           elif previous_supertrend == previous_final_lowerband and closec >= final_lowerband:
               supertrendc = final_lowerband
           elif previous_supertrend == previous_final_lowerband and closec <= final_lowerband:
               supertrendc = final_upperband

           supertrend.append(supertrendc)
           previous_close = closec
           previous_final_upperband = final_upperband
           previous_final_lowerband = final_lowerband
           previous_supertrend = supertrendc
    return supertrend


class BinanceConnection:
    def __init__(self, file):
        self.connect(file)

    """ Creates Binance client """
    def connect(self, file):
        lines = [line.rstrip('\n') for line in open(file)]
        key = lines[0]
        secret = lines[1]
        self.client = Client(key, secret)

def optim_func(series):
    if series["# Trades"]<5:
        return -1
    return series["Equity Final [$]"] / series["Exposure Time [%]"]


class Tillson_T3(Strategy): 
    a=0.618
    t3length=8
    
    def init(self):
        
        self.T3=self.I(calculate_t3,self.data.Close)
        
    def next(self):
        global T3_Flag
        global T3_Flag_change
        T3_Flag_change+=1
        try:
            if self.T3[-1]> self.T3[-2] and self.T3[-2] < self.T3[-3] and not self.position.is_long:
                self.position.close()
                self.buy()
                T3_Flag=True
                T3_Flag_change=0
                
            
            elif self.T3[-1]<self.T3[-2] and self.T3[-2] > self.T3[-3] and self.position.is_long:
                self.position.close()
                T3_Flag=False
                T3_Flag_change=0
        except IndexError:
            pass
        

class MaviLim(Strategy):
    
    def init(self):
        self.Mavi=self.I(calculate_mavi,self.data.Close)
        
    def next(self):
        global Mavi_Flag
        global Mavi_Flag_change
        Mavi_Flag_change+=1
        try:
            if self.Mavi[-1]> self.Mavi[-2] and not self.position.is_long:
                self.position.close()
                self.buy()
                Mavi_Flag=True
                Mavi_Flag_change=0
                
            
            elif self.Mavi[-1]<self.Mavi[-2] and self.position.is_long:
                self.position.close()
                Mavi_Flag=False
                Mavi_Flag_change=0
        except IndexError:
            pass
        
class Super_Trend(Strategy):
    period=10
    multiplier=3
    
    def init(self):
        self.Super=self.I(calculate_superTrend,self.data,self.period,self.multiplier)
    def next(self):
        global Super_Flag
        global Super_Flag_change
        Super_Flag_change+=1
        try:
            if self.data.Close[-1]> self.Super[-1] and self.data.Close[-2] < self.Super[-2] and not self.position.is_long:
                self.position.close()
                self.buy()
                Super_Flag=True
                Super_Flag_change=0
                
            
            elif self.data.Close[-1]<self.Super[-1] and self.data.Close[-2] > self.Super[-2] and self.position.is_long:
                self.position.close()
                Super_Flag=False
                Super_Flag_change=0
        except IndexError:
            pass
        
f = open('banner.txt', 'r')
file_contents = f.read()
print (file_contents)
f.close()
print("BORSA KAPLANI V 0.1")

filename = 'credentials.txt'
connection = BinanceConnection(filename)

symbol = 'BTCUSDT'
interval = '4h'
limit = 2000

try:
    klines = connection.client.get_klines(symbol=symbol, interval=interval, limit=limit)
except Exception as exp:
    print(exp.status_code, flush=True)
    print(exp.message, flush=True)
  
T3_Flag=False
T3_Flag_change=0
Mavi_Flag=False
Mavi_Flag_change=0
Super_Flag=False
Super_Flag_change=0
tickers=["GUBRF.IS","FROTO.IS","VAKBN.IS","AKBNK.IS","SISE.IS","ASELS.IS","EREGL.IS",
         "GARAN.IS","KCHOL.IS","ALARK.IS","ISCTR.IS","KOZAL.IS","MGROS.IS","AEFES.IS",
         "OYAKC.IS","PETKM.IS","ARCLK.IS","GOODY.IS","SAHOL.IS","ENKAI.IS","VESTL.IS",
         "TCELL.IS","THYAO.IS","TUPRS.IS","YKBNK.IS","AKSEN.IS","SASA.IS",
         "HALKB.IS","PGSUS.IS","BIMAS.IS","TTKOM.IS","KOZAA.IS","TKFEN.IS","TOASO.IS"]


d={}
iter=0
features=["Stock","Equity Final [$]","# Trades","Win Rate [%]","T3","Signal Change",
          "Equity Final [$]M","# TradesM","Win Rate [%]M","Mavi","Signal ChangeM",
          "Equity Final [$]S","# TradesS","Win Rate [%]S","SuperTrend","Signal ChangeMS"]
results=pd.DataFrame(columns=features)
ticker_name=input("Stock Name:")

dict_list=[]
for i in tickers:
    d[i]=yf.Ticker(i).history(period="max")
    #d[i].drop(index=d[i].index[:1500], axis=0, inplace=True)
    #Drop first 1500 rows
    d[i]=d[i].tail(2000)
    hlcc=(d[i]["High"]+d[i]["Low"]+2*d[i]["Close"])/4
    hl=(d[i]["High"]+d[i]["Low"])/2
    c=d[i]["Close"]
   ################### Tilson T3 #############################
    bt_T3=Backtest(d[i], Tillson_T3,cash=10000)
    bt_T3.optimize(a=[0.618,0.7,0.8,0.98],
                t3length=range(5,17,3),
                maximize="Win Rate [%]")
    #ax=d[i]["Close"].tail(50).plot()
    T3_Stats=bt_T3.run()   
    equity_final_T3 = float("{:.2f}".format(T3_Stats["Equity Final [$]"]))
    win_rate_T3= float("{:.2f}".format(T3_Stats["Win Rate [%]"]))
    total_trades_T3 = T3_Stats["# Trades"]
    print(i)
    print(T3_Flag)
    if T3_Flag:
        signal_T3="Buy"
    else:
        signal_T3="Sell"
        
    ################### Tilson T3 #############################  
    
    ###################  MAVILIMW #############################
    bt_Mavi=Backtest(d[i],MaviLim,cash=10000)
    Mavi_Stats=bt_Mavi.run()
    equity_final_mavi= float("{:.2f}".format(Mavi_Stats["Equity Final [$]"]))
    win_rate_mavi= float("{:.2f}".format(Mavi_Stats["Win Rate [%]"]))
    total_trades_mavi = Mavi_Stats["# Trades"]
    
    if Mavi_Flag:
        signal_Mavi="Buy"
    else:
        signal_Mavi="Sell"
    ###################  MAVILIMW ############################
    
    ################## SUPER TREND ##########################
  
    bt_Super=Backtest(d[i],Super_Trend,cash=10000)
    bt_Super.optimize(period=range(6,20,2),
                      multiplier=[3,3.5,4],
                maximize="Win Rate [%]")
    Super_Stats=bt_Super.run()
    equity_final_super= float("{:.2f}".format(Super_Stats["Equity Final [$]"]))
    win_rate_super= float("{:.2f}".format(Super_Stats["Win Rate [%]"]))
    total_trades_super = Super_Stats["# Trades"]
    
    if Super_Flag:
        signal_Super="Buy"
    else:
        signal_Super="Sell"
       
    ################## SUPER TREND ##########################
    row_dict={features[0]:i,
              features[1]:equity_final_T3,
              features[2]:total_trades_T3,
              features[3]:win_rate_T3,
              features[4]:signal_T3,
              features[5]:T3_Flag_change,
              features[6]:equity_final_mavi,
              features[7]:total_trades_mavi,
              features[8]:win_rate_mavi,
              features[9]:signal_Mavi,
              features[10]:Mavi_Flag_change,
              features[11]:equity_final_super,
              features[12]:total_trades_super,
              features[13]:win_rate_super,
              features[14]:signal_Super,
              features[15]:Super_Flag_change
                  
              }
                
    dict_list.append(row_dict)
    iter+=1
    if i==f"{ticker_name}.IS":
        bt_T3.plot()
        print(T3_Stats)
        bt_Mavi.plot()
        print(Mavi_Stats)
        bt_Super.plot()
        print(Super_Stats)
        debug_T3=calculate_t3(d[i]);
        debug_Mavi=calculate_mavi(d[i])
        
        
        
color_formats = {'"Sell"': '#FF0000',
                 '"Buy"': '#00FF00',}
                
results=pd.DataFrame.from_dict(dict_list)
writer = pd.ExcelWriter('backtest.xlsx', engine='xlsxwriter')
results.to_excel(writer)
workbook = writer.book
worksheet = writer.sheets['Sheet1']
results.to_csv("backtest.csv",index=True,header=features,mode="a")

for val, color in color_formats.items():
    fmt = workbook.add_format({'font_color': color})
    worksheet.conditional_format(f'F2:P{len(tickers)+2}',
                                          {'type': 'cell',
                                           'criteria': '=',
                                           'value': val,
                                           'format': fmt})
writer.close()








        
        
  
    
    


