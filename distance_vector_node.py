from warnings import warn
from simulator.node import Node
import json
import copy

class Distance_Vector_Node(Node):
    def __init__(self, id):
        super().__init__(id)
        # Lists all known nodes in the network. For each node (destination): [cost (latency), [AS_Path], next_hop]
        self.DV = {id: [0, [], id]}
        # neighbor: cost (latency)
        self.neighbors = {}

        # node: seq num of last message received
        self.messages_received = {}

        # node: latest DV received from a neighbor
        self.DVs_received = {}

        # This node's sequence number 
        self.seq_num = 0

        # A set of all destinations the node has seen and has been sent
        self.destinations = set()

        self.seq_num = 1
        # Destination, [cost, path]
        self.DV = {}
        # neighbor, {Destination, [cost, path]}
        self.neighbor_DV = {}
        # neighbor, latency
        self.neighbors = {}
        # int
        self.nodes = set()


    def print_status(self):
        status = f"NODE {self.id}\n";
        status += "DV:\n";
        for destination, (cost, path) in self.DV.items():
            status += f"Destination: {destination}, Cost: {cost}, Path: {path}\n"
        status += "Routing Table:\n"

    def send_update(self):
        message = {'sender': self.id, 'dv': self.DV, 'seq_num': self.seq_num}
        m = json.dumps(message)
        self.send_to_neighbors(m)

    # Return a string
    def __str__(self):
        status = f"Node Id: {self.id}, Num Entries: {len(self.DV)}\n"
        # status += "Destinations:\n"
        # for destination in self.destinations:
        #     status += f"{destination}\n"
        for destination, data in self.DV.items():
            status += (f"type {type(destination)}, {destination} : [{data[0]}, {data[1]} {data[2]}]\n")
        # status += "Neighbors: \n"
        # for neighbor, cost in self.neighbors.items(): 
        #     status += (f"{neighbor} : {cost}\n")
        # status += "DVs Stored: \n"
        for neighbor, DV in self.DVs_received.items():
            status += f"Neighbor: {neighbor}\n"
            for destination, arr in DV.items():
                status += f"destination: {destination}, cost: {arr[0]}, AS_Path: {arr[1]}\n" 
        return status
    
    def send_updated_dv_to_neighbors(self):
        message_dic = {}
        message_dic['seq_num'] = self.seq_num
        self.seq_num += 1 
        message_dic['sender'] = self.id
        message_dic['DV'] = self.DV
        message = json.dumps(message_dic)

        self.send_to_neighbors(message)

    def compare_dv_tables(self, dv1, dv2):
        if dv1.keys() != dv2.keys():
            return False
        
        for key in dv1:
            value1 = dv1[key]
            value2 = dv2[key]

            if value1[0] != value2[0]:  
                return False
            if value1[1] != value2[1]:
                return False
            if value1[2] != value2[2]:
                return False
        return True
    
    def recalculate_dv(self):
        new_DV = {self.id: [0, [], self.id]}

        # Find the shortest path to my neighbors. Could be direct, or through another neighbor
        for neighbor, neighbor_cost in self.neighbors.items():
            curr_cost_to_neighbor = neighbor_cost
            curr_AS_Path = [neighbor]
            curr_next_hop = neighbor

            # loop through the neighbors 
            for other_neighbor, other_neighbor_cost in self.neighbors.items():
                temp_cost_to_neighbor = float('inf')
                temp_AS_Path = []

                if other_neighbor in self.DVs_received and neighbor in self.DVs_received[other_neighbor]:
                    temp_cost_to_neighbor = other_neighbor_cost + self.DVs_received[other_neighbor][neighbor][0]
                    temp_AS_Path = self.DVs_received[other_neighbor][neighbor][1]

                    if temp_cost_to_neighbor < curr_cost_to_neighbor and other_neighbor not in temp_AS_Path: 
                        curr_cost_to_neighbor = temp_cost_to_neighbor
                        curr_AS_Path = copy.deepcopy(temp_AS_Path)
                        curr_AS_Path.insert(0, other_neighbor)
                        curr_next_hop = other_neighbor
            new_DV[neighbor] = [curr_cost_to_neighbor, curr_AS_Path, curr_next_hop]

        for destination in self.destinations.difference(set(self.neighbors)): 
            current_cost_to_dest = float('inf')
            AS_Path = []
            next_hop = None

            for neighbor, neighbor_cost in self.neighbors.items():
                temp_cost_to_dest = float('inf')
                temp_AS_Path = []
                if neighbor in self.DVs_received: 
                    if destination in self.DVs_received[neighbor]:
                        temp_cost_to_dest = neighbor_cost + self.DVs_received[neighbor][destination][0]
                        temp_AS_Path = self.DVs_received[neighbor][destination][1]

                # update our DV if going through the neighbor is cheaper and if we don't exist in their AS_Path to (prevent loops)
                if temp_cost_to_dest < current_cost_to_dest and self.id not in temp_AS_Path: 
                    current_cost_to_dest = temp_cost_to_dest
                    AS_Path = copy.deepcopy(temp_AS_Path)
                    AS_Path.insert(0, neighbor)
                    next_hop = neighbor

                    new_DV[destination] = [current_cost_to_dest, AS_Path, next_hop]

        if self.compare_dv_tables(self.DV, new_DV):
            return False
        
        self.DV = new_DV
        return True

    # Fill in this function
    def link_has_been_updated(self, neighbor, latency):
        # latency == -1 if delete a link
        self.destinations.add(neighbor)
        if latency == -1: 
            del self.neighbors[neighbor]
            if neighbor in self.DVs_received:
                del self.DVs_received[neighbor]
                del self.messages_received[neighbor]
            del self.DV[neighbor]
            self.destinations.remove(neighbor)
            self.recalculate_dv()
        # neighbor exists in DV and it's information may need to be updated
        elif neighbor in self.DV: 
            self.neighbors[neighbor] = latency 
            self.recalculate_dv()
        # neighbor doesn't exist in DV and it's information should be added to the DV and propagated
        else: 
            self.neighbors[neighbor] = latency 
            self.DV[neighbor] = [latency, [neighbor], neighbor]
        
        self.send_updated_dv_to_neighbors()

    # Fill in this function
    def process_incoming_routing_message(self, m):
        DV_changed = False

        message = json.loads(m)

        sender = message['sender']
        seq_num = message['seq_num']
        received_DV = message['DV']

        # new message from my neighbor or seq_num of message is greater than the one we have, so we should consider it
        if (sender not in self.messages_received or seq_num > self.messages_received[sender]) and sender in self.neighbors: 
            self.messages_received[sender] = seq_num
            self.DVs_received[sender] = {int(k): v for k, v in received_DV.items()}

            # loop through DV from neighbor and add all possible new destinations
            for destination in received_DV: 
                destination = int(destination)
                self.destinations.add(destination)

            DV_changed = self.recalculate_dv()
        # propogate changed DV
        if DV_changed: 
            self.send_updated_dv_to_neighbors()


    # Return a neighbor, -1 if no path to destination
    def get_next_hop(self, destination):
        if destination not in self.DV: 
            return -1
        return self.DV[destination][-1]
