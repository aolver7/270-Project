# -*- coding: utf-8 -*-
# Created on Sun Mar 12 17:55:49 2023

# @author: andre

@author: andre

import csv


# LETS USER INPUT YEAR AND SCENARIO TYPE IF NECESSARY
# OUTPUTS SECNARIO FILE NAME AND SCENARIO YEAR

def scenariochoice ():
    scenarioyear=str(input("ENTER SCENARIO YEAR "))
    if scenarioyear == '2025' :
        scenariotype=''
    else :
        scenariotype=str(input("ENTER SCENARIO TYPE(DE, GA OR NT) "))
    scenariofile=str('Demand'+scenarioyear+scenariotype+'.csv')
    print(scenariofile)
    return scenariofile, scenarioyear

# TAKES IN SCENARIO YEAR
# LETS USER INPUT START AND END DATES AND TIMES (HORIZON) THEN OUPUTS THEM IN THE SAME FORM AS THEY APPEAR IN THE SCENARIOFILE

def horizoninputs (scenarioyear):
    startday=str(input("ENTER START DAY "))
    startmonth=str(input("ENTER START MONTH "))
    starttime=str(input("ENTER START TIME(HH:MM) "))
    endday=str(input("ENTER END DAY "))
    endmonth=str(input("ENTER END MONTH "))
    endtime=str(input("ENTER END TIME(HH:MM) "))
    horizonstart=str(startday+'/'+startmonth+'/'+scenarioyear+' '+starttime)
    horizonend=str(endday+'/'+endmonth+'/'+scenarioyear+' '+endtime)
    print(horizonstart, horizonend)
    return horizonstart, horizonend

# TAKES IN CERTAIN WIND LEVELS
# PASSES OUT 3 PARALLEL LIST OF SUPPLY TYPE, SUPPLY EFFICIENCY AND SUPPLY CAPACITY ALL ORDERED BY EFFICIENCY INCREASING

def supplytotal (offwindiness, onwindiness):
    efficiencies=[]
    supplies=[]
    capacities=[]
    
    with open('generator_costs.csv', 'r') as f:
        csvfile=csv.DictReader(f)
        for row in csvfile:
            efficiencies.append(float(row['Cost (£/MWh)']))             #CHANGED INT TO FLOAT
        efficiencies.sort()
        
    for index in range(len(efficiencies)):
        with open('generator_costs.csv', 'r') as f:
            csvfile=csv.reader(f)
            starting=0
            for row in csvfile:
                if starting == 0 or efficiencies[index-1] == float(row[1]):         #CHANGED INT TO FLOAT
                    starting=1
                elif efficiencies[index] == float(row[1]):                 #CHANGED INT TO FLOAT
                    supplies.append(row[0])
        
    with open('generators.csv', 'r') as f:
        for index in range(len(supplies)):
            capacities.append(0)
        csvfile=csv.DictReader(f)
        for row in csvfile:
            for index in range(len(supplies)):
                if row['Type'] == 'Wind offshore':
                    capacities[index]=capacities[index]+(offwindiness*float(row['Installed capacity']))
                elif row['Type'] == 'Wind onshore':
                    capacities[index]=capacities[index]+(onwindiness*float(row['Installed capacity']))
                elif row['Type'] == supplies[index]:
                    
                    capacities[index]=capacities[index]+float(row['Installed capacity'])
        
    return efficiencies, supplies, capacities

# TAKES IN START AND END TIMES AND OUTPUTS A LIST OF THE DEMAND FOR EACH HOUR WITHIN THIS PERIOD AND PARALLEL LIST OF THE HOURS

def calcdemand (scenariofile, horizonstart, horizonend):     
    demand=[]
    hours=[]
    with open(scenariofile, 'r') as f:
        csvfile=csv.DictReader(f)
        started=0
        for row in csvfile:
            time=row['Time']
            if time == horizonend:
                started=0
            elif time == horizonstart or started == 1:
                started = 1
                demand.append(row['Total'])
                hours.append(row['Time'])
    return demand, hours

# TAKES IN THE LIST OF CAPACITIES OF EACH SUPPLY TYPE, THE LIST OF SUPPLY TYPES, THE DEMAND AT EACH HOUR, THE HOURS, AND THE EFFICIENCIES
# COMPARES SUPPLY AND DEMAND FOR EACH HOUR OF THE HORIZON
# RECORDS COST FOR EACH HOUR THEN CALCULATES AND AVERAGE AND OUTPUTS IT
# RECORDS UTILISATION PERCENTAGE OF EACH SUPPLY TYPE FOR EACH HOUR AND THEN CALCULATES AN AVERAGE UTILISATION PERCENTAGE, THEN OUTPUTS THIS AS A LIST OF PERCENTAGE FOR EACH SUPPLY TYPE
# RECORDS THE MARGINAL SUPPLY TYPE FOR EACH HOUR AND MAKES A LIST OF EVERY MARGINAL SUPPLY TYPE IN THE HORIZON
# MAKES A LIST OF EVERY HOUR WHERE SUPPLY COULD NOT BE MET(DISCONNECT HOURS)

def compare(capacities, supplies, demand, hours, efficiencies):
    utilisation=[]
    for index in range(len(supplies)):
        utilisation.append(0)

    disconnecthours=[]
    marginals=[]
    runningcost=0

    for index in range(len(demand)):
        hourlyutil=[]
        hourlycost=0
        for secondindex in range(len(supplies)):   #More efficient way to initialise array of certain length???
            hourlyutil.append(0)
        remaining=float(demand[index])
        stype=0
        while remaining > 0:
            if stype+1 > len(capacities):
                disconnecthours.append(hours[index])
                marginals.append(supplies[len(supplies)-1])
                remaining=0
                print("OVERLOAD")
                for secondindex in range(len(supplies)):
                    hourlyutil[secondindex]=0                       #Does disconnected hours count towards utilisation and cost???
                hourlycost=0
            elif remaining > capacities[stype] :
                remaining=remaining-capacities[stype]
                hourlyutil[stype]=100
                hourlycost=hourlycost+(efficiencies[stype]*capacities[stype])
                stype=stype+1 
            else :
                hourlycost=hourlycost+(efficiencies[stype]*remaining)
                hourlyutil[stype]=100*remaining/capacities[stype]
                remaining=0
                marginals.append(supplies[stype])
           
        for secondindex in range(len(supplies)):
            utilisation[secondindex]=utilisation[secondindex]+hourlyutil[secondindex]
        runningcost=runningcost+hourlycost
        
    for index in range(len(supplies)):
        utilisation[index]=utilisation[index]/len(demand)          
    averagecost=runningcost/(len(demand)-len(disconnecthours))          #Does disconnected hours count towards utilisation and cost???
    return averagecost, disconnecthours, marginals, utilisation



# INITIALISES CSV FILE

def clearcsv():
    with open('marginals.csv', 'w') as f:
        f.write("MARGINAL GENERATION TYPES\n")
    return


# WRITES MARGINAL SUPPLY TYPES TO CSV FILE

def writemarginals(marginals,hours, offwindiness, onwindiness):
    with open('marginals.csv', 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Time", "Marginal supply", "Offshore wind", "Onshore wind"])
        
        for index in range(len(marginals)):
            writer.writerow([hours[index], marginals[index], str(offwindiness), str(onwindiness)])
    return

offwindlevels=[0,25,55,85]
onwindlevels=[0,15,35,75]

scenariofile, scenarioyear=scenariochoice()
horizonstart, horizonend=horizoninputs(scenarioyear)
demand, hours=calcdemand(scenariofile, horizonstart, horizonend)
clearcsv()


# CALCULATES OUTCOMES FOR DIFFERENT LEVELS OF WIND STRENGTH

for index in range (len(offwindlevels)):
    efficiencies, supplies, capacities=supplytotal(offwindlevels[index], onwindlevels[index])
    averagecost, disconnecthours, marginals, utilisation=compare(capacities, supplies, demand, hours, efficiencies)
    print("OFFSHORE WIND, ONSHORE WIND")
    print(offwindlevels[index], onwindlevels[index])
    print("")
    print("AVERAGE COST",averagecost)
    print("GRID DISCONNECTION HOURS",disconnecthours)
    print(supplies)
    print(utilisation)
    writemarginals(marginals, hours, offwindlevels[index], onwindlevels[index])