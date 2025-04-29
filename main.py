############ Creator ############
# Jokela Vili-Pekka
# 29.4.2024
# Simulates boiler temperature based on outdoor temperature and exchange prices.
#################################
'''
Be carefule!!! In my computer it takes approx 15seconds to simulate one year data twice.
And this code simulates boiler temp for every minute in one year. Data can be changed in handleData.py file
'''
from time import sleep
from datetime import datetime,timedelta

from handleData import prices
import pandas as pd
import matplotlib.pyplot as plt

#create table for aquired data from simulation
exchangedf = pd.DataFrame(columns=["date","price","energy_used","cost","boilerTemp"])
exchangedf.set_index("date",inplace=True)
exchangedf.index.name = "Datetime"
exchangedf.Name = "WithExchangePrices"
no_Exchangedf = pd.DataFrame(columns=["date","price","energy_used","cost","boilerTemp"])
no_Exchangedf.set_index("date",inplace=True)
no_Exchangedf.index.name = "Datetime"
no_Exchangedf.Name = "WithOutExchangePrices"
dataframes = [exchangedf,no_Exchangedf]

BOILER_START_TEMP = 60  #Start temperature of boiler.
MAX_TEMP = 80           #Boiler max temperature
LOW_TEMP = 50           #Boiler minium temperature
BOILERCAPACITY = 2000   #Boiler capacity
WATERHEATCAPACITY = 4186    #J/(kg°C)

HEATINGPOWER = 12     #kWh (WattHours) 
HEATINGPOWER_W = HEATINGPOWER * 1000

YEARLY_CONSUMPTION = 64_000 * 1000 #kWh to Wh. Value changed to present approx 16kWh yearly consumption. (energy consumption is changed depending on outdoor temperature)
DAILY_CONSUMPTION = YEARLY_CONSUMPTION / 365
HOURLY_CONSUMPTION = DAILY_CONSUMPTION / 24
MINUTE_CONSUMPTION = HOURLY_CONSUMPTION / 60
SECOND_CONSUMPTION = MINUTE_CONSUMPTION / 60
CONSTANT_CONSUMPTION = SECOND_CONSUMPTION #Wh

# Shower water heating need == 8C --> 37C        1000l boiler 1C = 4 186 000
COLD_WATER_TEMP = 8     #C
USED_WATER_TEMP = 37    #C
SHOWER_TIME = 10        #minutes
WATER_FLOW = 8          #l/min
# Economic shower prox 8l/min 10 min = 80l
waterUsed = SHOWER_TIME * WATER_FLOW
# 80l*4186 = 334 880
showerConsumption = waterUsed * WATERHEATCAPACITY
# temperature decreases 334 880 * (37-8) / 4 186 000 = 2,32 C
temperatureDecrease = showerConsumption * (USED_WATER_TEMP - COLD_WATER_TEMP) / (BOILERCAPACITY * WATERHEATCAPACITY)

#One year changed to seconds.
YEAR = 1
DAYS = YEAR * 365
HOURS = DAYS * 24
MINUTES = HOURS * 60
SECONDS = MINUTES * 60

SECOND = 1
MINUTE = SECOND * 60
HOUR = MINUTE * 60

# temp = [20,15,10,5,0,-5,-10,-15,-20,-25,-30,-35,40] #for percentage test
min_temp = -40
max_temp = 20
dt_temp = max_temp - min_temp

#maps consumption percentage based on outdoor temperature. (-40 = 100% and 20 = 0%)
def percentage(t):

    if t < min_temp:
        return 100
    elif t > max_temp:
        return 0
    else:
        return (max_temp - t) / dt_temp

def main():
    data = prices() #get price and temp data from handleData
    for counter,dataframe in enumerate(dataframes):
        heatingTime = 0 #to count energy used.
        boilerTemp = BOILER_START_TEMP  #init start temp to boiler
        low_temp_minutes = 0        # to calculate how many minutes is heated with LOW_TEMP to keep boiler at miniun level
        cheap_temp_minutes = 0      # same for cheaper hours.
    
        for date,temp,price in data.itertuples():   #iterates through hours in year
            # print(date,temp,price)
            cheapest = 999999 #cheapest hour declared enough high.
            # when the cheapest hour is. 
            day = None
            # how many hours is looked forward.
            lookahead=0
            #based boiler temperature declaring how many hours can be looked forward for heating boiler with cheapest prices.
            if counter == 0:
                exchangePricesOn = True
            else:
                exchangePricesOn = False
            if exchangePricesOn:
                if boilerTemp < 55:
                    lookahead=1
                elif boilerTemp < 60:
                    lookahead=2
                elif boilerTemp < 65:
                    lookahead=3
                elif boilerTemp < 70:
                    lookahead=4
                elif boilerTemp < 75:
                    lookahead=5
                else:
                    lookahead=6
            for i,j,k in data[date:date+timedelta(hours=lookahead)].itertuples(): #iters lookahead amount of hours forward.
                if k < cheapest:    #if cheapest hour is found. refresh it's time and price.
                    cheapest = k
                    day = i
            
            
            if date.hour == 19: # triggers everyday in hour 19
                # decreases boiler temperature by 10 min shower.
                boilerTemp -= temperatureDecrease

            for i in range(int (MINUTE)):# iterates every minute in hour
                consumption = percentage(temp) * CONSTANT_CONSUMPTION * 60 * 3600   #percentage depends from outdoor temperature.
                boilerTemp -= consumption / (BOILERCAPACITY * WATERHEATCAPACITY)    #decreases boiler temp based on outdoor temp.
                if boilerTemp < MAX_TEMP and (date == day or price < 0):   # if boiler temp is below MAX_TEMP and cheapest hour is now. allow heating.
                    cheap_temp_minutes += 1 #count heating minutes
                    
                    boilerTemp += HEATINGPOWER_W * 60 / (BOILERCAPACITY * WATERHEATCAPACITY)    #Heating on. increase boiler temp based on heating power and boiler capasity.
                    heatingTime += 60       #count heating time to calculate used energy.

                elif boilerTemp < LOW_TEMP and price < 20: #keeps boiler temperature at declared min level. Triggered if now is not the cheap hour.
                    low_temp_minutes += 1
                    boilerTemp += HEATINGPOWER_W * 60 / (BOILERCAPACITY * WATERHEATCAPACITY)
                    heatingTime += 60
                elif boilerTemp < LOW_TEMP - 10:
                    low_temp_minutes += 1
                    boilerTemp += HEATINGPOWER_W * 60 / (BOILERCAPACITY * WATERHEATCAPACITY)
                    heatingTime += 60
            #Saves hour heating data. to df. index is date.
            dataframe.loc[date] = [price,heatingTime*(HEATINGPOWER/60/60),heatingTime * (HEATINGPOWER/60/60) * price,boilerTemp]
            #index = "date","price","energy_used",                 "cost",                                   "boilerTemp"]
            heatingTime = 0
    
    # for date,price,energy_used,cost,boilerTemp in exchangedf.itertuples():
    #     print(date,price,energy_used,cost,boilerTemp)
    for dataframe in dataframes:
        print("Dataframe name:",dataframe.Name)
        print(f"TotalCost: {dataframe["cost"].sum()/100:.2f}","€")
        print(f"EnergyUsed: {dataframe["energy_used"].sum():.2f} kWh")
        print("MedianPrice:",dataframe["price"].median())

        #printing shorter period to see chart more clear
        shorter = dataframe["2024-02-01":"2024-02-15"]

        plt.figure(figsize=(12, 6))

        
        plt.plot(shorter.index, shorter["price"], label="Price (c/kWh)")
        plt.plot(shorter.index, shorter["energy_used"], label="Energy Used (kWh)")
        plt.plot(shorter.index, shorter["boilerTemp"], label="BoilerTemp C")
        plt.plot(shorter.index, shorter["cost"]/10,linestyle="--", label="Cost (10c/h)")

        plt.ylim(top=100,bottom=-10)
        plt.title("Hourly Heating Energy and Cost")

        plt.xlabel("Time")
        plt.ylabel("Values")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()

["date","price","energy_used","cost","boilerTemp"] # dataframes contains these infoes. date is index.
if __name__ == "__main__":
    main()