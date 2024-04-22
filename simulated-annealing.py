"""

03-04-2024

Vincenzo Bucaria

Università degli Studi di Messina


work in progress

update 10/04/2024


- aggiunto il sistema a punti anche per il collegamento tra power nodes
- risolto il problema per cui potevano essere generati dei loop o avere soluzioni con grafi non connessi
- sistemati i parametri per il sistema a punti dei nodi constrained

update 12/04/2024


- trovato un metodo migliore basato sull'algoritmo di Kruskal per la generazione della soluzione iniziale




update 16/04/2024


- aggiunto il concetto di capacity

"""




from networkx.algorithms import approximation
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
import math



# _________________________ DEBUG SETTINGS ______________________________

debug = True
general_debug = True
save_graphs = True 
show_graphs = True 

# _______________________________________________________________________


def generate_initial_graph(constrained_nodes, mandatory_power_nodes, discretionary_power_nodes):
    #print("DEBUG: generazione grafo", constrained_nodes, mandatory_power_nodes, discretionary_power_nodes)
    
    #E' utile farsi restituire un grafo dove i nodi constrained non sono direttamente connessi tra loro
    
    G = nx.Graph()
    G_edit = nx.Graph()
    all_nodes=[]
    
    if (constrained_nodes is not None) and (mandatory_power_nodes is not None) and (discretionary_power_nodes is not None):
        G.add_nodes_from(constrained_nodes, node_type='constrained', links=0)
        G.add_nodes_from(mandatory_power_nodes, node_type='power_mandatory', links=0)
        G.add_nodes_from(discretionary_power_nodes, node_type='power_discretionary', links=0)
        G_edit.add_nodes_from(constrained_nodes, node_type='constrained', links=0 )
        G_edit.add_nodes_from(mandatory_power_nodes, node_type='power_mandatory',links=0)
        G_edit.add_nodes_from(discretionary_power_nodes, node_type='power_discretionary', links=0)
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

        if G_edit.nodes[i]["node_type"] == "constrained":
            capacity = 1
        else:
            capacity = random.random()
        G_edit.nodes[i]["capacity"] = capacity
        G.nodes[i]["capacity"] = capacity

        for j in all_nodes:
            if i != j and not G.has_edge(i, j):
                type_of_node_i = G_edit.nodes[i]["node_type"]
                type_of_node_j = G_edit.nodes[j]["node_type"]
                # Assign a random weight between 10 and 80 (ms) (you can customize the range)
                weight = random.randint(5, 80)
                G.add_edge(i, j, latency=weight)
                G.nodes[i]["links"] = G.nodes[i]["links"]+1
                G.nodes[j]["links"] = G.nodes[j]["links"]+1
                
                if (type_of_node_i == "constrained") and (type_of_node_j == "constrained"):
                    pass
                else:
                    G_edit.add_edge(i, j, latency=weight)    
                    G_edit.nodes[i]["links"] = G_edit.nodes[i]["links"]+1
                    G_edit.nodes[j]["links"] = G_edit.nodes[j]["links"]+1
                
    return G, G_edit

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

def connect_constrained_nodes(graph, solution_graph, power_nodes, constrained_nodes):


    
        for constrained_node in constrained_nodes:
        
            minimum_latency = 10000 #as like as infinite
            best_power_node_score = 0

            for power_node in power_nodes:

                edge_latency = graph[constrained_node][power_node]["latency"]
                
                direct_latency_score = edge_latency

                power_node_score = direct_latency_score
    
                if(power_node_score>best_power_node_score):
                    
                    best_power_node_score=power_node_score
                    best_power_node = power_node
                    minimum_latency = edge_latency
                    type_of_power_node = graph.nodes[best_power_node]["node_type"]
                        
                
            solution_graph.add_node(constrained_node, node_type="constrained", capacity=1, links=1)
            
            if(best_power_node not in solution_graph.nodes()):
                
                solution_graph.add_node(best_power_node, node_type=type_of_power_node, capacity=graph.nodes[best_power_node]["capacity"], links=0)
            
            solution_graph.nodes[best_power_node]["links"] = solution_graph.nodes[best_power_node]["links"] + 1
            solution_graph.add_edge(constrained_node, best_power_node, latency=minimum_latency)
            solution_graph.nodes[constrained_node]["power_node"] = best_power_node

        return solution_graph

def connect_power_nodes(graph, initial_solution_graph, power_nodes):
        processed_nodes = list()
        edges_list = list()
        sorted_edges_list = list()
        for first_power_node in power_nodes:
            for second_power_node in power_nodes:
                
                if first_power_node!=second_power_node:
                    if second_power_node not in processed_nodes:
                        edge_latency = graph[first_power_node][second_power_node]["latency"]
                        edges_list.append((first_power_node, second_power_node, edge_latency))
            processed_nodes.append(first_power_node)
        
        
        #1:B: ordinare la lista
        
        
        edges_list.sort(key=lambda a: a[2])
        
        #print(edges_list)
        
        
        for edges in edges_list:
            
            first_power_node = edges[0]
            second_power_node = edges[1]
            edge_latency = edges[2]
            
            if first_power_node not in initial_solution_graph.nodes():
                type_of_power_node = graph.nodes[first_power_node]["node_type"]
                initial_solution_graph.add_node(first_power_node, node_type=type_of_power_node, capacity=graph.nodes[first_power_node]["capacity"], links=0)
            if second_power_node not in initial_solution_graph.nodes():
                type_of_power_node = graph.nodes[second_power_node]["node_type"]
                initial_solution_graph.add_node(second_power_node, node_type=type_of_power_node, capacity=graph.nodes[second_power_node]["capacity"], links=0)

            initial_solution_graph.add_edge(first_power_node, second_power_node, latency=edge_latency)
            
            cycles = list(nx.simple_cycles(initial_solution_graph))
            #print(cycles)
            if(len(cycles)>0):
                initial_solution_graph.remove_edge(first_power_node, second_power_node)
            else:
                initial_solution_graph.nodes[first_power_node]["links"] = initial_solution_graph.nodes[first_power_node]["links"]+1
                initial_solution_graph.nodes[second_power_node]["links"] = initial_solution_graph.nodes[second_power_node]["links"]+1
                
                if first_power_node<second_power_node:
                   sorted_edges_list.append((first_power_node, second_power_node))
                else:
                   sorted_edges_list.append((second_power_node, first_power_node))
            
        return initial_solution_graph, sorted_edges_list

def generate_initial_solution(graph, constrained_nodes, power_nodes):
    
    initial_solution_graph = nx.Graph()
  
    initial_solution_graph = connect_constrained_nodes(graph, initial_solution_graph, power_nodes, constrained_nodes)
    initial_solution_graph, power_nodes_edges = connect_power_nodes(graph, initial_solution_graph, power_nodes)   

    return initial_solution_graph, power_nodes_edges


def calculate_aoc(graph):

    nodes_info = graph.nodes.data()

    cost = 0

    for node_info in nodes_info:
        cost = cost + (node_info[1]['links']*node_info[1]['capacity'])
    
    aoc = cost/len(nodes_info)

    return aoc

def calculate_acc(graph):
    average_latency = nx.average_shortest_path_length(graph, weight="latency")
    print("average latency: ", average_latency)
    #calcolo della latenza massima
    
    max_latency = 40

    acc = average_latency/max_latency

    return acc

def eliminate_discretionary_power_node(network_graph, graph, power_nodes, discretionary_power_nodes, power_nodes_edges):

    quantity_of_discretionary_power_nodes = len(discretionary_power_nodes)
    if(len(discretionary_power_nodes)>1):
        selected_discretionary_power_node = random.choice(discretionary_power_nodes)
    else:
        return graph, power_nodes, discretionary_power_nodes, power_nodes_edges

    if debug:
        print("randomly selected discretionary power node ", selected_discretionary_power_node)
    
    neighbors = list(graph.neighbors(selected_discretionary_power_node))

    #Se il discretionary power node non ha foglie ed è connesso al più ad un solo power node (discretionary o mandatory)
    #è possibile eliminarlo in maniera semplice (o forse converrebbe non eliminarlo).


    linked_power_nodes = list()
    linked_constrained_nodes = list()
    neighbors = list(graph.neighbors(selected_discretionary_power_node))

    for neighbor in neighbors:
        type_of_node = graph.nodes[neighbor]["node_type"]
        if(type_of_node == "constrained"):
            linked_constrained_nodes.append(neighbor)
        else:
            linked_power_nodes.append(neighbor)


    quantity_of_constrained_nodes = len(linked_constrained_nodes)
    quantity_of_power_nodes = len(linked_power_nodes) 

    
    if quantity_of_power_nodes < 1 and quantity_of_constrained_nodes < 1:
        return
        #Non ha senso eliminare un nodo foglia, potrebbe essere utile in un'iterazione successiva
    
    graph.remove_edges_from(power_nodes_edges)
    graph.remove_node(selected_discretionary_power_node)
    power_nodes.remove(selected_discretionary_power_node)
    discretionary_power_nodes.remove(selected_discretionary_power_node)
    processed_graph = connect_constrained_nodes(network_graph, graph, power_nodes, linked_constrained_nodes)
    processed_graph, power_nodes_edges = connect_power_nodes(network_graph, processed_graph, power_nodes)
    return graph, power_nodes, discretionary_power_nodes, power_nodes_edges
    
    
    
    #I nodi constrained connessi al power node devono essere spostati su un altro power node. Scelgo di collegarli al power node più vicino

def change_reference_power_node(network_graph, graph, power_nodes, constrained_nodes):
    
    #Estraggo randomicamente la quantità di nodi constrained da sollecitare
    number_of_constrained_nodes_to_edit = int(random.randint(1, int(len(constrained_nodes)/10)))
    print("number of constrained nodes to edit: ", number_of_constrained_nodes_to_edit)
    
    
    #Seleziono randomicamente i nodi constrained da sollecitare e li metto in una lista
    constrained_nodes_to_edit = list()
    selected_constrained = 0
    while selected_constrained < number_of_constrained_nodes_to_edit:

        constrained_node = random.choice(constrained_nodes)
        if(constrained_node not in constrained_nodes_to_edit):
            constrained_nodes_to_edit.append(constrained_node)
            selected_constrained=selected_constrained+1
    
    #collego randomicamente ogni constrained node a un nuovo power node

    for constrained in constrained_nodes_to_edit:
        previous_power_node = graph.nodes[constrained]["power_node"]
        graph.remove_edge(constrained, previous_power_node)
        random_power_node = random.choice(power_nodes)
        edge_latency = network_graph[constrained_node][random_power_node]["latency"]
        graph.add_edge(constrained, random_power_node, latency=edge_latency)
        graph.nodes[constrained]["power_node"] = random_power_node
        print("constrained ", constrained_node, "was previously connected to power node", previous_power_node, "now is connected to ", random_power_node)
     
        
        

    return graph

def simulated_annealing(network_graph, initial_solution_graph, constrained_nodes, power_nodes, discretionary_power_nodes, power_nodes_edges, initial_temperature=10, minimum_temperature=0.0001, max_iterations=1000):
    k = 0.2
    sa_solution_graph = initial_solution_graph
    temporary_graph = initial_solution_graph
    temperature = initial_temperature
    solution_energy = calculate_acc(sa_solution_graph)+calculate_aoc(sa_solution_graph)
    print("Initial energy: ", solution_energy)
    temp_power_nodes_edges = power_nodes_edges
    temp_power_nodes = power_nodes
    temp_discretionary_power_nodes = discretionary_power_nodes
    while(temperature > minimum_temperature):
        
        move = random.randrange(2)
        print(move)
        if(move == 0):
            temporary_graph, temp_power_nodes, temp_discretionary_power_nodes, temp_power_nodes_edges = eliminate_discretionary_power_node(network_graph, sa_solution_graph, power_nodes, discretionary_power_nodes, power_nodes_edges)
        elif(move == 1):
            temporary_graph = change_reference_power_node(network_graph, sa_solution_graph, power_nodes, constrained_nodes)
        
        iteration_energy = calculate_acc(temporary_graph)+calculate_aoc(temporary_graph)
        print("iteration energy", iteration_energy, "best energy ", solution_energy)
        delta_energy = (iteration_energy-solution_energy)
        print("delta energy: ", delta_energy)
        if(delta_energy < 0):
            sa_solution_graph = temporary_graph
            solution_energy = iteration_energy
            print("DEBUG: negative delta energy")
            power_nodes_edges = temp_power_nodes_edges
            power_nodes = temp_power_nodes
            discretionary_power_nodes = temp_discretionary_power_nodes
        else:
            random_factor = random.uniform(0, 1)
            print("DEBUG: positive delta energy, random factor", random_factor)
            if random_factor<math.exp(-delta_energy/(k*temperature)):                                                
                print("randomly accepted new solution, ", random_factor, "<",math.exp(-delta_energy/(k*temperature)))
                sa_solution_graph = temporary_graph
                solution_energy = iteration_energy
                power_nodes_edges = temp_power_nodes_edges
                power_nodes = temp_power_nodes
                discretionary_power_nodes = temp_discretionary_power_nodes
        temperature = temperature*0.9
    return sa_solution_graph
        


# ___________________ simulated annealing parameters ____________________________


initial_T = 120 #to be defined

max_iterations_number = 100 #to be defined ...

# ... work in progress

# ______________________________________________________________________________




# _____________________ editable network parameters  ____________________________


total_nodes_quantity = 20 #Total quantity of nodes composing the graph. At the moment for test purpose let this quantity be 10
constrained_nodes_quantity = int(0.7*total_nodes_quantity)      #Total quantity of constrained nodes, all of them must be connected in the graph with just 1 arc for node.
mandatory_power_nodes_quantity = int(0.2*(total_nodes_quantity))   #Quantity of mandatory nodes: that is, they must be included in the graph and each of them can have more then 1 arc.
discretionary_power_nodes_quantity = total_nodes_quantity-constrained_nodes_quantity-mandatory_power_nodes_quantity #Quantity of power nodes that can be used for getting a better spanning tree but are not mandatory


print("\n \n__________ Network parameters ___________ \n")
print("total number of nodes: ", total_nodes_quantity, "\ntotal number of constrained nodes: ", constrained_nodes_quantity, "\ntotal number of power nodes: ", mandatory_power_nodes_quantity, "(mandatory)", discretionary_power_nodes_quantity, "(discretionary)")
print("___________________________________________\n \n")

# _______________________________________________________________________________



 
# The first thing i can do is the random generation of the graph including all type of nodes (discretionary power nodes are included).


constrained_nodes = range(1, constrained_nodes_quantity+1)
power_nodes = list(range(constrained_nodes_quantity+1, constrained_nodes_quantity+mandatory_power_nodes_quantity+discretionary_power_nodes_quantity+1))
mandatory_power_nodes = list(range(constrained_nodes_quantity+1, constrained_nodes_quantity+mandatory_power_nodes_quantity+1))
discretionary_power_nodes = list(range(constrained_nodes_quantity+mandatory_power_nodes_quantity+1, total_nodes_quantity+1))

print(constrained_nodes)
print(mandatory_power_nodes)
print(discretionary_power_nodes)



network_graph, edited_network_graph = generate_initial_graph(constrained_nodes, mandatory_power_nodes, discretionary_power_nodes)
#draw_graph(network_graph)
#draw_graph(edited_network_graph)
initial_solution_graph, power_nodes_edges = generate_initial_solution(edited_network_graph, constrained_nodes, power_nodes)
initial_solution = initial_solution_graph
#draw_graph(initial_solution_graph)
initial_cost = calculate_acc(initial_solution_graph)+calculate_aoc(initial_solution_graph)
"""
second_solution_graph, power_nodes_edges = eliminate_discretionary_power_node(network_graph, initial_solution_graph, power_nodes, discretionary_power_nodes, power_nodes_edges)
draw_graph(second_solution_graph)

print("ACC of second solution:", calculate_acc(second_solution_graph), "AOC: ", calculate_aoc(second_solution_graph))
third_solution_graph = change_reference_power_node(network_graph, initial_solution_graph, power_nodes, constrained_nodes)
print("ACC of third solution:", calculate_acc(third_solution_graph), "AOC: ", calculate_aoc(third_solution_graph))
draw_graph(third_solution_graph)
"""
simulated_annealing_solution = simulated_annealing(network_graph, initial_solution_graph, constrained_nodes, power_nodes, discretionary_power_nodes, power_nodes_edges)

print("initial cost", initial_cost)
print("cost of sa solution:", calculate_acc(simulated_annealing_solution)+calculate_aoc(simulated_annealing_solution))
draw_graph(simulated_annealing_solution)