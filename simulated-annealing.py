"""

03-04-2024

Vincenzo Bucaria

Università degli Studi di Messina


work in progress

last update 08/04/2024

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

debug = True
general_debug = True
save_graphs = True 
show_graphs = True 

# _______________________________________________________________________


def generate_initial_graph(constrained_nodes, mandatory_power_nodes, discretionary_power_nodes):
    print("DEBUG: generazione grafo", constrained_nodes, mandatory_power_nodes, discretionary_power_nodes)
    
    G = nx.Graph()
    all_nodes=[]
    
    if (constrained_nodes is not None) and (mandatory_power_nodes is not None) and (discretionary_power_nodes is not None):
        G.add_nodes_from(constrained_nodes, node_type='constrained')
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
                G.add_edge(i, j, latency=weight)
    return G

    
def draw_graph(G):
    plt.clf()
    global count_picture
    
    print("\tnodes_", G.nodes(), " edges:", G.edges)
    pos = nx.spring_layout(G)
    node_colors = {'constrained': 'green', 'power_mandatory': 'red', 'power_discretionary': 'orange'}
    colors = [node_colors[data['node_type']] for _, data in G.nodes(data=True)]
    edge_labels = {(i, j): G[i][j]['latency'] for i, j in G.edges()}
    
    nx.draw(G, pos, with_labels=True, node_color=colors, font_weight='bold')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
    plt.show()


def generate_greedy_initial_solution(graph, constrained_nodes, power_nodes):
    
    initial_solution_graph = nx.Graph()



    #Mediante la relazione utilizzata si tenta di cercare un compromesso tra
    
    # La miglior latenza tra il nodo constrained e il suo nodo power afferente
    # Il maggior numero di altri nodi constrained contattabili direttamente per mezzo del power node
    # Latenza media dei link gestiti dal power node 
    
    # In questo modo è possibile minimizzare il numero di hop


    for constrained_node in constrained_nodes:
        
        minimum_latency = 10000 #as like as infinite
        best_power_node_score = 0

        for power_node in power_nodes:

            edge_latency = graph[constrained_node][power_node]["latency"]
            
            
            if power_node in initial_solution_graph.nodes(): #Enables advanced score  
           
                constrained_neighbours = list(initial_solution_graph.neighbors(power_node))
                number_of_constrained_neighbours = len(constrained_neighbours)
                
                for constrained in constrained_neighbours:
                    neighbours_latency = initial_solution_graph[constrained][power_node]["latency"]
                neighbours_average_latency = neighbours_latency/number_of_constrained_neighbours
                
                if debug:
                    print("Neighbours of", power_node, "are:", constrained_neighbours, "Average latency: ", neighbours_average_latency, "ms")
            else:
                
                number_of_constrained_neighbours = 1
                neighbours_average_latency = 0
                        
            power_node_score = (1.4*number_of_constrained_neighbours)/(edge_latency+0.5*neighbours_average_latency)   
                
            if(power_node_score>best_power_node_score):
                best_power_node_score=power_node_score
                best_power_node = power_node
                minimum_latency = edge_latency
                type_of_power_node = graph.nodes[best_power_node]["node_type"]
                    
                

        print("the best power node for node", constrained_node, "is the",type_of_power_node, "node", best_power_node, "which minimum latency is", minimum_latency, "ms")
        
        
        initial_solution_graph.add_node(constrained_node, node_type="constrained")
        initial_solution_graph.add_node(best_power_node, node_type=type_of_power_node)
        initial_solution_graph.add_edge(constrained_node, best_power_node, latency=minimum_latency)
        
    for first_power_node in power_nodes:
        
        #Questo non funziona in quanto non abbiamo nessuna garanzia che il grafo sia connesso!
        # ci devo lavorare
        
        
        minimum_latency = 10000 #as like as infinite
        type_of_first_power_node = graph.nodes[first_power_node]["node_type"]
        for second_power_node in power_nodes:
            if second_power_node != first_power_node:
                edge_latency = graph[first_power_node][second_power_node]["latency"]
            
                if edge_latency < minimum_latency:
                    best_power_node = second_power_node
                    type_of_second_power_node = graph.nodes[best_power_node]["node_type"]
                    minimum_latency = edge_latency
                    
                
                
        initial_solution_graph.add_node(first_power_node, node_type=type_of_first_power_node)
        initial_solution_graph.add_node(best_power_node, node_type=type_of_second_power_node)
        initial_solution_graph.add_edge(first_power_node, best_power_node, latency=minimum_latency)
            
        
    
    
        
        
  
        
    return initial_solution_graph









# ___________________ simulated annealing parameters ____________________________


initial_T = 100 #to be defined
max_iterations_number = 100 #to be defined ...

# ... work in progress

# ______________________________________________________________________________




# _____________________ editable network parameters  ____________________________


total_nodes_quantity = 10                                            #Total quantity of nodes composing the graph. At the moment for test purpose let this quantity be 10
constrained_nodes_quantity = int(0.7*total_nodes_quantity)              #Total quantity of constrained nodes, all of them must be connected in the graph with just 1 arc for node.
mandatory_power_nodes_quantity = int(0.2*(total_nodes_quantity))        #Quantity of mandatory nodes: that is, they must be included in the graph and each of them can have more then 1 arc.
discretionary_power_nodes_quantity = total_nodes_quantity-constrained_nodes_quantity-mandatory_power_nodes_quantity #Quantity of power nodes that can be used for getting a better spanning tree but are not mandatory


print("\n \n__________ Network parameters ___________ \n")
print("total number of nodes: ", total_nodes_quantity, "\ntotal number of constrained nodes: ", constrained_nodes_quantity, "\ntotal number of power nodes: ", mandatory_power_nodes_quantity, "(mandatory)", discretionary_power_nodes_quantity, "(discretionary)")
print("___________________________________________\n \n")

# _______________________________________________________________________________



 
# The first thing i can do is the random generation of the graph including all type of nodes (discretionary power nodes are included).


constrained_nodes = range(1, constrained_nodes_quantity+1)
power_nodes = range(constrained_nodes_quantity+1, constrained_nodes_quantity+mandatory_power_nodes_quantity+discretionary_power_nodes_quantity+1)
mandatory_power_nodes = range(constrained_nodes_quantity+1, constrained_nodes_quantity+mandatory_power_nodes_quantity+1)
discretionary_power_nodes = range(constrained_nodes_quantity+mandatory_power_nodes_quantity+1, total_nodes_quantity+1)

print(constrained_nodes)
print(mandatory_power_nodes)
print(discretionary_power_nodes)



initial_graph = generate_initial_graph(constrained_nodes, mandatory_power_nodes, discretionary_power_nodes)
draw_graph(initial_graph)
initial_solution_graph = generate_greedy_initial_solution(initial_graph, constrained_nodes, power_nodes)
draw_graph(initial_solution_graph)














