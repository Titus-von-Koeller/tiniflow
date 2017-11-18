#!/usr/bin/env python3

from re import compile, escape, DOTALL, UNICODE
from collections import namedtuple

Pattern = namedtuple('Pattern', 'block node edge workflow tempchange permchange nodesep edgedata nodedata workflowdata')

def generate_patterns(nodesep='[|-]'):
    node_sigil         = escape('*')
    edge_sigil         = escape('%')
    nodesep_sigil      = nodesep
    workflow_sigil     = escape('>')
    tempchange_sigil   = escape('$')
    permchange_sigil   = tempchange_sigil * 2
    edgedata_sigil     = nodesep_sigil * 2
    nodedata_sigil     = nodesep_sigil * 2
    workflowdata_sigil = nodesep_sigil * 2

    block  = r'([^\n]+)(\n)'
    indent = r'[ \t]*'
    name   = r'\w+'
    assign = escape(':') + r'?' + escape('=')
    space  = r'\s*'
    expr   = r'.+'

    _name   = f'(?P<name>{name})?'
    _assign = f'(?P<assign>{assign})'
    _expr   = f'(?P<expr>{expr})'
    _indent = f'(?P<indent>{indent})'

    node         = _indent + space.join([node_sigil, _name, _assign, _expr])
    edge         = _indent + space.join([edge_sigil, _name, _assign, _expr])
    workflow     = _indent + space.join([workflow_sigil, _expr])
    tempchange   = _indent + space.join([tempchange_sigil, _name, _assign, _expr])
    permchange   = _indent + space.join([permchange_sigil, _name, _assign, _expr])
    nodesep      = space + nodesep_sigil      + space
    edgedata     = space + edgedata_sigil     + space
    nodedata     = space + nodedata_sigil     + space
    workflowdata = space + workflowdata_sigil + space

    flags = DOTALL | UNICODE
    return Pattern(
        block        = compile(block,        flags=flags),
        node         = compile(node,         flags=flags),
        edge         = compile(edge,         flags=flags),
        workflow     = compile(workflow,     flags=flags),
        tempchange   = compile(tempchange,   flags=flags),
        permchange   = compile(permchange,   flags=flags),
        nodesep      = compile(nodesep,      flags=flags),
        edgedata     = compile(edgedata,     flags=flags),
        nodedata     = compile(nodedata,     flags=flags),
        workflowdata = compile(workflowdata, flags=flags),
    )

def parse(text):
    temp_changes = {}
    perm_changes = {}
    p = generate_patterns(**{**perm_changes, **temp_changes})
    for block in p.block.split(text):
        if block.strip():
            temp_changes.clear()
        mo = p.node.fullmatch(block)
        if mo:
            indent = mo.group('indent')
            name   = mo.group('name')
            expr   = mo.group('expr')
            assign = mo.group('assign')
            args   = p.nodedata.split(expr)
            f      = 'f' if assign == ':=' else ''
            arg    = args[0].replace('\\','\\\\').replace('"', r'\"')
            args   = ', '.join([f'{f}"{arg}"', *args[1:]])
            yield f'{indent}{name} = __node__({args})'
            continue
        
        mo = p.workflow.fullmatch(block)
        if mo:
            indent = mo.group('indent')
            expr   = mo.group('expr')
            args   = p.workflowdata.split(expr)
            args   = ', '.join([f'f{args[0]!r}', *args[1:]])
            yield f'{indent}with __workflow__({args}):'
            continue
        
        mo = p.edge.fullmatch(block)
        if mo:
            indent = mo.group('indent')
            name   = mo.group('name')
            expr   = mo.group('expr')
            args   = p.edgedata.split(expr)
            seps   = [p.nodesep.findall(arg) for arg in args]
            args   = [p.nodesep.split(arg) for arg in args]
            args   = ', '.join(f'({", ".join(arg)})' for arg in args)
            yield f'{indent}{name or "_"} = __edge__({args}, seps={seps!r})'
            continue
        
        mo = p.tempchange.fullmatch(block)
        if mo:
            indent = mo.group('indent')
            name   = mo.group('name')
            expr   = mo.group('expr')
            temp_changes[name] = expr
            yield f'{indent}#$ {name} = {expr}'
            p = generate_patterns(**{**perm_changes, **temp_changes})
            continue
            
        mo = p.permchange.fullmatch(block)
        if mo:
            indent = mo.group('indent')
            name   = mo.group('name')
            expr   = mo.group('expr')
            perm_changes[name] = expr
            yield f'{indent}#$$ {name} = {expr}'
            p = generate_patterns(**{**perm_changes, **temp_changes})
            continue
            
        yield block

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('filename')
    parser.add_argument('--disable-prologue', action='store_true', default=False)
    parser.add_argument('--disable-epilogue', action='store_true', default=False)

    args = parser.parse_args()
    
    with open(args.filename) as f:
        text = f.read()
    first_line, rest = text.split('\n', 1)
    if not first_line.startswith('#!'):
        raise Exception('first line MUST be shebang!')
    prologue = 'from tiniflow.prologue import __node__, __edge__, __workflow__, on'
    epilogue = f'__workflow__.run({args.filename!r})'
    if (args.disable_prologue):
        prologue = ''
    if (args.disable_epilogue):
        epilogue = ''
    parsed = parse(rest)
    first_line = ''.join([prologue, first_line])
    print(first_line, ''.join(parsed), epilogue, end='', sep='\n')
