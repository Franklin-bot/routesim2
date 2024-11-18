from re import split
from simulator.node import Node
import json
import heapq


class Link_State_Node(Node):
    def __init__(self, id):
        super().__init__(id)
        self.id = id
        # frozenset (edge), [latency, sequence number]
        self.graph = {}
        # destination, next hop
        self.routing_table = {}
        self.nodes = set()
        self.paths = {}

    def link_update(self, link, latency):
        link = frozenset(link)
        if link in self.graph:
            self.graph[link][0] = latency
            self.graph[link][1] += 1
        else:
            self.graph[link] = [latency, 1]


    def encode_graph(self):
        encoded_graph = {}
        for key, value in self.graph.items():
            encoded_graph[",".join(sorted(map(str, key)))] = value  # frozenset to sorted string
        return encoded_graph

    def decode_graph(self, encoded_graph):
        decoded_graph = {}
        for key, value in encoded_graph.items():
            decoded_key = frozenset(sorted(int(n) for n in key.split(",")))  # String back to frozenset
            decoded_graph[decoded_key] = value
        return decoded_graph

    # Return a string
    def __str__(self):
        return "bruh"

    def print_status(self):
        status = f"------------------------------------\n"
        status += f"Node Id: {self.id}\n"
        status += f"Known Nodes: {self.nodes}\n"
        for link, data in self.graph.items():
            status += (f"Link: {link} Latency: {data[0]} seq_num {data[1]}\n")
        status += f"------------------------------------\n"
        print(status)

    # Fill in this function
    def link_has_been_updated(self, neighbor, latency):
        # latency = -1 if delete a link
        link = frozenset([self.id, neighbor])
        self.link_update(link, latency)                             # update current node
        self.nodes.add(self.id)

        if neighbor not in self.nodes:
            #print(f"New node detected by Node {self.id}")
            self.nodes.add(neighbor)

            encoded_graph = self.encode_graph()
            state_update = {'type':'state', 'sender':self.id, 'state': encoded_graph}
            su = json.dumps(state_update)
            #print(f"Sent state update to Node {neighbor}")
            self.send_to_neighbor(neighbor, su)

        link_update = {'type':'link', 'sender':self.id, 'link':list(link), 'latency':latency, 'seq_num':self.graph[link][1]}
        lu = json.dumps(link_update)
        self.send_to_neighbors(lu)

        #print(f"Simulation updated link between {self.id} and {neighbor} to {latency}")
        #self.print_status()

    # Fill in this function
    def process_incoming_routing_message(self, m):

        message = json.loads(m)
        sender = message['sender']
        #print(f"MESSAGE RECIEVED\n type: {message['type']}\n by: {self.id} \n from: {sender}")

        # handle state message
        if message['type'] == 'state':
            updated = False
            #print(f"State update recieved by Node {self.id} from Node {sender}")
            graph = self.decode_graph(message['state'])
            for link, state in graph.items():
                link = frozenset(link)
                self.nodes.add(list(link)[0])
                self.nodes.add(list(link)[1])

                if link not in self.graph or state[1] > self.graph[link][1]:
                    self.graph[link] = state
                    updated = True
            if updated: self.send_to_neighbors(m)
            #print(f"State of Node {self.id} updated!")
            #self.print_status()

        # handle link message
        elif message['type'] == 'link':
            link = frozenset(message['link'])
            latency = message['latency']
            seq_num = message['seq_num']

            #print(f"Node {self.id} received update that link {link} latency was updated to {latency}")

            link_update = {'type':'link', 'sender':self.id, 'link':list(link), 'latency':latency, 'seq_num':seq_num}
            lu = json.dumps(link_update)

            if link not in self.graph or self.graph[link][1] < seq_num:
                self.link_update(link, latency)
                self.nodes.add(list(link)[0])
                self.nodes.add(list(link)[1])
                self.send_to_neighbors(lu)
            elif self.graph[link][1] > seq_num:
                self.send_to_neighbor(sender, json.dumps({'type': 'link', 'sender':self.id, 'link':list(link), 'latency':self.graph[link][0], 'seq_num':self.graph[link][1]}))
                #print(f"Node {self.id} received update that link {link} latency was updated to {latency}")
        #self.print_status()

    def get_next_hop(self, destination):

        neighbors = {}
        for link, state in self.graph.items():
            if link != -1:
                a = list(link)[0]
                b = list(link)[1]
                if a not in neighbors: neighbors[a] = []
                if b not in neighbors: neighbors[b] = []
                neighbors[a].append((b, state[0]))
                neighbors[b].append((a, state[0]))

        costs = {n: float('inf') for n in neighbors}
        costs[self.id] = 0
        heap = [(0, self.id)]
        predecessor = {n: -1 for n in neighbors}

        while heap:
            curr_cost, curr_node = heapq.heappop(heap)

            for link in neighbors[curr_node]:
                neighbor, latency = link
                if latency == -1:
                    continue
                cost = curr_cost + latency

                if cost < costs[neighbor]:
                    costs[neighbor] = cost
                    predecessor[neighbor] = curr_node
                    heapq.heappush(heap, (cost, neighbor))
        if costs[destination] == float('inf'):
            return -1

            
        prev = destination
        while (predecessor[prev] != self.id and predecessor[prev] != -1):
            prev = predecessor[prev]
        return prev if predecessor[prev] == self.id else -1
