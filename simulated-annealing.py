"""

03-04-2024

Vincenzo Bucaria

Università degli Studi di Messina


work in progress

last update 10/04/2024


- aggiunto il sistema a punti anche per il collegamento tra power nodes
- risolto il problema per cui potevano essere generati dei loop o avere soluzioni con grafi non connessi
- sistemati i parametri per il sistema a punti dei nodi constrained

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

    def connect_constrained_nodes():


    
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
                            
                #Come posso calcolare il punteggio? 

                #Più è bassa la latenza diretta tra il nodo constrained e il power node e più alto sarà il punteggio
                
                direct_latency_score = 60/(edge_latency)

                #Se ci sono già altri nodi constrained (nel limite della capacity) il punteggio può aumentare perchè possiamo diminuire il numero di hop

                neighbours_quantity_score = 0.2*number_of_constrained_neighbours

                #Se la latenza dei nodi constrained affenti al power node è bassa il punteggio può aumentare
                if number_of_constrained_neighbours>1:
                    neighbours_latency_score = 10/(neighbours_average_latency)
                else:
                    neighbours_latency_score = 0
                
                

                
                power_node_score = direct_latency_score+neighbours_quantity_score+neighbours_latency_score


                ''
                print("Score for power node", power_node, "is: ", power_node_score, "direct latency: ", edge_latency, "average neighbours latency: ", neighbours_average_latency) 
                    
                if(power_node_score>best_power_node_score):
                    best_power_node_score=power_node_score
                    best_power_node = power_node
                    minimum_latency = edge_latency
                    type_of_power_node = graph.nodes[best_power_node]["node_type"]
                        
                    

            print("the best power node for node", constrained_node, "is the",type_of_power_node, "node", best_power_node, "which minimum latency is", minimum_latency, "ms")
            
            
            initial_solution_graph.add_node(constrained_node, node_type="constrained")
            initial_solution_graph.add_node(best_power_node, node_type=type_of_power_node)
            initial_solution_graph.add_edge(constrained_node, best_power_node, latency=minimum_latency)

        return initial_solution_graph
            
        #Mediante la relazione utilizzata si tenta di cercare un compromesso tra
        
        # La miglior latenza tra il nodo constrained e il suo nodo power afferente
        # Il maggior numero di altri nodi constrained contattabili direttamente per mezzo del power node
        # Latenza media dei link gestiti dal power node 
        
        # In questo modo è possibile minimizzare il numero di hop


    def connect_power_nodes():   

    
        def sort_power_nodes():

            power_nodes_sorted_list = list()

            for power_node in power_nodes:
                
                if power_node in initial_solution_graph.nodes():
                    power_nodes_sorted_list.append((power_node, len(initial_solution_graph.adj[power_node])))
                else:
                    power_nodes_sorted_list.append((power_node, 0))
        

            power_nodes_sorted_list = data_ordinata = sorted(power_nodes_sorted_list, key=lambda x: x[1], reverse=True)

           
            return power_nodes_sorted_list
        
        sorted_power_nodes_tuples = sort_power_nodes()


        processed_power_nodes = list()

        for first_power_node_tuple in sorted_power_nodes_tuples:
            
            first_power_node = first_power_node_tuple[0]
            
            #Questo non funziona in quanto non abbiamo nessuna garanzia che il grafo sia connesso!
            # ci devo lavorare
            

            minimum_latency = 10000 #as like as infinite
            type_of_first_power_node = graph.nodes[first_power_node]["node_type"]

            
            add_to_graph = 0
            best_power_score = 0
            for second_power_node_tuple in sorted_power_nodes_tuples:
                second_power_node = second_power_node_tuple[0]
                if second_power_node != first_power_node:
                    edge_latency = graph[first_power_node][second_power_node]["latency"]
                
                    
                    if (second_power_node not in processed_power_nodes):

                        
                        second_power_node_quantity_score = second_power_node_tuple[1]

                        second_power_node_latency_score = 100/edge_latency

                        second_power_score = second_power_node_latency_score + second_power_node_quantity_score
                        

                        print("debug: Score for power", second_power_node, "is: ", second_power_score, ". Quantity score:", second_power_node_quantity_score, "Latency score: ", second_power_node_latency_score)
                        
                        if second_power_score > best_power_score:
                            best_power_node = second_power_node
                            type_of_second_power_node = graph.nodes[best_power_node]["node_type"]
                            best_power_score = second_power_score
                            best_power_score_latency = edge_latency
                            add_to_graph = 1
            processed_power_nodes.append(first_power_node)
            print("best node ", best_power_node)        
            if add_to_graph:
                initial_solution_graph.add_node(first_power_node, node_type=type_of_first_power_node)
                initial_solution_graph.add_node(best_power_node, node_type=type_of_second_power_node)
                initial_solution_graph.add_edge(first_power_node, best_power_node, latency=best_power_score_latency)
        
        
        
        print("fatto")
    
    
    
    initial_solution_graph = connect_constrained_nodes()
    connect_power_nodes()



            
    return initial_solution_graph




def is_graph_connected():
    
    #restituisce true se il grafo è connesso, viceversa false
    
    pass










# ___________________ simulated annealing parameters ____________________________


initial_T = 100 #to be defined
max_iterations_number = 100 #to be defined ...

# ... work in progress

# ______________________________________________________________________________




# _____________________ editable network parameters  ____________________________


total_nodes_quantity = 20  #Total quantity of nodes composing the graph. At the moment for test purpose let this quantity be 10
constrained_nodes_quantity = int(0.7*total_nodes_quantity)      #Total quantity of constrained nodes, all of them must be connected in the graph with just 1 arc for node.
mandatory_power_nodes_quantity = int(0.2*(total_nodes_quantity))   #Quantity of mandatory nodes: that is, they must be included in the graph and each of them can have more then 1 arc.
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














