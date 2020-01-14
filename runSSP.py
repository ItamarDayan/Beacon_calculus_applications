from pathlib import Path
import subprocess
import csv
import numpy
import matplotlib.pyplot as plt
import math
import time


def Calc_first_n_primes(n):
    primes = [2]
    n = int(n)
    n -= 1
    i = 3
    is_prime = True
    
    while n > 0:
        is_prime = True
        for k in range(2, math.ceil(i/2)+1):
            if i % k == 0:
                is_prime = False
                break
    
        if(is_prime): 
            n -= 1
            primes.append(i)
    
        i += 1

    return primes

def print_partial_sums(lst,n):
    sum = 0
    partial_sums = ""
    partial_sums += "0"
    for i in range(0,n-1):
        sum += lst[i]
        partial_sums += (", " + str(sum))

    return partial_sums


def print_setup_params(num):
    setup_params = "s0"
    for i in range(1, num):
        setup_params += ",s" + str(i)

    return setup_params


def print_setup(num):
    setup = "{s0![1],fast}"
    for i in range(1, num+1):
        setup += ".{s" + str(i) + "![1],fast}"

    return setup


#________________________________________________________MAIN___________________________________________________________________-

# creating an empty list 
lst = [] 
mode = int(input("choose input mode; 1: Manually insert nummbers set, 2: run SSP on first n primes"))

if  mode == 1:
    # number of elements as input 
    n = int(input("Enter the length of the set and a set of numbers for the SSP: ")) 
    
    # iterating till the range 
    for i in range(0, n): 
        ele = int(input()) 
    
        lst.append(ele) # adding the element 
        
    lst.sort()

if mode == 2:
    n = int(input("Enter the amount of the first prime numbers to use as a set for the SSP"))
    lst = Calc_first_n_primes(n)

sum = sum(lst)

num_of_agents = input("Enter amount of agents")


#------------------------------------------Create the bcs code-------------------------------------#
bcs_code = '''
fast = 1000;
r = 1;


Setup[''' + print_setup_params(n) + '''] = ''' + print_setup(n) + '''.{start![1] ,fast};
 
 
P[x,y,sum,last] = {start?[1], r}.
(
[y==sum]->{done![x],fast} ||

[y!=sum]->{y?[0..sum], fast}.({splitDown,1}.P[x,y+1,sum,0] + {splitDiag,1}.P[x+1,y+1,sum,1]) ||

[y!=sum]->{~y?[0..sum],fast}.( [last == 0] -> {continueStraight, r}.P[x,y+1,sum,0] + [last == 1]-> {continueStraight, r}.P[x+1,y+1,sum,1])
);


Setup[''' + print_partial_sums(lst,n) + '''] || ''' + str(num_of_agents) + '''*P[0,0,'''+ str(sum) +''',0];'''

#---------------------------------------------------------------------------------------------------#



#---------------------------Create a new file for the generated code and run a simulation---------------------# 

BCS_file = open("generated_bcs_code.bc", "w")    # Open a new text file with write premmisions
BCS_file.write(bcs_code)                         # Write the bcs code to the file
BCS_file.close()                                 # close the file

DIR_path = Path().absolute()

start = time.time()  # get time before computation
subprocess.run(str(DIR_path) + '/bin/bcs generated_bcs_code.bc', shell = True)	# Run BCS simulation on the generated code
end = time.time()    # get time after computation

elapsed_time = end-start  # estimate the computation time

results = numpy.zeros(sum + 1, dtype = numpy.int8)
#--------------------------------------------------------------------------------------------------------------#


#----------------------------Read and interpert the results file----------------------------------------------#

with open(str(DIR_path) + '/simulationOutput') as csvFile:			
    fileReader = csv.reader(csvFile, delimiter = '\t', skipinitialspace=True)
    for line in fileReader:
        if(len(line)==11):
            if(line[1] == 'done'):
                results[int(line[4])] += 1
#-------------------------------------------------------------------------------------------------------------#

#--------------------------------------Print and plot results-------------------------------------------------#

print("--------------------------------------RESULTS--------------------------------------------\n\n")

results = numpy.absolute(results) # for some reason I can't see some of the results becomes negative in the np array

for counter,value in enumerate(results):
    print("Number of agents on output slot " + str(counter) + ": " + str(value) + '\n') 

print("Elapsed computation time: " + str(elapsed_time) + " seconds\n")

plt.figure()
plt.bar(range(0,len(results)), results)
plt.xlabel('Output slots')
plt.ylabel('Number of agents')
plt.savefig('resultsFig')

while True:
    answer = input("To get a specific result, enter the slot number; otherwise enter -1 \n")
    answer = int(answer)
    if answer == -1:
            break

    if answer >= len(results) or answer < -1:
        print("Index out of results range\n")
        continue

    print("Number of agents on output slot " + str(answer) + ": " + str(results[int(answer)]) + '\n')

        





    

