import csv
import math
import cPickle as pickle
import numpy as np
from scipy import stats

#Gather 2016-17 season data
pbp_reader = csv.reader(open('16-17-pbp/[10-25-2016]-[06-12-2017]-combined-stats.csv','rb'))
pbp_list=[row for row in pbp_reader]
pbp_mat = np.array(pbp_list[1:])

#Get league-wide foul/sub data
def get_foul_sub_dict(cut_time=0.75):
    #Set an initial ID so we can chunk games together
    prev_id = ''
    foul_dict={}

    #Looping time
    for i, play in enumerate(pbp_mat):
        #reset game dat
        if not play[0]==prev_id:
            game_dict={}
        prev_id=play[0]
        #Check if play is a foul
        if play[21]=='foul':
            #Don't care about technical fouls, so need a fould drawer
            if not play[29]=='':    
                player = play[31]
                #Track player fouls
                if player not in game_dict.keys():
                    game_dict[player]={'fouls':1}
                else:
                    game_dict[player]['fouls']+=1
                foul_num = game_dict[player]['fouls']
                quarter=int(play[13])
                minute = int(play[16].split(':')[1])
                if minute>6:
                    late=0
                else:
                    late=1
                #Figure out when foul occurred. Divide game by eigths
                chunk = (quarter-1)*2+late
                dkey = '%i_%i' % (chunk, foul_num)
                time = get_time(play)
                #Check to see if player benched after committing foul
                sub = False
                j = i+1
                if j <pbp_mat.shape[0]:
                    fut_play = pbp_mat[j]
                    while (not sub and fut_play[0] == play[0] and get_time(fut_play)-time <=cut_time and fut_play[13] in ['1','2','3','4']):
                        if fut_play[21]=='sub' and fut_play[27]==player:
                            sub = True
                        j+=1
                        if j>=pbp_mat.shape[0]:
                            break
                        fut_play=pbp_mat[j]
                if int(quarter)<=4:
                    if dkey not in foul_dict:
                        foul_dict[dkey]={'fouls':1,'subs':int(sub)}
                    else:
                        foul_dict[dkey]['fouls']+=1
                        foul_dict[dkey]['subs']+=int(sub)

    return foul_dict

#Get minutes played at time of play
def get_time(play):
    rtime = play[16]
    quarter = int(play[13])
    time = 12.-(float(rtime.split(':')[1])+float(rtime.split(':')[2])/60.)+12*(quarter-1)
    return time

#For player_foul_dict, update the season data after each game
def update_player_dict(player_dict,game_dict):
    for player in game_dict.keys():
        game_dat = game_dict[player]
        if not game_dat['Dirty']:
            #print game_dat, player
            player_dict[player]['Clean_mins'].append(game_dat['Mins'])
            player_dict[player]['Clean_fouls'].append(game_dat['Fouls'])
            player_dict[player]['Clean_fpm'].append(game_dat['Fouls']/game_dat['Mins'])
        else:
            player_dict[player]['Dirty_mins'].append(game_dat['Mins'])
            player_dict[player]['Dirty_fouls'].append(game_dat['Fouls'])
            player_dict[player]['Dirty_fpm'].append(game_dat['Fouls']/game_dat['Mins'])
            for i in range(8):
                if game_dat[i]:
                    player_dict[player]['min%i' % i].append(game_dat['Mins'])

#Get more detailed data for players
def get_player_foul_dict(players,cut_time=0.75):
    #Create output dict
    player_dict={}
    game_dict={}
    players_in=[]
    for player in players:
        player_dict[player]={'Clean_fouls':[],'Dirty_fouls':[],'Clean_mins':[],'Dirty_mins':[],'Clean_fpm':[],'Dirty_fpm':[],'min0':[],'min1':[],'min2':[],'min3':[],'min4':[],'min5':[],'min6':[],'min7':[]}
    prev_id=''
    proceed=False
    #iterate through every play
    for i,play in enumerate(pbp_mat):
        #Check sub outs for minutes played
        if proceed and play[0]==prev_id and play[13] in ['1','2','3','4']:
            for playing in players_in:
                if playing not in play[3:13]:
                    players_in.remove(playing)
                    game_dict[playing]['Mins']+=(get_time(play)-game_dict[playing]['sub_in'])
        proceed=False
        #Reset for every game
        if not play[0]==prev_id:
            #Update player_dict
            update_player_dict(player_dict,game_dict)
            game_dict={}
            #Reset if players we care about are in the game
            players_in=[]
            prev_id=play[0]
        #If in regulation and someone we care about is on the court
        if play[13] in ['1','2','3','4']:
            for playing in play[3:13]:
                if playing in players:
                    proceed =True
                    #Initial sub in 
                    if playing not in game_dict.keys():
                        game_dict[playing]={'Dirty':False,'Fouls':0,'Mins':0.0,'sub_in':get_time(play),0:False,1:False,2:False,3:False,4:False,5:False,6:False,7:False}
                        players_in.append(playing)
                    #new sub-in
                    if playing not in players_in:
                        players_in.append(playing)
                        game_dict[playing]['sub_in']=get_time(play)
        if proceed:
            #End of game check
            if play[21]=='end of period' and play[13]=='4':
                for playing in players_in:
                    game_dict[playing]['Mins']+=(48.0-game_dict[playing]['sub_in'])
            #Foul check
            if play[21]=='foul' and play[31] in players and not play[29]=='':
                player = play[31]
                game_dict[player]['Fouls']+=1
                #Check when/if player is pulled
                j=i+1
                time=get_time(play)
                sub=False
                if j<pbp_mat.shape[0]:
                    fut_play =pbp_mat[j]
                    while ( not sub and fut_play[0] == play[0] and get_time(fut_play)-time <=cut_time and fut_play[13] in ['1','2','3','4']):
                        if fut_play[21]=='sub' and fut_play[27]==player:
                            sub=True
                            game_dict[player]['Dirty']=True
                            quarter = int(play[13])
                            minute=int(play[16].split(':')[1])
                            if minute>6:
                                late=0
                            else:
                                late=1
                            key = (quarter-1)*2+late
                            game_dict[player][key]=True
                        j+=1
                        if j>=pbp_mat.shape[0]:
                            break
                        fut_play=pbp_mat[j]  
    #Derive season-wide rate statistics   
    for player in player_dict.keys():
        mpg = np.mean(player_dict[player]['Clean_mins']+player_dict[player]['Dirty_mins'])
        d_mpg = np.mean(player_dict[player]['Dirty_mins'])
        c_mpg = np.mean(player_dict[player]['Clean_mins'])
        fpg = np.mean(player_dict[player]['Clean_fouls']+player_dict[player]['Dirty_fouls'])
        d_fpg= np.mean(player_dict[player]['Dirty_fouls'])
        c_fpg = np.mean(player_dict[player]['Clean_fouls'])
        add_dict = {'MPG':mpg,'DirtyMPG':d_mpg,'CleanMPG':c_mpg,'FPG':fpg,'DirtyFPG':d_fpg,'CleanFPG':c_fpg}
        player_dict[player].update(add_dict)
    return player_dict

#Get fouls and sub in/out data for ind. players
def get_player_sub_dict(players,cut_time=0.75):
    prev_id =''
    #Create output dict
    player_sub_dict={}
    for player in players:
        player_sub_dict[player]={}
    #Iterate through plays
    for i,play in enumerate(pbp_mat):
        if not prev_id==play[0]:
            game_dict={}
            prev_id=play[0]
        #If it's a two-person foul in regulation by a player we care about
        if play[13] in ['1','2','3','4'] and play[21]=='foul' and not play[29]=='' and play[31] in players:
            if play[31] not in game_dict.keys():
                game_dict[play[31]]={'fouls':1}
            else:
                game_dict[play[31]]['fouls']+=1
            foul_num = game_dict[play[31]]['fouls']
            quarter=int(play[13])
            minute = int(play[16].split(':')[1])
            if minute>6:
                late=0
            else:
                late=1
            chunk = (quarter-1)*2+late
            dkey = '%i_%i' % (chunk,foul_num)
            #Check if subbed out
            time = get_time(play)
            sub=False
            j=i+1
            if j<pbp_mat.shape[0]:
                fut_play=pbp_mat[j]
                while (not sub and fut_play[0] == play[0] and get_time(fut_play)-time <=cut_time and fut_play[13] in ['1','2','3','4']):
                    if fut_play[21]=='sub' and fut_play[27]==play[31]:
                        sub=True
                    j+=1
                    if j>=pbp_mat.shape[0]:
                        break
                    fut_play=pbp_mat[j]
            if dkey not in player_sub_dict[play[31]]:
                player_sub_dict[play[31]][dkey]={'fouls':1,'subs':int(sub)}
            else:
                player_sub_dict[play[31]][dkey]['fouls']+=1
                player_sub_dict[play[31]][dkey]['subs']+=int(sub)
    return player_sub_dict

#Get detailed per game player data for each event in events
def get_graph_dict(players,cut_time=0.75,events=['1_2','3_3','5_4']):
    prev_id=''
    graph_dict={}
    for player in players:
        graph_dict[player]={}
        for event in events:
            graph_dict[player][event]={'GameID':[],'MP_event':[],'MP_game':[],'Fouls_game':[],'Time_50':[],'Time_90':[]}
    
    proceed=False
    players_in=[]
    #Iteration time
    for i,play in enumerate(pbp_mat):
        #Check sub outs
        if proceed and play[0]==prev_id and play[13] in ['1','2','3','4']:
            for playing in players_in:
                if playing not in play[3:13]:
                    players_in.remove(playing)
                    game_dict[playing]['Mins']+=(get_time(play)-game_dict[playing]['sub_in'])
        proceed=False
        #Better end of game check
        if i+1==pbp_mat.shape[0] or not play[0]==pbp_mat[i+1][0]:
            for event in events:
                for player in players:
                    if play[0] in graph_dict[player][event]['GameID']:
                        graph_dict[player][event]['MP_game'].append(game_dict[player]['Mins'])
                        graph_dict[player][event]['Fouls_game'].append(game_dict[player]['Fouls'])
        #Reset for every game
        if not play[0]==prev_id:
            game_dict={}
            #Reset if players we care about are in the game
            players_in=[]
            prev_id=play[0]
        if play[13] in ['1','2','3','4']:
            for playing in play[3:13]:
                if playing in players:
                    proceed =True
                    #Initial sub in
                    if playing not in game_dict.keys():
                        game_dict[playing]={'Fouls':0,'Mins':0.0,'sub_in':get_time(play)}
                        players_in.append(playing)
                    #new sub-in
                    if playing not in players_in:
                        players_in.append(playing)
                        game_dict[playing]['sub_in']=get_time(play)
        if proceed:
            #End of game check
            if play[21]=='end of period' and play[13]=='4':
                for playing in players_in:
                    game_dict[playing]['Mins']+=(48.0-game_dict[playing]['sub_in'])
            #Foul check
            if play[21]=='foul' and play[31] in players and not play[29]=='':
                player = play[31]
                game_dict[player]['Fouls']+=1
                #Check when/if player is pulled
                j=i+1
                time=get_time(play)
                sub=False
                if j<pbp_mat.shape[0]:
                    fut_play =pbp_mat[j]
                    while (not sub and fut_play[0] == play[0] and get_time(fut_play)-time <=cut_time and fut_play[13] in ['1','2','3','4']):
                        if fut_play[21]=='sub' and fut_play[27]==player:
                            sub=True
                            quarter = int(play[13])
                            minute=int(play[16].split(':')[1])
                            if minute>6:
                                late=0
                            else:
                                late=1
                            key = '%i_%i' %  (((quarter-1)*2+late),game_dict[player]['Fouls'])
                            if key in events:
                                #Check GameIDs. Don't want repeats.
                                already_in =False
                                for event in events:
                                    if play[0] in graph_dict[player][event]['GameID']:
                                        already_in =True
                                if not already_in:
                                    graph_dict[player][key]['GameID'].append(play[0])
                                    mp = game_dict[player]['Mins'] + get_time(fut_play) - game_dict[player]['sub_in']
                                    graph_dict[player][key]['MP_event'].append(mp)
                        j+=1
                        if j>=pbp_mat.shape[0]:
                            break
                        fut_play=pbp_mat[j]
    return graph_dict


'''
for t in [0.5,0.75,1.0]:
    fd = get_foul_sub_dict(t)
    pickle.dump(fd,open('foul_subs_%.2f.pkl' % t,'wb'))
    print "Cutoff = %0.2f" % t
    keys = fd.keys()
    keys.sort()
    for k in keys:
        print "%s %s quarter with %i fouls. Rate: %0.3f" % (['Early','Late'][int(k.split('_')[0])%2],int(k.split('_')[0])/2 +1,int(k.split('_')[1]),fd[k]['subs']/float(fd[k]['fouls'])*100)
    print '\n'
'''
players =['James Harden','Rudy Gobert','Jimmy Butler', 'LeBron James','Damian Lillard','Gordon Hayward','Kawhi Leonard','Stephen Curry','Kevin Durant','Anthony Davis','Chris Paul','Kyle Lowry','Hassan Whiteside','Isaiah Thomas','Giannis Antetokounmpo','Jimmy Butler','DeAndre Jordan','Russell Westbrook','Mike Conley','Nikola Jokic','Karl-Anthony Towns']
#pd = get_player_foul_dict(players)
#pickle.dump(pd,open('top_20_player_data.pkl','wb'))
#ps = get_player_sub_dict(players)
#pickle.dump(ps,open('top_20_player_subs.pkl','wb'))
#gd  = get_graph_dict(players,events=['1_2','3_3','5_4'],cut_time=0.75)
#pickle.dump(gd,open('top_20_prelim_graph.pkl','wb'))
gd = pickle.load(open('top_20_prelim_graph.pkl','rb'))
pd = pickle.load(open('top_20_player_data.pkl','rb'))
#Get estimated time lost from subbing out early
def get_est_time(gd,pd):
    for player in gd.keys():
        #Baseline minutes
        mpg = pd[player]['CleanMPG']
        #Get foul rates
        fpm = pd[player]['FPG']/pd[player]['MPG']
        s_fpm = np.std(pd[player]['Dirty_fpm']+pd[player]['Clean_fpm'])
        for event in ['1_2','3_3','5_4']:
            for i,fouls in enumerate(gd[player][event]['Fouls_game']):
                t_50=0
                t_90=0
                if fouls<6:
                    #Guess max time to be gained
                    time_missing = np.max([0.0,mpg-gd[player][event]['MP_game'][i]])
                    norm=0
                    #Figure out likley time to be gained, figuring in fouling out
                    #Iterating through a Gamma distribution
                    for val in np.linspace(np.max([0.01,fpm-2*s_fpm]),fpm+2*s_fpm,100):
                        normalize = stats.gamma.pdf(val,a=(fpm/s_fpm)**2,scale=s_fpm*s_fpm/fpm)
                        try:
                            #CANNOT FIGURE OUT MULTI FOULS NEEDED
                            #LACKNG STAT KNOWLEDGE
                            #THIS IS A HACK!!!!!!!!
                            t_50 +=(6-fouls)*normalize*math.log(0.5,(1-(val/100)))/100
                            t_90 +=(6-fouls)*normalize*math.log(0.9,(1-(val/100)))/100
                            norm+=normalize
                        except ZeroDivisionError:
                            print normalize,val,fouls
                    t_50/=norm
                    t_90/=norm
                gd[player][event]['Time_50'].append(min([t_50,time_missing]))
                gd[player][event]['Time_90'].append(min([t_90,time_missing]))
    return gd
gd2 = get_est_time(gd,pd)    
pickle.dump(gd2,open('top_20_final_graph.pkl','wb'))

#Graph Make Time!
import sys
sys.path[0] = '/nfs/slac/g/suncatfs/aidank/software/lib/python2.7/site-packages/matplotlib-1.5.1-py2.7-linux-x86_64.egg'
import matplotlib.pyplot as plt
fs = pickle.load(open('foul_subs.pkl','rb'))
ps=pickle.load(open('top_20_player_subs.pkl','rb'))
#Harden/Curry plot first
events = ['1_2','3_3','5_4']
labels = ['Late 1st\n2 Fouls','Late 2nd\n3 Fouls','Late 3rd\n4 Fouls']
fig = plt.figure()
ax = fig.add_subplot(111)
for i,event in enumerate(events):
    ax.bar(0+i*4.5,ps['James Harden'][event]['fouls'],width=1.0,color='r',alpha=0.25)
    ax.bar(0+i*4.5,ps['James Harden'][event]['subs'],width=1.0,color='r',alpha=1,label='James Harden')
    ax.bar(1+i*4.5,ps['Stephen Curry'][event]['fouls'],width=1.0,color='b',alpha=0.25)
    ax.bar(1+i*4.5,ps['Stephen Curry'][event]['subs'],width=1.0,color='b',alpha=1,label='Stephen Curry')
    ax.bar(2+i*4.5,10.0,width=1.0,color='w')
    ax.bar(2+i*4.5,10.0*fs[event]['subs']/fs[event]['fouls'],width=1.0,color='k',label='League Rate')
    if i==0:
        ax.legend(loc='best')
ax.set_ylim([0,12])
ax.set_xticklabels(labels,size=10,rotation=45)
ax.set_xticks(np.arange(0,13.5,4.5)+1.5)
ax.set_ylabel('Fouls and Substitutions')
plt.savefig('HardenCurry.pdf')

#Est. time/ws gained time
players=['Russell Westbrook','LeBron James','Hassan Whiteside','Jimmy Butler','Nikola Jokic','Giannis Antetokounmpo']
ws =[.224,.221,.181,.236,.228,.21]
ws = np.array(ws)/48.0
gd2 = pickle.load(open('top_20_final_graph.pkl','rb'))
fig = plt.figure()
ax = fig.add_subplot(111)
ax.set_xlim([0,25.])
ax2 = ax.twinx()
for i,player in enumerate(players):
    mp =[]
    t50=[]
    t90=[]
    for event in gd2[player].keys():
        mp+=gd2[player][event]['MP_game']
        t50+=gd2[player][event]['Time_50']
        t90+=gd2[player][event]['Time_90']
    ws50 = np.array(t50)*ws[i]
    ws90 = np.array(t90)*ws[i]
    t50 = np.array(t50)+np.array(mp)
    t90 = np.array(t90)+np.array(mp)
    ax.bar(0+i*4.25,np.mean(mp),width=1,alpha=0.5,label='Actual Minutes',color='mediumblue')
    ax.bar(1+i*4.25,np.mean(t50),width=1,alpha=0.2,color='dodgerblue',yerr=np.array([[np.mean(t50)-np.mean(t90)],[0]]),ecolor='k',label='Projected Minutes')
    ax2.bar(2+i*4.25,np.sum(ws50),width=1,alpha=0.2,color='darkorange',yerr=np.array([[np.sum(ws50)-np.sum(ws90)],[0]]),ecolor='k',label='Projected Win Shares Gained')
    if i==0:
        ax.bar(2+i*4.25,0,width=1,alpha=0.2,color='darkorange',label='Projected Win Shares Gained')
        ax.legend(loc='best',fontsize=9.5)
ax.set_xlim([0,25])
ax2.set_xlim([0,25])
ax.set_ylim([0,50])
ax2.set_ylim([0,0.85])
labels=[]
for player in players:
    labels.append(player.replace(' ','\n'))
fig.subplots_adjust(bottom=0.2)
ax.set_xticklabels(labels,size=9.5,rotation=45)
ax.set_xticks(np.arange(0,25.5,4.25 )+1.5)
ax.set_ylabel('Minutes\nPer Game')
ax2.set_ylabel('Win Shares')
plt.savefig('Projections.pdf')



