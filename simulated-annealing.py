"""

03-04-2024

Vincenzo Bucaria

Università degli Studi di Messina


work in progress

"""


import networkx as nx
import matplotlib.pyplot as plt
from itertools import combinations
import random
from collections import Counter
from itertools import chain
import copy
import time
import os
import sys




# _________________________ DEBUG SETTINGS ______________________________


general_debug = True
save_graphs = True 
show_graphs = True 

# _______________________________________________________________________


def generate_initial_graph(constrained_nodes, mandatory_power_nodes, discretionary_power_nodes):
    print("DEBUG: generazione grafo", constrained_nodes, mandatory_power_nodes, discretionary_power_nodes)
    
    G = nx.Graph()
    all_nodes=[]
    
    if (constrained_nodes is not None) and (mandatory_power_nodes is not None) and (discretionary_power_nodes is not None):
        G.add_nodes_from(constrained_nodes, node_type='weak')
        G.add_nodes_from(mandatory_power_nodes, node_type='power_mandatory')
        G.add_nodes_from(discretionary_power_nodes, node_type='power_discretionary')
        all_nodes = list(constrained_nodes) + list(mandatory_power_nodes) + list(discretionary_power_nodes)
    elif (constrained_nodes is not None) and (mandatory_power_nodes is not None):
        G.add_nodes_from(constrained_nodes, node_type='weak')
        G.add_nodes_from(mandatory_power_nodes, node_type='power_mandatory')
        all_nodes = list(constrained_nodes) + list(mandatory_power_nodes)
    elif (constrained_nodes is not None) and (discretionary_power_nodes is not  None):
        G.add_nodes_from(constrained_nodes, node_type='weak')
        G.add_nodes_from(discretionary_power_nodes, node_type='power_discretionary')
        all_nodes = list(constrained_nodes) + list(discretionary_power_nodes)

    elif discretionary_power_nodes is not None:
        G.add_nodes_from(discretionary_power_nodes, node_type='power_discretionary')
        all_nodes = list(discretionary_power_nodes)    
    else:
        print("\tnot a possible case")

    for i in all_nodes:
        for j in all_nodes:
            if i != j and not G.has_edge(i, j):
                # Assign a random weight between 10 and 80 (ms) (you can customize the range)
                weight = random.randint(10, 80)
                G.add_edge(i, j, weight=weight)
    return G

    










# ___________________ simulated annealing parameters ____________________________


initial_T = 100 #to be defined
max_iterations_number = 100 #to be defined ...

# ... work in progress

# ______________________________________________________________________________




# _____________________ editable network parameters  ____________________________


total_nodes_quantity = 8                                                #Total quantity of nodes composing the graph
constrained_nodes_quantity = int(0.4*total_nodes_quantity)              #Total quantity of constrained nodes, all of them must be connected in the graph with just 1 arc for node.
mandatory_power_nodes_quantity = int(0.2*(total_nodes_quantity))        #Quantity of mandatory nodes: that is, they must be included in the graph and each of them can have more then 1 arc.
discretionary_power_nodes_quantity = total_nodes_quantity-constrained_nodes_quantity-mandatory_power_nodes_quantity #Quantity of power nodes that can be used for getting a better spanning tree but are not mandatory


print("\n \n__________ Network parameters ___________ \n")
print("total number of nodes: ", total_nodes_quantity, "\ntotal number of constrained nodes: ", constrained_nodes_quantity, "\ntotal number of power nodes: ", mandatory_power_nodes_quantity, "(mandatory)", discretionary_power_nodes_quantity, "(discretionary)")
print("___________________________________________\n \n")

# _______________________________________________________________________________




# The first thing i can do is the random generation of the graph including all type of nodes (discretionary power nodes are included).


constrained_nodes = range(1, constrained_nodes_quantity+1)
mandatory_power_nodes = range(constrained_nodes_quantity+1, constrained_nodes_quantity+mandatory_power_nodes_quantity+1)
discretionary_power_nodes = range(constrained_nodes_quantity+mandatory_power_nodes_quantity+1, total_nodes_quantity+1)

print(constrained_nodes)
print(mandatory_power_nodes)
print(discretionary_power_nodes)



initial_graph = generate_initial_graph(constrained_nodes, mandatory_power_nodes, discretionary_power_nodes)







