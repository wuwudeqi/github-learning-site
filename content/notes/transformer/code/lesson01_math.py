"""Lesson 01: exact output-head, gradient and decoding examples; Python stdlib only.
Run: python3 lesson01_math.py
This is NOT a trained Transformer. h and W are hand specified.
"""
import math

W = [[math.log(6), math.log(3), 0.0], [0.0, math.log(8), 0.0]]

def softmax(z, temperature=1.0):
    assert temperature > 0
    u = [v / temperature for v in z]
    m = max(u)
    e = [math.exp(v - m) for v in u]
    return [v / sum(e) for v in e]

def head(h, w):
    return [sum(h[i] * w[i][j] for i in range(len(h))) for j in range(len(w[0]))]

def loss(h, w, target=0):
    z = head(h, w)
    m = max(z)
    return m + math.log(sum(math.exp(v - m) for v in z)) - z[target]

def entropy(p):
    return -sum(v * math.log(v) for v in p if v > 0)

def close(a, b, tol=1e-9):
    assert abs(a-b) < tol, (a, b)

def main():
    h = [1.0, 0.0]
    p = softmax(head(h, W))
    cold = softmax(head([0.0, 1.0], W))
    for a,b in zip(p,[.6,.3,.1]): close(a,b)
    for a,b in zip(cold,[.1,.8,.1]): close(a,b)
    for a,b in zip(p,softmax([x+1000 for x in head(h,W)])):close(a,b)
    close(math.log(p[0]/p[1]),math.log(2))
    g = [v - (j == 0) for j,v in enumerate(p)]
    grad_w = [[h[i]*g[j] for j in range(3)] for i in range(2)]
    grad_h = [sum(g[j]*W[i][j] for j in range(3)) for i in range(2)]
    eps=1e-6; errors=[]
    for i in range(2):
        for j in range(3):
            plus=[r[:] for r in W];minus=[r[:] for r in W]
            plus[i][j]+=eps;minus[i][j]-=eps
            numerical=(loss(h,plus)-loss(h,minus))/(2*eps)
            errors.append(abs(numerical-grad_w[i][j]))
    for i in range(2):
        plus=h[:];minus=h[:];plus[i]+=eps;minus[i]-=eps
        numerical=(loss(plus,W)-loss(minus,W))/(2*eps)
        errors.append(abs(numerical-grad_h[i]))
    assert max(errors)<1e-7
    updated=[[W[i][j]-.1*grad_w[i][j] for j in range(3)] for i in range(2)]
    assert loss(h,updated)<loss(h,W)
    # A two-context, one-head causal attention example, independent of the output head.
    x=[[1.,0.],[0.,1.]]
    scores=[[sum(a*b for a,b in zip(q,k))/math.sqrt(2) if j<=i else -math.inf
             for j,k in enumerate(x)] for i,q in enumerate(x)]
    att=[softmax(row) for row in scores]
    close(att[0][1],0)
    close(att[1][0],1/(1+math.exp(1/math.sqrt(2))))
    context=[[sum(att[i][j]*x[j][d] for j in range(2)) for d in range(2)] for i in range(2)]
    # K/V only; no activations, weights or allocator overhead.
    kv_bytes=2*32*4096*8*128*2
    assert kv_bytes==536870912
    print('hot probabilities:',p,'cold probabilities:',cold)
    print('loss:',loss(h,W),'dL/dz:',g,'dL/dW:',grad_w,'dL/dh:',grad_h)
    print('finite-difference max error:',max(errors))
    print('after one W update, loss:',loss(h,updated),'p:',softmax(head(h,updated)))
    print('causal attention:',att,'output:',context)
    print('temperature .5:',softmax(head(h,W),.5))
    print('entropy hot/cold (nats):',entropy(p),entropy(cold))
    print('KL(hot||cold):',sum(a*math.log(a/b) for a,b in zip(p,cold)))
    print('GQA KV cache MiB:',kv_bytes/1024**2)
    print('All numerical checks passed.')

if __name__=='__main__':main()
