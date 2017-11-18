from networkx import DiGraph
from .flow import run
from contextlib import contextmanager

class Node:
    def __init__(self, contents, metadata):
        self.contents = contents
        self.metadata = metadata
    def __repr__(self):
        return f'Node({self.contents!r}, {self.metadata!r})'

class Edge:
    def __init__(self, contents, metadata):
        self.contents = contents
        self.metadata = metadata
    def __repr__(self):
        return f'Edge({self.contents!r}, {self.metadata!r})'
    def __iter__(self):
        nodes = list(self.traverse())
        return zip(nodes, nodes[1:])
    def traverse(self):
        for x in self.contents:
            if isinstance(x, Node):
                yield x
            if isinstance(x, Edge):
                yield from x.traverse()

class WorkflowGroup:
    def __init__(self):
        self.workflows = {}
        self.current   = None
    def add_node(self, *args, **kwargs):
        return self.current.add_node(*args, **kwargs)
    def add_edge(self, *args, **kwargs):
        return self.current.add_edge(*args, **kwargs)
    def run(self, *args, **kwargs):
        for flow in self.workflows.values():
            flow.run(*args, **kwargs)
    def new(self, name=None):
        self.current = self.workflows[name] = Workflow()
        return self.workflows[name]
    @contextmanager
    def __call__(self, item):
        if isinstance(item, int):
            workflow = list(self.workflows.values())[item]
        else:
            if item not in self.workflows:
                workflow = self.new(item)
            else:
                workflow = self.workflows[item]
        previous = self.current
        self.current = workflow
        yield
        self.current = previous
    def __getitem__(self, item):
        if isinstance(item, int):
            return list(self.workflows.values())[item]
        else:
            return self.workflows[item]

class Workflow:
    def __init__(self):
        self.nodes, self.edges = [], []
    def add_node(self, contents, metadata=(), *args, **kwargs):
        node = Node(contents, metadata)
        self.nodes.append(node)
        return node
    def add_edge(self, contents, metadata=(), *args, seps=(), **kwargs):
        seps = {s.strip() for s in seps[0]}
        if len(seps) != 1:
            raise TypeError('cannot mix data & control edges in the same line')
        if not isinstance(metadata, tuple):
            metadata = (metadata, )
        if '-' in seps:
            metadata = (*metadata, on.control)
        elif '|' in seps:
            metadata = (*metadata, on.data)
        edge = Edge(contents, metadata)
        self.edges.append(edge)
        return edge
    def run(self, filename):
        data_graph    = DiGraph()
        control_graph = DiGraph()
        for edge in self.edges:
            if on.success in edge.metadata:
                for i, node in enumerate(edge.traverse()):
                    if i == 0: continue
                    node.metadata = ('tf-success',)
            elif on.failure in edge.metadata:
                for i, node in enumerate(edge.traverse()):
                    if i == 0: continue
                    node.metadata = ('tf-failure',)
            elif on.always in edge.metadata:
                for i, node in enumerate(edge.traverse()):
                    if i == 0: continue
                    node.metadata = ('tf-always',)

            if on.start in edge.metadata:
                for node in edge.traverse():
                    node.metadata = ('tf-start', *node.metadata)
                    break
        for node in self.nodes:
            if node.metadata:
                node.contents = f'{" ".join(node.metadata)} {node.contents!r}'
        for edge in self.edges:
            if on.data in edge.metadata:
                for u,v in edge:
                    data_graph.add_edge(u, v)
            elif on.control in edge.metadata:
                for u,v in edge:
                    control_graph.add_edge(u, v)
        for node in self.nodes:
            data_graph.add_node(node)
            control_graph.add_node(node)
        run(data_graph, control_graph, filename=filename)

class Tags:
    start   = 'start'
    always  = 'always'
    success = 'success'
    failure = 'failure'
    data    = 'data'
    control = 'control'

on = Tags()
__workflow__ = WorkflowGroup()
__workflow__.new()
__node__ = __workflow__.add_node
__edge__ = __workflow__.add_edge
