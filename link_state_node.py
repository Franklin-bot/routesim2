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

    def link_update(self, link, latency):
        if link in self.graph:
            self.graph[link][0] = latency
            self.graph[link][1] += 1
        else:
            self.graph[link] = [latency, 1]

    # Return a string
    def __str__(self):
        status = f"Node Id: {self.id}\n"
        for link, data in self.graph.items():
            status += (f"Link: {link} Latency: {data[0]} seq_num {data[1]}\n")

    # Fill in this function
    def link_has_been_updated(self, neighbor, latency):
        # latency = -1 if delete a link
        link = frozenset([self.id, neighbor])
        self.link_update(link, latency)                             # update current node

        link_update = {'sender':self.id, 'link':list(link), 'latency':latency, 'seq_num':self.graph[link][1]}
        lu = json.dumps(link_update)
        self.send_to_neighbors(lu)


        self.update_routing_table()

    # Fill in this function
    def process_incoming_routing_message(self, m):

        message = json.loads(m)

        sender = message['sender']
        link = message['link']
        latency = message['latency']
        seq_num = message['seq_num']

        link_update = {'sender':self.id, 'link':link, 'latency':latency, 'seq_num':seq_num}
        lu = json.dumps(link_update)

        if link not in self.graph or self.graph[link][1] < seq_num:
            self.link_update(link, latency)
            self.send_to_neighbors(lu)
        elif self.graph[link][1] > seq_num:
            self.send_to_neighbor(sender, json.dumps({'sender':self.id, 'link':link, 'latency':self.graph[link][0], 'seq_num':self.graph[link][1]}))

        self.update_routing_table()


    # Return a neighbor, -1 if no path to destination
    def get_next_hop(self, destination):
        return self.routing_table[destination]


    def update_routing_table(self):

        neighbors = {}
        for link, state in self.graph.items():
            if link != -1:
                a = link[0]
                b = link[1]
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
                neighbor = link[0]
                latency = link[1]
                cost = curr_cost + latency

                if cost < costs[neighbor]:
                    costs[neighbor] = cost
                    predecessor[neighbor] = curr_node
                    heapq.heappush(heap, (cost, neighbor))

        for node, cost in costs.items():
            if node == self.id or cost == float('inf'):
                self.routing_table[node] = -1
            
            prev = node
            while (predecessor[prev] != self.id):
                prev = predecessor[prev]

            self.routing_table[node] = prev


                

                

            









        
