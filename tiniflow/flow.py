#!/usr/bin/env python3

from networkx import DiGraph
from os import getpid, getppid, execvpe, environ, fork, waitpid
from os import open as os_open, pipe, dup2, close, set_inheritable
from os import O_RDONLY, O_WRONLY
from sys import argv

noread  = os_open('/dev/null', O_RDONLY)
nowrite = os_open('/dev/null', O_WRONLY)
set_inheritable(noread,  True)
set_inheritable(nowrite,  True)

shell = environ.get('SHELL', '/bin/sh')

class Pipe:
    def __init__(self):
        self.read, self.write = pipe()
    def __repr__(self):
        return f'Pipe(read={self.read}, write={self.write})\n{hex(id(self))}'

class Command:
    def __init__(self, command, ifds=[], ofds=[], env={}):
        self.command = command
        self.ifds, self.ofds = list(ifds), list(ofds)
        self.pid = None
        self.env = {'TF_DATA_IN':'0',         'TF_DATA_OUT':'1',
                    'TF_CTRL_IN':f'{noread}', 'TF_CTRL_OUT':f'{nowrite}', **env, }

    def __repr__(self):
        return f'Command({self.command!r})\n{hex(id(self))}'

    def close_fds(self):
        for fd, _, _ in self.ofds:
            try: close(fd)
            except OSError: pass

    def __call__(self):
        self.pid = fork()
        if self.pid:
            return self.pid
        for ifd, isdata, name in self.ifds:
            set_inheritable(ifd, True)
            if isdata:
                dup2(ifd, 0)
            self.env[f'{name}_IN'] = str(ifd)
        for ofd, isdata, name in self.ofds:
            set_inheritable(ofd, True)
            if isdata:
                dup2(ofd, 1)
            self.env[f'{name}_OUT'] = str(ofd)
        env = {**environ, **self.env}
        execvpe(shell, [shell, '-c', self.command], env)

class Tee:
    def __init__(self, ifds=[], ofds=[]):
        self.ifds, self.ofds = list(ifds), list(ofds)
        self.pid = None

    def __repr__(self):
        return f'Tee({self.ifds!r}, {self.ofds!r})\n{hex(id(self))}'

    def close_fds(self):
        for fd, _, _ in self.ofds:
            try: close(fd)
            except OSError: pass

    def __call__(self):
        self.pid = fork()
        if self.pid:
            return self.pid
        for ifd, _, _ in self.ifds:
            set_inheritable(ifd, True)
            dup2(ifd, 0)
        for ofd, _, _ in self.ofds:
            set_inheritable(ofd, True)
        args = [f'/proc/self/fd/{ofd}' for ofd, _, _ in self.ofds]
        command = f'tee {" ".join(args)} >/dev/null'
        execvpe(shell, [shell, '-c', command], environ)

def create_xgraph(graph, nodes, isdata, name):
    xgraph = DiGraph()
    for u in graph.nodes():
        xgraph.add_node(nodes[u])
        if graph.out_degree(u) > 1:
            t = Tee()
            xgraph.add_node(t)
            xgraph.add_edge(nodes[u], t)
            for v in graph.successors(u):
                xgraph.add_edge(t, nodes[v])
        else:
            for v in graph.successors(u):
                xgraph.add_edge(nodes[u], nodes[v])

    pipes  = {}
    pgraph = DiGraph()
    for u in xgraph.nodes():
        pgraph.add_node(u)
        for v in xgraph.successors(u):
            if (u, v) not in pipes:
                p = Pipe()
                for n in xgraph.predecessors(v):
                    pipes[n, v] = p
            p = pipes[u, v]
            pgraph.add_edge(u, p)
            pgraph.add_edge(p, v)

    for u, v in xgraph.edges():
        p = pipes[u, v]
        u.ofds.append((p.write, isdata, name))
        v.ifds.append((p.read, isdata, name))

    return xgraph

def run(data_graph, *extra_graphs, filename=''):
    nodes = {n: Command(n.contents) for n in data_graph.nodes()}
    data_xgraph = create_xgraph(data_graph, nodes, isdata=True, name='TF_DATA')
    extra_xgraphs = [create_xgraph(g, nodes, isdata=False, name='TF_CTRL')
                        for g in extra_graphs]
    all_nodes = set(data_xgraph.nodes())
    for xg in extra_xgraphs:
        all_nodes.update(xg.nodes())

    pids = {node(): node for node in all_nodes}

    # in the parent: wait for all children
    while pids:
        pid, rc = waitpid(-1, 0)
        if pid in pids:
            pids[pid].close_fds()
            del pids[pid]
