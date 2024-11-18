from simulator.node import Node
import json


class Distance_Vector_Node(Node):
    def __init__(self, id):
        super().__init__(id)
        self.id = id
        self.DV = {}
        # neighbor, latency
        self.neighbors = {}
        # neighbor, [DV, seq_num]
        self.neighbor_DV = {}
        # destination, next hop
        self.routing_table = {}

        self.seq_num = 1

    def send_dv(self):

        message = {'sender':self.id, 'dv':self.DV, 'seq_num':self.seq_num}
        m = json.dumps(message)
        self.send_to_neighbors(m)
        
    # Return a string
    def __str__(self):
        return "Rewrite this function to define your node dump printout"

    # Fill in this function
    def link_has_been_updated(self, neighbor, latency):

        self.neighbors[neighbor] = latency
        if self.recompute_dv(): self.send_dv()
        pass

    # Fill in this function
    def process_incoming_routing_message(self, m):
        message = json.loads(m)
        sender = message['sender']
        DV = message['dv']
        seq_num = message['seq_num']

        if sender not in self.neighbor_DV or self.neighbor_DV[sender][1] < seq_num:
            self.neighbor_DV[sender] = [DV, seq_num]
            if self.recompute_dv():
                self.send_dv()


    # Return a neighbor, -1 if no path to destination
    def get_next_hop(self, destination):
        if destination not in self.routing_table:
            print(f"ERROR: Destination node {destination} not in routing table of Node {self.id}")
        else:
            return self.routing_table[destination]

    def recompute_dv(self):

        changed = False






        if changed:
            self.seq_num += 1
        return changed