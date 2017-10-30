import numpy as np
import scipy as sp

#Class of a knight chess piece
class Knight:
    #Move the knight to the initialized position
    def __init__(self,position):
        import numpy as np
        self.move(position)

    def get_position(self):
        return self.position    

    #Move the knight to one of the 16 squares on the problem board
    def move(self,position):
        assert position in range(16)
        self.position=position
        #Get the possible moves for the new position
        try:
            self.get_moves()
        #Error checking
        except AssertionError:
            print self.position, self.possible_moves

    #Get a list of all of the allowable moves
    def get_moves(self):
        self.possible_moves=[]
        #Check the moves where you move 2 horizontal spaces
        for hor in [-2,2]:
            if np.floor((self.position+hor)/4.) == np.floor(self.position/4.):
                p_ = self.position+hor
                for vert in [-4,4]:
                    if p_+vert in range(16):
                        self.possible_moves.append(p_+vert)
        #Now 1 horizontal space cases
        for hor in [-1,1]:
            if np.floor((self.position+hor)/4.) == np.floor(self.position/4.):
                p_ = self.position+hor
                for vert in [-8,8]:
                    if p_+vert in range(16):
                        self.possible_moves.append(p_+vert)
        assert (len(self.possible_moves) in [2,3,4])

    #Randomly select a move from the list of possible moves
    def random_move(self):
        mov_id = np.random.randint(len(self.possible_moves))
        self.move(self.possible_moves[mov_id])

#Move the knight randomly count sequential times and record the square sum
def random_run(count,rseed=5):
    knight = Knight(0)
    move_sum = knight.get_position()
    np.random.seed(seed=rseed)
    for c in range(count):
        knight.random_move()
        move_sum+=knight.get_position()
    return move_sum
#Do the random run runs time. Take care of the random seeding
def stat_run(runs,count,init_seed=5):
    sums=[]
    np.random.seed(init_seed)
    rseeds= np.random.randint(255,size=runs)
    for r in range(runs):
        sums.append(random_run(count,rseed=rseeds[r]))
    return sums


sums1 = stat_run(5000,16)
assert len(sums1)==5000
mod_sums=[]
thirteen_sums=[]
for s in sums1:
    mod_sums.append(s%13)
    if s%13 ==0:
        thirteen_sums.append(s)
#print thirteen_sums
m1 = np.mean(mod_sums)
std1 = np.std(mod_sums)
five_sums = []
for s in thirteen_sums:
    if s%5 ==0:
        five_sums.append(s)

if len(thirteen_sums)==0:
    prob1 = 0.
    print "prob1 undefined"
else:
    prob1= float(len(five_sums))/float(len(thirteen_sums))

sums2 = stat_run(5000,512)
mod_sums=[]
four_three_sums=[]
for s in sums2:
    mod_sums.append(s%311)
    if s%43 ==0:
        four_three_sums.append(s)
m2 = np.mean(mod_sums)
std2 = np.std(mod_sums)
seven_sums = []
for s in four_three_sums:
    if s%7==0:
        seven_sums.append(s)
if len(four_three_sums)==0:
    prob2 =0
    print "prob2 undefined"
else:
    prob2 = float(len(seven_sums))/float(len(four_three_sums))

print "For run with T=16:\nMean mod 13 = %.10f.\nStandard Deviation = %.10f.\nSum probability (13 vs 13 and 5) = %.10f." % (m1,std1,prob1)
print "For run with T=512:\nMean mod 311 = %.10f.\nStandard Deviation = %.10f.\nSum probability(43 vs 43 and 7) = %.10f." % (m2,std2,prob2)


