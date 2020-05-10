from pathlib import Path

import subprocess

import csv

import numpy

import matplotlib.pyplot as plt

import math

import time

import abc



class Script_generator:



    def __init__(self, list, num_of_agents, bcs_file_name):

        self.list = list

        self.list_sum = sum(list)

        self.list_length = len(list)

        self.num_of_agents = int(num_of_agents)

        self.bcs_file_name = bcs_file_name

        self.bcs_code = ""

        self.DIR_path = Path().absolute()

        self. elapsed_time = 0

        self.results = [[]]

        self.tagged = True

        self.agents_info = {}

        self.num_of_threads = 1

        self.num_of_simulations = 1

        self.sim_results = []

    #**************************** Print functions ******************************************************#



    def print_partial_sums(self):

        # The function returns a string that describes the partial sums of self.list

        partial_sums_list = self.get_partial_sums()

        

        partial_sums = "0"



        for item in partial_sums_list:

            partial_sums += ", " + str(item)

        

        return partial_sums



    def print_setup_params(self):

        setup_params = "s0"

        for i in range(1, self.list_length):

            setup_params += ",s" + str(i)



        return setup_params



    @abc.abstractmethod

    def print_setup(self):

        '''This method prints the bcs setup. Implementation in inheriting classes'''

        return



    def print_sim_results(self, i):

        results = self.results[i]

        elapsed_time = self.elapsed_time



        for counter,value in enumerate(results):

            print("Number of agents on output slot " + str(counter) + ": " + str(value) + '\n') 



        print("Elapsed computation time: " + str(elapsed_time) + " seconds\n")



    def print_all_sims_results(self):

        

        print("\n--------------------------------------RESULTS--------------------------------------------\n\n")



        for i in range(0, len(self.results)):

            print("__________________________________Simulation #%d results_______________________________\n"%(i+1))

            self.print_sim_results(i)

            print("\n________________________________________________________________________________________\n")



    def print_start_P_untagged(self):

        

        string = "|| num_of_agents*P[0,0," + str(self.list_sum) + ",0,0]\n"   # all agents have serial = 0

        return string



    def print_start_P_tagged(self):

        

        serial = 0

        string = ""



        for i in range(0, self.num_of_agents):

            string += "||P[0,0," + str(self.list_sum) + ",0,"+ str(serial) +"]\n"

            serial += 1



        return string



    def print_processes_start(self):

        

        if self.tagged:

            return self.print_start_P_tagged()

        else:

            return self.print_start_P_untagged()



    def print_constants(self):

        string = '''

        fast = 1000;

        r = 1;

        num_of_agents = ''' + str(self.num_of_agents) + ";"

        return string

        

    def create_bcs_code(self):



                bcs_code = self.print_constants() + '''





                Setup[''' + self.print_setup_params() + '''] = \n \t \t \t \t''' + self.print_setup() + '''.{start![1] ,fast};

                

                

                P[x,y,sum,last,serial] = {start?[1], r}.

                (

                [y==sum]->{done![x],fast} ||



                [y!=sum]->{y?[x], fast}.({splitDown,fast}.P[x,y+1,sum,0,serial] + {splitDiag,fast}.P[x+1,y+1,sum,1,serial]) ||



                [y!=sum]->{~y?[0],fast}.( [last == 0] -> {continueStraight, fast}.P[x,y+1,sum,0,serial] + [last == 1]-> {continueStraight, fast}.P[x+1,y+1,sum,1,serial]) ||



                [y!=sum]->{y?[0],fast}.{~y?[x],fast}.{blockedSplitDown,fast}.P[x,y+1,sum,0,serial]

                );





                Setup[''' + self.print_partial_sums() + ''']''' + "\n" + self.print_processes_start() + ";"



                #---------------------------------------------------------------------------------------------------#

                self.bcs_code = bcs_code



    #***************************************************************************************************#





    #***************************** Interpret results functions *****************************************#



    def interpret_results_tagged(self, sim_results):

        # This function gets results of *one* simulation (csv obj) and returns slots count and agents info dict

        agents_info = {}

        DIR_path = self.DIR_path

        

        results = numpy.zeros(self.list_sum + 1, dtype = numpy.uint64)

        

    

        for line in sim_results:

        

            if "splitDown" in line or "splitDiag" in line or "done" in line: # If this line is in our interest



                x = line[line.index("x") + 1]      # get x 

                x = int(x)



                y = line[line.index("y") + 1]      # get y

                y = int(y)



                serial = line[line.index("serial") + 1]   # get the proccess serial number



                if not serial in agents_info:  # If the proccess is not in our dictionary, add it

                    agents_info[serial] = ""

                

                if( "done" in line):

                    results[x] += 1



                if "splitDown" in line:

                    agents_info[serial] += "[x:" + str(x) + ", y:" + str(y) + ", Down]" 

                

                if "splitDiag" in line:

                    agents_info[serial] += "[x:" + str(x) + ", y:" + str(y) + ", Diag]"

                

                #TODO: create a class "agent_info" so we can easily get info on agents instead of this dictionary

        return results, agents_info

    

    def interpret_results_untagged(self, sim_results):

        #----------------------------Read and interpret the results file----------------------------------------------#

        list_sum = self.list_sum

        results = numpy.zeros(list_sum + 1, dtype = numpy.uint64)

        

        for line in sim_results:

            if "P" in line:  # if this line describes a proccess (agent)

                if "done" in line:  # if the agent is done

                    index = int(line[line.index("x") + 1])  

                    results[index] += 1 # add 1 to the slot counting

        #-------------------------------------------------------------------------------------------------------------#

        return results



    def interpret_results(self):

        

        sims_res_file = open(str(self.DIR_path) + '/simulationOutput')

        sims_res_string = sims_res_file.read()

        sims_lst = self.split_simulations(sims_res_string)



        results = [[]]

        agent_info = [{}]

        

        for i, sim in enumerate(sims_lst):



            sim_csv = [[]]

            sim_lines = sim.split('\n')

            for k, line in enumerate(sim_lines):

                sim_csv[k] += line.split('\t')

                sim_csv.append([])



            if self.tagged:

                results[i], agent_info[i] = self.interpret_results_tagged(sim_csv)

                results.append([])

                agent_info.append({})

            

            else:   # not tagged

                results[i] = self.interpret_results_untagged(sim_csv)

                results.append([])



        self.results = filter_empty_lists(results) # remove redundent empty lists

        self.agents_info = filter_empty_lists(agent_info)



    def split_simulations(self, simulationOutput):

        simulationOutput = str(simulationOutput)

        sim_lst = simulationOutput.split(">=======")

        sim_lst = sim_lst[1:] # the file starts with a ">=====" so we get rid of the first empty string 

        return sim_lst

    

    #***************************************************************************************************#





    #***************************** Set functions *******************************************************#



    def set_num_of_threads(self, num):

        self.num_of_threads = str(num)

    

    def set_num_of_simulations(self, num):

        self.num_of_simulations = str(num)

        

    def set_tagged(self, bool):

        self.tagged = bool



    def set_results(self, results):

        self.results = results

    

    #**************************************************************************************************#

    

    #**************************** Files and simulation handling ***************************************#

    

    def run_simulation(self):

        #------------------------ Run bcs simulation -----------------------------------# 

        cmd = (str(self.DIR_path) + '/bin/bcs -t ' + str(self.num_of_threads) + ' -s '     # Create cmd

            + str(self.num_of_simulations) + " " + self.bcs_file_name)



        elapsed_time = File_handling.run_shell_command(cmd)

        

        self.elapsed_time = elapsed_time

        #-------------------------------------------------------------------------------#



    def generate_and_run(self):

        self.create_bc_file()

        self.run_simulation()



    def create_bc_file(self):

        File_handling.write_new_file(self.bcs_file_name, self.bcs_code)



    def save_plot(self, results, i):

        

        plt.figure()

        plt.bar(range(0,len(results)), results)

        plt.xlabel('Output slots')

        plt.ylabel('Number of agents')

        fig_name = 'resultsFig#' + str(i)

        plt.savefig(fig_name)



    def save_plots(self):

        for i,res in enumerate(self.results):

            self.save_plot(res, i)

    #**************************************************************************************************#



    #***************************** Browsing functions *************************************************#



    def browse_result_slots(self, indx):

        # this function lets the user browse the number of agents in each slot

        results = self.results[indx]



        while True:

            try:

                answer = int(input("To get a specific result, enter the slot number; to go back enter -1 \n"))

            

            except:    

                print("invalid input\n")

                continue

            

            if answer == -1:

                    break



            try:

                print("Number of agents on output slot " + str(answer) + ": " + str(results[int(answer)]) + '\n')



            except:

                if answer >= len(results) or answer < -1:

                    print("Index out of results range\n")

                    continue

                else:

                    print("unknown error")

            

    def browse_results_tagged(self, indx):

        # this function lets the user browse the number of agents in each slot and the path of every agent

        agents_info = self.agents_info[indx]

        while True:

            answer = input("To see a specific slot, enter 1;\nTo see an agent's route, enter 2 \nto go back enter -1 \n\n")

            answer = int(answer)

            if answer == -1:

                return

            

            if answer == 1:

                self.browse_result_slots(indx)

            

            if answer == 2: 

                answer = input("Enter agent's serial number ")

                answer = int(answer)

                if answer > self.num_of_agents-1 or answer < 0:

                    print("Invalid serial number")

                    continue



                print("Route taken by agent: ")

                print(agents_info.get(str(answer)) + '\n')



    def browse_sim_results(self, indx):

        if self.tagged:

            self.browse_results_tagged(indx)

        else:

            self.browse_result_slots(indx)



    def browse_main_menu(self):

        

        while True:

            try:

                sim_to_browse_index = int(input("Enter index of simulation to browse. to exit enter -1\n")) - 1

                

                if sim_to_browse_index == -2:

                    return

                else:

                    self.browse_sim_results(sim_to_browse_index)



            except:

                print("invalid input. try again\n")

                continue



    #**************************************************************************************************#



    def get_partial_sums(self):

        # The method returns a list of the partial sums of self.list

        lst = self.list

        return Math_funcs.partial_sums(lst)

    



    

class SSP(Script_generator):

        #------------------------------------------bcs model notes (SSP)-------------------------------------#

        #   Model explanation:

        #   At first, the setup process is started. It produces beacons at y levels that 

        #   correspond to the partial sums of the numbers given, these are the split junctions.

        #   These beacons transmit the value 1.

        #  

        #   After the setup is done, the agents are created, each with a unique serial number, and then

        #   begin to travel in the system. At each step an agent checks his y level:

        #   If there is no active beacon on this y channel, then the agent proceeds to travel in the last direction that he took.

        #   If there is an active beacon on this y channel, then it means the agent reached a split junction,

        #   and then there is a 50% chance that he will split down, and 50% chance that he will split diagonally

        # 

        #   When an agent reaches a y level that is equal to the SSP numbers sum, it creates a beacon 

        #   on a channel called "done" and transmits through it his x level.





    def __init__(self, list, num_of_agents, bcs_file_name):

        super().__init__(list, num_of_agents, bcs_file_name)



    def print_setup(self):

        

        setup = "{s0![0],fast} \n \t \t \t \t"

        

        for i in range(1, self.list_length):

            setup += ".{s" + str(i) + "![0],fast}"

        setup += '\n \t \t \t \t'

        return setup



    def create_bcs_code(self):

        # Optimized simulation code for SSP (reduced beacon transmits)



        bcs_code = (self.print_constants() + '''\n\n        

                Setup[''' + self.print_setup_params() + '''] = ''' + self.print_setup() + '''.{start![1] ,fast};

                

                

                P[x,y,sum,last,serial] = {start?[1], r}.

                (

                [y==sum]->{done![x],fast} ||



                [y!=sum]->{y?[0..sum], fast}.({splitDown,1}.P[x,y+1,sum,0,serial] + {splitDiag,1}.P[x+1,y+1,sum,1,serial]) ||



                [y!=sum]->{~y?[0..sum],fast}.( [last == 0] -> {continueStraight, r}.P[x,y+1,sum,0,serial] + [last == 1]-> {continueStraight, r}.P[x+1,y+1,sum,1,serial])

                );





                Setup[''' + self.print_partial_sums() + ''']''' + "\n" + self.print_processes_start()) + ';'



                #---------------------------------------------------------------------------------------------------#

        self.bcs_code = bcs_code



    #***************************************************************************************************#



class Exact_cover(Script_generator):

   

   #------------------------------------------Create the bcs code (Exact Cover)-------------------------------------#

            #   Model explanation:

            #   At first, the setup process is started. It produces beacons at y levels that 

            #   correspond to the partial sums of the sets encoding. For each set there is a calculation

            #   of what x level bits don't override the set encoding. A set transmits over his beacon 

            #   an x value if and only if this x value bits do not override the set encoding's bits.

            #  

            #   After the setup is done, the agents are created, each with a unique serial number, and then

            #   begin to travel the network. At each step an agent checks his y level:

            #   If there is no active beacon on this y channel that transmits x, then the agent proceeds to travel in the last direction that he took.

            #

            #   If there is an active beacon on this y channel that transmits x, then it means the agent reached a split junction,

            #   and then there is a 50% chance that he will split down, and 50% chance that he will split diagonally.

            #   If there is an active beacon on this y channel but it does not transmit x, then it means the agent reached

            #   a blocked junction, then it will proceed in the last direction that it took.

            #  

            #   When an agent reaches a y level that is equal to the exact cover groups encoding sum, it creates a beacon 

            #   on a channel called "done" and transmits through it his x level.



    def __init__(self, list, num_of_agents, bcs_file_name, group_size):

        super().__init__(list, num_of_agents, bcs_file_name)

        self.group_size = group_size



    def print_setup(self):

        

        max_junctions = int(math.pow(2, self.group_size)) - 1

        partial_sums = self.get_partial_sums()



        setup = "{s0![0],fast} \n \t \t \t \t"

        

        for i in range(0, self.list_length-1):

            junctions_on_level = min(max_junctions, partial_sums[i])

            

            for x in range(0, junctions_on_level + 1):          # until junctions_on_level including

                if not Math_funcs.bits_override(self.list[i+1], x):

                    setup += ".{s" + str(i+1) + "!["+ str(x) +"],fast}"

            

            setup += "\n \t \t \t \t"



        return setup



    

    @staticmethod

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







class User_IO:

    @staticmethod

    def manual_SSP_input():

        # number of elements as input 

                lst_length = int(input("Enter the length of the set and a set of numbers for the SSP: ")) 

                lst = []



                # iterating till the range 

                for i in range(0, lst_length): 

                    ele = int(input()) 

                    lst.append(ele) # adding the element 

                    

                lst.sort()

                

                num_of_agents = input("Enter amount of agents")



                return lst, num_of_agents

    @staticmethod

    def primes_input():



        lst_length = int(input("Enter the amount of first prime numbers to use as a set for the SSP"))

        lst = Math_funcs.calc_first_n_primes(lst_length)

        num_of_agents = input("Enter amount of agents")



        return lst, num_of_agents

    @staticmethod

    def Exact_cover_input():



        lst_length = int(input("Enter number of groups\n"))

        size = int(input("Enter total number of items\n"))

        lst = []



        for i in range(0, lst_length):

            print("For group number " + str(i) + ", Enter 1 if item is in group and 0 o.w\n")

            lst.append(Exact_cover.encode_group(size))



        lst.sort()

        

        num_of_agents = input("Enter number of agents")



        return lst, num_of_agents, size

    @staticmethod

    def menu():

        # creating an empty list 

        lst = [] 

        mode = int(input("Choose simulation mode;\n 1: Manual SSP \n 2: Run SSP on first n primes \n 3: Exact Cover Problem"))



        if  mode == 1:

            lst, num_of_agents = User_IO.manual_SSP_input()

            scrptG = SSP(lst, num_of_agents, "manual_SSP_generated_bcs_code.bc") # Create a SSP object



        if mode == 2:

            lst, num_of_agents = User_IO.primes_input()

            scrptG = SSP(lst, num_of_agents, "primes_SSP_generated_bcs_code.bc") # Create a SSP object



        if mode == 3:

            lst, num_of_agents, size = User_IO.Exact_cover_input()

            scrptG = Exact_cover(lst, num_of_agents, "Exact_cover_generated_bcs_code.bc", size) # Create Exact_Cover obj

        



        tagged = input("tag agents? y: Yes, n: No")

        if tagged == "y":

            scrptG.set_tagged(True)

        elif tagged == "n":

            scrptG.set_tagged(False)



        num_of_threads = input("Enter number of threads to use")

        scrptG.set_num_of_threads(num_of_threads)        



        num_of_simulations = input("Enter number of simulations to run")

        scrptG.set_num_of_simulations(num_of_simulations)



        return scrptG



class File_handling:

    

    @staticmethod        

    def run_shell_command(cmd):

        

        cmd = str(cmd)

        

        start = time.time()  # get time before computation



        subprocess.run(cmd, shell = True)	# Run BCS simulation on the generated code



        end = time.time()    # get time after computation



        elapsed_time = end-start  # estimate the computation time



        return elapsed_time

    @staticmethod

    def write_new_file(file_name, data_to_write):

        

        file_name = str(file_name)

        data_to_write = str(data_to_write)



        #---------------------------Create a new file for the generated bcs code ---------------------# 

        file = open(file_name, "w")             # Open a new text file with write premissions

        file.write(data_to_write)               # Write the bcs code to the file

        file.close()                            # close the file        

        #----------------------------------------------------------------------------------------------#



    #def read_file_as_csv(path_to_file):





class Math_funcs:



    @staticmethod

    def partial_sums(lst):

        # The method returns a list of the partial sums of lst

        n = len(lst)



        sum = 0

        partial_sums = []



        for i in range(0,n-1):

            sum += lst[i]

            partial_sums.append(sum)



        return partial_sums



    @staticmethod

    def calc_first_n_primes(n):

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

    

    @staticmethod

    def bits_override(g1, g2):

        if g1|g2 == g1^g2:

            return False

        else:

            return True    



def filter_empty_lists(the_list):

   return [elem for elem in the_list if len(elem)!=0]



#   ______________________________Main______________________________________________

if __name__ == "__main__":



    scrptG = User_IO.menu()



    scrptG.create_bcs_code()



    scrptG.generate_and_run()



    scrptG.interpret_results()



    scrptG.save_plots()



    scrptG.print_all_sims_results()


    scrptG.browse_main_menu()

