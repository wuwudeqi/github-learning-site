"""Teaching-only late interaction; Python 3 standard library, no model weights."""
from math import sqrt, isfinite, isclose


def normalize(rows):
    if not rows or not rows[0]:
        raise ValueError('vectors must not be empty')
    width = len(rows[0])
    result = []
    for row in rows:
        if len(row) != width or not all(isfinite(x) for x in row):
            raise ValueError('invalid dimensions or values')
        norm = sqrt(sum(x*x for x in row))
        if norm == 0:
            raise ValueError('zero vector has no direction')
        result.append([x/norm for x in row])
    return result


def maxsim(query, document):
    query, document = normalize(query), normalize(document)
    if len(query[0]) != len(document[0]):
        raise ValueError('query and document dimensions must match')
    return sum(max(sum(a*b for a, b in zip(q, d)) for d in document)
               for q in query)


def checks():
    q = [[1, 0], [0, 1]]
    assert isclose(maxsim(q, q), 2)
    assert isclose(maxsim(q, [[1, 0], [1, 0]]), 1)
    assert isclose(maxsim(q, [[.6, .8]]), 1.4)
    for bad in [[], [[0, 0]], [[1]], [[1, 0], [1]]]:
        try:
            maxsim(q, bad)
        except ValueError:
            continue
        raise AssertionError('invalid input was accepted')


if __name__ == '__main__':
    query = [[1, 0], [0, 1]]
    documents = {'A': [[1, 0], [0, 1]], 'B': [[1, 0], [1, 0]],
                 'C': [[.6, .8]]}
    for name, score in sorted(((k, maxsim(query, v)) for k, v in documents.items()),
                              key=lambda pair: pair[1], reverse=True):
        print(f'{name}: {score:.2f}')
    checks()
    print('checks: passed')
