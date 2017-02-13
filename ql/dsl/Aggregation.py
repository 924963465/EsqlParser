'''
Created on Feb 9, 2017

@author: qs
'''

from ql.parse.ASTNode import Node
from ql.parse.parser import TK
from ql.dsl import parse_object,parse_value
from ql.dsl import Query



def bucket_function(tree: Node,_size):
    bucket = {}
    bucket[tree.get_value()] = {}
    field = parse_value(tree.get_child(0))
    bucket[tree.get_value()]['field'] = field
    for i in range(1,tree.get_children_count()):
        bucket[tree.get_value()].update(parse_object(tree.get_child(i)))
    if _size != -1:
        bucket[tree.get_value()]['size'] = _size
    aggs = {"aggs":{}}
    aggs['aggs'][field] = bucket
    return (field,aggs)


def bucket_field(tree: Node,_size):
    bucket = {}
    bucket['terms'] = {}  
    
    field = parse_value(tree)
    bucket['terms']['field'] = field
    if _size != -1:
        bucket['terms']['size'] = _size
    
    aggs = {"aggs":{}}
    aggs['aggs'][field] = bucket
    
    return (field,aggs)


def bucket(tree: Node,_size):
    if tree.get_type() == TK.TOK_FUNCTION:
        return bucket_function(tree,_size)
    else:
        return bucket_field(tree,_size)


def metrics_functions(selexpr):
    alias = ''
    if hasattr(selexpr,'alias'):
        alias = selexpr.alias
    else:
        alias = 'count'
    metric = {}
    if selexpr.selexpr.function_name == 'count':
        metric['value_count'] = {}
    else:
        metric[selexpr.selexpr.function_name] = {'field':selexpr.selexpr.function_parms[0]}
    return {alias:metric}



def get_metrics(selexprs):
    retval = {}
    for e in selexprs:
        if type(e.selexpr) == Query.FunctionXpr:
            retval.update(metrics_functions(e))
    return retval



class AggBuckets(object):    
    __slots__ = ('buckets')
    
    def __init__(self,tree: Node,_size,root=True):
        self.buckets = []
        for element in tree.get_children():
            self.buckets.append(bucket(element,_size))
    def dsl(self,_selexpr):
        (field,bucket) = self.buckets[0]
        aggs_body = bucket
        cur_aggs = aggs_body['aggs'][field]
        for i in range(1,len(self.buckets)):
            (field,bucket) = self.buckets[i]
            cur_aggs.update(bucket)
            cur_aggs = cur_aggs['aggs'][field]
        metrics = get_metrics(_selexpr)
        cur_aggs['aggs'] = metrics
        return aggs_body
    
    