from pathlib import Path
import subprocess
import csv
import numpy
import matplotlib.pyplot as plt
import math
import time




#________________________________________________________MAIN___________________________________________________________________-

def encode_group(n):
    group = 0
    size = int(n)
    for i in range(0, size):
        bit = int(input())
        while bit!=0 and bit!=1:
            print("invalid input. Enter 1 if item is in group or 0 else\n")
            bit = int(input())

        group += int(math.pow(2,i))*bit
    
    return group

def bits_override(g1, g2):
    if g1|g2 == g1^g2:
        return False
    else:
        return True

def print_partial_sums(lst,n):
    sum = 0
    partial_sums = ""
    partial_sums += "0"
    for i in range(0,n-1):
        sum += lst[i]
        partial_sums += (", " + str(sum))

    return partial_sums


def print_setup(groups_num, groups_list):
    setup = "{s0![0],fast}"
    for i in range(1, groups_num):
        for x in range(0, int(math.pow(2,i))):
            if not bits_override(groups_list[i], x):
                setup += ".{s" + str(i) + "!["+ str(x) +"],fast}"

    return setup


def print_setup_params(num):
    setup_params = "s0"
    for i in range(1, num):
        setup_params += ",s" + str(i)

    return setup_params

# Main:

groups_num = int(input("Enter number of groups\n"))
size = int(input("Enter total number of items\n"))
groups_list = []

for i in range(0, groups_num):
    print("For group number " + str(i) + ", Enter 0 if item is in group and 0 o.w\n")
    groups_list.append(encode_group(size))

groups_list.sort()
num_of_agents = input("Enter number of agents")
sum = sum(groups_list)

#------------------------------------------Create the bcs code-------------------------------------#
bcs_code = '''
fast = 1000;
r = 1;


Setup[''' + print_setup_params(groups_num) + '''] = ''' + print_setup(groups_num, groups_list) + '''.{start![1] ,fast};
 
 
P[x,y,sum,last] = {start?[1], r}.
(
[y==sum]->{done![x],fast} ||

[y!=sum]->{y?[x], fast}.({splitDown,1}.P[x,y+1,sum,0] + {splitDiag,1}.P[x+1,y+1,sum,1]) ||

[y!=sum]->{~y?[0],fast}.( [last == 0] -> {continueStraight, r}.P[x,y+1,sum,0] + [last == 1]-> {continueStraight, r}.P[x+1,y+1,sum,1]) ||

[y!=sum]->{y?[0],fast}.{~y?[x],fast}.{splitDown,1}.P[x,y+1,sum,0]
);


Setup[''' + print_partial_sums(groups_list, groups_num) + '''] || ''' + str(num_of_agents) + '''*P[0,0,'''+ str(sum) +''',0];'''

#---------------------------------------------------------------------------------------------------#



#---------------------------Create a new file for the generated code and run a simulation---------------------# 

BCS_file = open("Exact_cover_generated_bcs_code.bc", "w")    # Open a new text file with write premmisions
BCS_file.write(bcs_code)                         # Write the bcs code to the file
BCS_file.close()                                 # close the file

DIR_path = Path().absolute()

start = time.time()  # get time before computation
subprocess.run(str(DIR_path) + '/bin/bcs Exact_cover_generated_bcs_code.bc', shell = True)	# Run BCS simulation on the generated code
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
