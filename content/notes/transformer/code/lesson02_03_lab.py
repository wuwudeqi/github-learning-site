"""A reproducible toy BPE tokenizer and embedding lookup. Python stdlib only.
The tokenizer accepts one ASCII word at a time. No normalization, spaces,
byte fallback, special tokens or full-model training are implemented.
"""
from collections import Counter

CORPUS={'low':5,'lower':2,'new':6}
BASE=sorted(set(''.join(CORPUS)))
E=[[0.1,0.2,0.3],[0.2,0.0,0.1],[0.0,0.3,0.2],[0.1,-0.1,0.0],
   [-0.2,0.4,0.1],[0.3,0.2,-0.1],[0.4,0.1,0.2],[0.8,0.1,-0.2],
   [0.2,0.6,0.1],[-0.1,0.9,0.3]]

def merge_parts(parts,pair):
    out=[];i=0
    while i<len(parts):
        if i+1<len(parts) and tuple(parts[i:i+2])==pair:
            out.append(''.join(pair));i+=2
        else:out.append(parts[i]);i+=1
    return out

def train(rounds=4):
    splits={word:list(word) for word in CORPUS};vocab=BASE[:];rules=[];trace=[]
    for _ in range(rounds):
        counts=Counter()
        for word,parts in splits.items():
            for pair in zip(parts,parts[1:]):counts[pair]+=CORPUS[word]
        if not counts:break
        best=max(counts,key=counts.get)  # ties: first encountered in corpus/token order
        before={w:p[:] for w,p in splits.items()}
        splits={w:merge_parts(p,best) for w,p in splits.items()}
        rules.append(best);vocab.append(''.join(best))
        trace.append({'counts':dict(counts),'pair':best,'frequency':counts[best],
                      'before':before,'after':{w:p[:] for w,p in splits.items()}})
    return vocab,rules,trace

def encode(word,vocab,rules):
    unknown=set(word)-set(BASE)
    if unknown:raise ValueError('Toy base vocabulary lacks: '+repr(sorted(unknown)))
    parts=list(word)
    for pair in rules:parts=merge_parts(parts,pair)
    return parts,[vocab.index(p) for p in parts]

def matmul(a,b):
    assert len(a[0])==len(b)
    return [[sum(a[i][k]*b[k][j] for k in range(len(b)))
             for j in range(len(b[0]))] for i in range(len(a))]

def main():
    vocab,rules,trace=train()
    assert rules==[('l','o'),('lo','w'),('n','e'),('ne','w')]
    assert [r['frequency'] for r in trace]==[7,7,6,6]
    assert [sum(len(r['after'][w])*n for w,n in CORPUS.items()) for r in trace]==[36,29,23,17]
    for word,ids in [('lower',[7,0,4]),('newer',[9,0,4]),('new',[9])]:
        parts,out=encode(word,vocab,rules);assert out==ids
        assert ''.join(vocab[i] for i in out)==word
        print(word,parts,out)
    # Frozen ranks are not a synonym for left-to-right longest matching.
    parts=list('abc')
    for pair in [('b','c'),('a','b')]:parts=merge_parts(parts,pair)
    assert parts==['a','bc']  # longest-prefix matching would select ab + c
    ids=encode('lower',vocab,rules)[1]
    onehot=[[int(j==i) for j in range(len(vocab))] for i in ids]
    lookup=[E[i][:] for i in ids];assert matmul(onehot,E)==lookup
    repeated=[7,0,7];upstream=[[1,0,0],[0,2,0],[3,0,1]]
    grad=[[0,0,0] for _ in vocab]
    for idx,g in zip(repeated,upstream):
        grad[idx]=[a+b for a,b in zip(grad[idx],g)]
    assert grad[7]==[4,0,1] and grad[0]==[0,2,0]
    # Renumber IDs and reorder E consistently; the lookup output is unchanged.
    permutation=list(reversed(range(len(vocab))))
    e_new=[None]*len(vocab)
    for old,new in enumerate(permutation):e_new[new]=E[old]
    assert [e_new[permutation[i]] for i in ids]==lookup
    print('vocab:',list(enumerate(vocab)))
    print('merge frequencies:',[r['frequency'] for r in trace])
    print('X = S @ E =',lookup,'shape=(3,3)')
    print('repeated-row gradient: E[7]=',grad[7])
    print('All BPE, decoding, matrix and renumbering checks passed.')

if __name__=='__main__':main()
