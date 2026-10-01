"""Four-token maximal coupling, synthetic example, Python standard library only."""
import random, json, sys, platform, datetime
from pathlib import Path

def validate(p, q):
    if not p or len(p) != len(q):
        raise ValueError("nonempty distributions must have equal lengths")
    for dist in (p, q):
        if any(x < 0 for x in dist) or abs(sum(dist)-1) > 1e-10:
            raise ValueError("nonnegative probabilities must sum to one")

def couple(p, q, rng):
    # Draft z comes from p; retain the shared probability mass.
    z = rng.choices(range(len(p)), weights=p)[0]
    if rng.random() < min(1.0, q[z]/p[z]):
        return z, False
    residual = [max(b-a, 0) for a,b in zip(p,q)]
    return rng.choices(range(len(q)), weights=residual)[0], True

def main():
    p, q = [.4,.3,.2,.1], [.1,.2,.3,.4]
    validate(p,q)
    exact = [min(a,b)+max(b-a,0) for a,b in zip(p,q)]
    assert all(abs(a-b)<1e-12 for a,b in zip(exact,q))
    rng = random.Random(20261001)
    n=50000; counts=[0]*4; changed=0
    for _ in range(n):
        y, corrected = couple(p,q,rng); counts[y]+=1; changed+=corrected
    # Boundary cases: equal distributions and disjoint support.
    assert all(not couple(p,p,rng)[1] for _ in range(1000))
    assert all(couple([1.,0.],[0.,1.],rng)==(1,True) for _ in range(1000))
    for bad in (([],[]), ([1.],[.5,.5]), ([-.1,1.1],[.5,.5]), ([.5,.6],[.5,.5])):
        try: validate(*bad)
        except ValueError: pass
        else: raise AssertionError("invalid distribution accepted")
    out=dict(kind="synthetic four-token example, not LLM training",seed=20261001,n=n,p=p,q=q,
        counts=counts,observed=[x/n for x in counts],corrections=changed,
        correctionRate=changed/n,theoreticalCorrectionRate=sum(abs(a-b) for a,b in zip(p,q))/2,
        exactMarginal=exact,checks="equal/disjoint/invalid distributions passed",python=sys.version,
        platform=platform.platform(),runAt=datetime.datetime.now(datetime.timezone.utc).isoformat())
    Path(__file__).with_name("coupling-results.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=="__main__": main()
