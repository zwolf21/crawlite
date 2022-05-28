from itertools import groupby
from operator import itemgetter



def diselect(container, query):
    '''yield from diselect(container, ['companyName', 'description', 'website'])
       yield from diselect(container, ['companyName', ('representedBrands', 'value')])
    '''
    cntrq = [((), (0,), container)]
    records = []
    while cntrq:
        path, index, cntr = cntrq.pop(0)
        p = None
        if isinstance(cntr, dict):
            for key, value in cntr.items():
                p = *path, key,
                cntrq.append((p, index, value))
                if not isinstance(value, (dict,)):
                    records.append((p, index, value))
        
        elif isinstance(cntr, (list, tuple, set)):
            for i, c in enumerate(cntr):
                idx = *index, i
                cntrq.append((path, idx, c))

    selected = []
    min_index_length = None
    for path, index, value in records:
        for qry in query:
            oriq = qry
            if isinstance(qry, str):
                qry = qry,

            if (qry_length := len(qry)) > len(path):
                continue

            if path[-qry_length:] == qry:
                if min_index_length is not None:
                    min_index_length = min(len(index), min_index_length)
                else:
                    min_index_length = len(index)
                selected.append((index, oriq, value))

    selected = [
        (index[min_index_length-1], path, value)
        for index, path, value in selected
    ]

    for name, grouped in groupby(sorted(selected, key=itemgetter(0)), itemgetter(0)):
        ret = {
          key:value  for index, key, value in grouped
        }
        yield {q:ret[q] for q in query if q in ret.keys()}
        