import numpy as np
import scipy as sp
from scipy.optimize import minimize
import sklearn as skl
from sklearn import linear_model
import csv

#Collect the data matrices we need
files =['Accidents0514.csv','Vehicles0514.csv']
acc,veh = [[row for row in csv.reader(open(f,'rb'))] for f in files]
acc_head=acc[0]
acc_mat = np.array(acc[1:])
veh_head = veh[0]
veh_mat = np.array(veh[1:])

#Create output values
acc_num = acc_mat.shape[0]
urban_num =0
hour_acc = np.zeros(24)
hour_fatal = np.zeros(24)
years=range(2005,2015)
year_acc = np.zeros(len(years))
sl_dict={}
pd_dict={}
age_dict={}
skid_rain=0
skid_clear=0
all_rain=0
all_clear=0
male_fatal_car=0
male_acc_car=0
female_fatal_car=0
female_acc_car=0
veh_ind=0
#Loop throught accident data
for i,accident in enumerate(acc_mat):
    # Pull relevant vehicle data
    #will assume same sorting, so looping together, sort of
    rel_inds=[0]
    while veh_ind<veh_mat.shape[0] and accident[0]==veh_mat[veh_ind][0]:
        rel_inds.append(veh_ind)
        veh_ind+=1
    veh_data = veh_mat[rel_inds]
    #Check urban/non-urban
    if int(accident[29])==1:
        urban_num+=1    
    #Check accident time
    try:
        hour = int(accident[11].split(':')[0])
        hour_acc[hour]+=1
        fatal=False
        if int(accident[6])==1:
            fatal=True
            hour_fatal[hour]+=1
    except:
        pass
    #Get year-by-year data
    year = int(accident[9].split('/')[-1])
    year_ind = years.index(year)
    year_acc[year_ind]+=1
    #Look at speed limits and lethality
    sl = accident[17]
    if sl not in sl_dict.keys():
        sl_dict[sl]={'Accidents':1,'Fatals':int(fatal)}
    else:
        sl_dict[sl]['Accidents']+=1
        sl_dict[sl]['Fatals']+=int(fatal)
    #Estimate police district size
    if accident[12] not in pd_dict.keys():
        try:
            pd_dict[accident[12]]={'Longitudes':[float(accident[3])],'Latitudes':[float(accident[4])]}
        except:
            pass
    else:
        try:
            pd_dict[accident[12]]['Longitudes'].append(float(accident[3]))
            pd_dict[accident[12]]['Latitudes'].append(float(accident[4]))
        except:
            pass
    #Vehicle data question data gathering time
    for vehicle in veh_data:
        #Check skidding and weather data
        if int(vehicle[7])>=0:
            if int(accident[25])==1:
                all_clear+=1
            elif int(accident[25]) in [2,3,5,6]:
                all_rain+=1
        if int(vehicle[7])>0:
            if int(accident[25])==1:
                skid_clear+=1
            elif int(accident[25]) in [2,3,5,6]:
                skid_rain+=1
        #only care about car accidents for these two
        if int(vehicle[2])==9:
            #Need (legal) age data
            age=vehicle[15]
            if int(age)>=17:
                if age not in age_dict.keys():
                    age_dict[age]=1
                else:
                    age_dict[age]+=1
            #Male/female data
            if int(vehicle[14])==1:
                male_acc_car+=1
                male_fatal_car+=int(fatal)
            elif int(vehicle[14])==2:  
                female_acc_car+=1
                female_fatal_car+=int(fatal)           

q1 = urban_num/float(acc_num)
q2 = np.max(hour_fatal/np.array(hour_acc,dtype=float))
q5 = (skid_rain/float(all_rain))/(skid_clear/float(all_clear))
q6 = (male_fatal_car/float(male_acc_car))/(female_fatal_car/float(female_acc_car))

#Regress years and accident number.
lin_reg = linear_model.LinearRegression()
years = np.reshape(np.array(years),(-1,1))
year_acc = np.reshape(np.array(year_acc),(-1,1))
lin_reg.fit(years,year_acc)
q3 = lin_reg.coef_[0][0]

#Basically same for speed limit
speeds=[]
fat_rat =[]
for spd in sl_dict.keys():
    speeds.append(float(spd))
    ratio = float(sl_dict[spd]['Fatals'])/float(sl_dict[spd]['Accidents'])
    fat_rat.append(ratio)
speeds = np.array(speeds,ndmin=2).T
fat_rat = np.array(fat_rat,ndmin=2).T
lin_reg = linear_model.LinearRegression()
lin_reg.fit(speeds,fat_rat)
q4=lin_reg.score(speeds,fat_rat)

#Ellipse time!
long_convert = 69.47
lat_convert = 111.26
areas = []
for pd in pd_dict.keys():
    lats = pd_dict[pd]['Latitudes']
    longs = pd_dict[pd]['Longitudes']
    a = np.std(lats)*lat_convert
    b = np.std(longs)*long_convert
    areas.append(np.pi*a*b)
q7 = np.max(areas)

#Exponential regression the hard way
age_dat=[]
acc_dat=[]
for age in age_dict.keys():
    age_dat.append(float(age)-17)
    acc_dat.append(float(age_dict[age]))

def exp_func(co_mat,x):
    return co_mat[0]*np.exp(-1*co_mat[1]*x)
def ErrorFunc(co_mat,x_dat,y_dat):
    val=0
    for i in range(len(x_dat)):
        val+=(y_dat[i]-exp_func(co_mat,x_dat[i]))**2
    return val
f = lambda co_mat: ErrorFunc(co_mat,age_dat,acc_dat)
res = minimize(f,np.array([1.,0.2]),method='SLSQP',tol=1e-07)
q8 = res.x[1]
print res.x

#And the easy way:
lin_reg = linear_model.LinearRegression()
age_dat = np.array(age_dat,ndmin=2).T
acc_dat = np.array(acc_dat,ndmin=2).T
lin_reg.fit(age_dat,np.log(acc_dat))
q8b = lin_reg.coef_[0][0]
age_dat = np.reshape(age_dat,(-1,))
acc_dat = np.reshape(acc_dat,(-1,))
q8c = np.polyfit(age_dat,np.log(acc_dat),1)[0]
q8d = np.polyfit(age_dat,np.log(acc_dat),1,w=np.sqrt(acc_dat))[0]

#Return results!
print "Question 1: %0.10f\nQuestion 2: %0.10f\nQuestion 3: %0.10f\nQuestion 4: %0.10f\nQuestion 5: %0.10f\nQuestion 6: %0.10f\nQuestion 7: %0.10f\nQuestion 8: %0.10f or %0.10f, or %0.10f or %0.10f." % (q1,q2,q3,q4,q5,q6,q7,q8,q8b,q8c,q8d)

