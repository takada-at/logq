# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
import os
import networkx as nx
import matplotlib.pyplot as plt

def drawg(G):
    pos=nx.spring_layout(G)
    nx.draw(G, pos)
    nx.draw_networkx_edges(G,pos,width=1.0,alpha=0.5)
def draw():
    labels0 = {(1, 2): 'hoge', (2, 3): 'fuga', (4, 5): 'piyo'}
    labels1 = {(0, 1): 'hoge', (0, 3): 'piyo', (1, 2): 'fuga',
               (1, 3): 'piyo', (2, 3): 'piyo'}
    NFA = nx.Graph()
    NFA.add_nodes_from([0,1,2,3,4,5])
    NFA.add_edges_from([(0, 1), (0, 4), (1, 2), (1, 4), (2, 3), (2, 4), (4, 5)], label=labels0)
    DFA = nx.Graph()
    DFA.add_nodes_from([0,1,2,3])
    DFA.add_edges_from([(0, 1), (0, 3), (1, 2), (1, 3), (2, 3)], label=labels1)
    drawg(NFA)
    path = os.path.join(os.path.dirname(__file__), 'nfa.png')
    plt.savefig(path)
    drawg(DFA)
    path = os.path.join(os.path.dirname(__file__), 'dfa.png')
    plt.savefig(path)

def main():
    draw()

if __name__=='__main__':
    main()

