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

    # Return a string
    def __str__(self):
        status = f"Node Id: {self.id}, Num Entries: {len(self.DV)}\n"
        for destination, data in self.DV.items():
            status += (f"type {type(destination)}, {destination} : [{data[0]}, {data[1]} {data[2]}]\n")
        status += "Neighbors: \n"
        for neighbor, cost in self.neighbors.items(): 
            status += (f"{neighbor} : {cost}\n")
        
        return status
    
    def send_updated_dv_to_neighbors(self):
        message_dic = {}
        message_dic['seq_num'] = self.seq_num
        self.seq_num += 1 
        message_dic['sender'] = self.id
        message_dic['DV'] = self.DV
        message = json.dumps(message_dic)

        self.send_to_neighbors(message)
    
    def recalculate_dv(self):
        DV_changed = False

        for destination in self.DV: 
            destination = int(destination)

            current_cost_to_dest = float('inf')

            for neighbor, DV_received in self.DVs_received.items():
                neighbor_cost = self.neighbors[neighbor]
                temp_cost_to_dest = float('inf')
                temp_AS_Path = []

                if destination in DV_received:
                    temp_cost_to_dest = neighbor_cost + DV_received[destination][0]
                    temp_AS_Path = DV_received[destination][1]

                # update our DV if going through the neighbor is cheaper and if we don't exist in their AS_Path to (prevent loops)
                if temp_cost_to_dest < current_cost_to_dest and self.id not in temp_AS_Path: 
                    current_cost_to_dest = temp_cost_to_dest
                    new_AS_Path = copy.deepcopy(temp_AS_Path)
                    new_AS_Path.insert(0, neighbor)

                    self.DV[destination] = [temp_cost_to_dest, new_AS_Path, neighbor]
                    DV_changed = True
        return DV_changed

    # Fill in this function
    def link_has_been_updated(self, neighbor, latency):
        # latency == -1 if delete a link
        if latency == -1: 
            del self.neighbors[neighbor]
            del self.DV[neighbor]
            del self.messages_received[neighbor]
            del self.DVs_received[neighbor]
        # neighbor exists in DV and it's information may need to be updated
        elif neighbor in self.DV: 
            self.neighbors[neighbor] = latency 
        # neighbor doesn't exist in DV and it's information should be added to the DV and propagated
        else: 
            self.neighbors[neighbor] = latency 
            self.DV[neighbor] = [latency, [neighbor], neighbor]
        
        self.recalculate_dv()
        self.send_updated_dv_to_neighbors()

    # Fill in this function
    def process_incoming_routing_message(self, m):
        DV_changed = False

        message = json.loads(m)

        sender = message['sender']
        seq_num = message['seq_num']
        received_DV = message['DV']

        print(f"message to {self.id} received from {sender}")
        print(received_DV)

        # new message from my neighbor or seq_num of message is greater than the one we have, so we should consider it
        if (sender not in self.messages_received or seq_num > self.messages_received[sender]) and sender in self.neighbors: 
            print("considered")
            self.messages_received[sender] = seq_num
            self.DVs_received[sender] = {int(k): v for k, v in received_DV.items()}

            # loop through DV from neighbor
            for destination, arr in received_DV.items(): 
                destination = int(destination)
                cost, AS_Path, next_hop = arr

                temp_cost_to_dest = cost + self.neighbors[sender]
                current_cost_to_dest = float('inf')
                if destination in self.DV:
                    current_cost_to_dest = self.DV[destination][0]

                # update our DV if going through the neighbor is cheaper and if we don't exist in their AS_Path to (prevent loops)
                if temp_cost_to_dest < current_cost_to_dest and self.id not in AS_Path: 
                    new_AS_Path = copy.deepcopy(AS_Path)
                    new_AS_Path.insert(0, sender)

                    self.DV[destination] = [temp_cost_to_dest, new_AS_Path, sender]
                    DV_changed = True

        # propogate changed DV
        if DV_changed: 
            print("change propogated")
            self.send_updated_dv_to_neighbors()
        

    # Return a neighbor, -1 if no path to destination
    def get_next_hop(self, destination):
        if destination not in self.DV: 
            return -1
        return self.DV[destination][-1]
