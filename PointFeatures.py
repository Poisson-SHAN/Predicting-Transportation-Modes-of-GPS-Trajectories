from itertools import groupby
from operator import itemgetter
import numpy as np
import pandas as pd
from operator import mul
import itertools
from sklearn.metrics import accuracy_score
from sklearn.metrics import classification_report
from haversine import haversine
from datetime import datetime
import math
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier

# Loading the Input Data and sorting it in ascending order of 't_user_id' and 'collected_time'. This way of sorting
# the data is equivalent to grouping the data on the bases of 't_user_id' and 'collected_time'.
df = pd.read_csv('geolife_raw.csv')
total = len(df)
df = df.sort_values(['t_user_id', 'collected_time'], ascending=True).reset_index(drop=True)

# Preprocessing
x = df['collected_time'].str.split(' ', expand = True)
df['date_Start'] = x[0]
y = x[1].str.split('-', expand = True)
df['time_Start'] = y[0]
df['latitude_Start'] = df['latitude']
df['longitude_Start'] = df['longitude']

df['latitude_End'] = df['latitude'].drop([0]).reset_index(drop=True)
df['longitude_End'] = df['longitude'].drop([0]).reset_index(drop=True)

df['date_End'] = df['date_Start'].drop([0]).reset_index(drop=True)
df['time_End'] = df['time_Start'].drop([0]).reset_index(drop=True)

df['UserChk'] = df['t_user_id'].drop([0]).reset_index(drop=True)
df['ModeChk'] = df['transportation_mode'].drop([0]).reset_index(drop=True)
df = df.drop('collected_time', axis =1)
df = df.drop('latitude', axis =1)
df = df.drop('longitude', axis =1)
df = df.drop([total-1], axis =0)

# The above preprocessing has created a DataFrame with the columns arranged in a much more better computational way.
# Columns of processable data now are :- 
# 't_user_id', 'transportation_mode', 'date_Start', 'time_Start', 'latitude_Start', 'longitude_Start',
# 'latitude_End', 'longitude_End','date_End', 'time_End', 'UserChk', 'ModeChk' 
# We finally convert this DataFrame to list of lists because of the better time complexity of lists than pandas DataFrame
dataList = df.values.tolist()

# This is the method to calculate bearing between two points on the bases
# of latitute and longitutes of the 2 points.
def bearing_Calculator(row):
    start, end = ((row[4], row[5]), (row[6], row[7])) 
    lat1 = math.radians(float(start[0]))
    lat2 = math.radians(float(end[0]))

    diffLong = math.radians(float(end[1]) - float(start[1]))
    x = math.sin(diffLong) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1)* math.cos(lat2) * math.cos(diffLong))
    initial_bearing = math.atan2(x, y)
    initial_bearing = math.degrees(initial_bearing)
    compass_bearing = (initial_bearing + 360) % 360
    return compass_bearing

# This below method will create this kind of list of list structure
#         s -> (s0,s1), (s1,s2), (s2, s3), ...
def pairwise(iterable):
    a, b = itertools.tee(iterable)
    next(b, None)
    return itertools.zip_longest(a, b)

# Here we are calculating distance, speed, acceleration and bearing.

# Filtering the data so as to remove as per our preprocessed data and understanding of trajectories.
# We are filtering:-
# 1. The information if starting inf is from 1 user and ending inf is from another user
# 2. The information if starting inf is from 1 transportation mode and ending inf is from another transportation mode
# 3. If the starting date and ending date match or not
FMT = '%H:%M:%S'
filteredData = [item for item in dataList if(item[0]==item[10] and item[1]==item[11] and item[2]==item[8])]

# Here we are creating a flag numerical column so as to easily find when there is a change in subtrajectory or trajectory
startId = filteredData[0][0]
startMode = filteredData[0][1]
startDate = filteredData[0][2]
subTrajGrper = []
count = 1
for row in filteredData:
    if(startId ==row[0] and startMode ==row[1] and startDate ==row[2]):
        subTrajGrper.append(count)
    else:
        startId = row[0]
        startMode = row[1]
        startDate = row[2]
        count+=1
        subTrajGrper.append(count)

# Calculating Distance
distance = [haversine((float(row[4]),float(row[5])), (float(row[6]),float(row[7])))*1000.0 for row in filteredData]
# Calculating Time
time = [(datetime.strptime(str(row[9]), FMT) - datetime.strptime(str(row[3]), FMT)).seconds for row in filteredData]
# Calculating speed
speed = [x/y if y != 0 else 0 for x,y in zip(distance, time)]
# Calculating acceleration
pairedSpeed = list(pairwise(speed))
acceleration = [(x[1]-x[0])/y if(y != 0 and x[1]!=None) else 0 for x,y in zip(pairedSpeed, time) ]
# Calculating Bearing
bearing = [bearing_Calculator(row) for row in filteredData]

# Here we are doing a list compression so as to add the answer of Q1 to our preprocessed data. 
dataA1Soln = [u + [v,w,x,y,z]  for u,v,w,x,y,z in zip(filteredData,subTrajGrper, distance, speed, acceleration, bearing)]

# Here we are masking the accleration to 0 in case it is calculated by change in speed between 2 different users.
pairedA1 = list(pairwise(dataA1Soln))
dataA1Soln = [list(map(mul, rows[0], [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,1])) if(rows[1]!= None and rows[0][12] != rows[1][12]) else rows[0] for rows in pairedA1]

