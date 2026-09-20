"""Synthetic reward illustration, not a training run or paper reproduction."""
from pathlib import Path
import datetime
import json
import math
import sys

def reward(correct, length, alpha, tau, delta=0.05, think=True):
    efficiency = math.exp(-length * alpha / tau) if think else 1.0
    return int(correct) * (1 + delta * efficiency) - alpha, efficiency

curves = [{"tokens": length,
           "easy": reward(True, length, 0.81, 2048)[1],
           "hard": reward(True, length, 0.18, 2048)[1]}
          for length in range(0, 8193, 256)]
cases = []
for label, correct, length, think in [
    ("短但答错", False, 128, True),
    ("长但答错", False, 8192, True),
    ("短且答对", True, 1024, True),
    ("长且答对", True, 8192, True),
    ("直接答对", True, 128, False),
]:
    value, efficiency = reward(correct, length, 0.81, 2048, think=think)
    cases.append(dict(label=label, correct=correct, tokens=length,
                      think=think, reward=value, efficiency=efficiency))
assert cases[0]['reward'] == cases[1]['reward'] == -0.81
assert cases[2]['reward'] > cases[3]['reward'] > cases[0]['reward']
result = dict(kind="synthetic numeric illustration", executedAt=datetime.datetime.now().astimezone().isoformat(),
              python=sys.version.split()[0], tau=2048, delta=0.05, alphas=dict(easy=0.81, hard=0.18),
              formula="r=V*(1+delta*lambda)-alpha; Think lambda=exp(-L*alpha/tau); NoThink lambda=1",
              source="https://arxiv.org/abs/2609.19671v1", curves=curves, cases=cases)
here = Path(__file__).parent
(here / 'when2think-results.json.txt').write_text(json.dumps(result, ensure_ascii=False, indent=2))
template = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>When2Think 合成奖励示例</title>
<style>*{box-sizing:border-box}body{margin:0;background:#faf8f3;color:#19332f;font-family:Arial,"PingFang SC",sans-serif}main{width:1200px;padding:40px 48px}h1{font-size:32px;margin:0 0 10px}p{font-size:20px;margin:10px 0 24px}.pill{color:#735c40;font-size:17px}svg{display:block;background:white;border:1px solid #dbdfd7;border-radius:12px}text{font-family:Arial,"PingFang SC",sans-serif}.grid{display:grid;grid-template-columns:repeat(5,1fr);gap:14px;margin-top:22px}.case{background:white;padding:16px;border-top:4px solid #218b76;border-radius:6px}.case.bad{border-color:#b7644e}.case b{font-size:19px}.case div{font-size:15px;margin-top:7px}.case strong{font-size:25px;display:block;margin-top:8px}footer{margin-top:24px;font-size:16px;color:#52625d;line-height:1.6}</style>
<main><div class="pill">合成数据 · Python 实际计算 · 未训练模型</div><h1>只有答对，才获得“少用 token”的额外奖励</h1>
<p>上图只比较效率系数 λ；下方固定 α = 0.81，再看完整奖励 r。</p>
<svg id="chart" width="1104" height="370" viewBox="0 0 1104 370" aria-label="同一参考长度下，难题的效率系数衰减更慢"></svg><div class="grid" id="cases"></div>
<footer>人为设定 τ = 2048、δ = 0.05；α = 0.81 / 0.18 代表较容易 / 较难样本的参考正确率缩放值。<br>不包含批内优势标准化、采样或训练；曲线不是论文的准确率实验。来源：When2Think v1，奖励公式。</footer></main>
<script>const data=DATA;const svg=document.querySelector('#chart');const ns='http://www.w3.org/2000/svg';function el(tag,a,t){let e=document.createElementNS(ns,tag);Object.entries(a).forEach(([k,v])=>e.setAttribute(k,v));if(t!==undefined)e.textContent=t;svg.append(e);return e}const x=v=>86+v/8192*930,y=v=>290-v*218;[0,.25,.5,.75,1].forEach(v=>{el('line',{x1:86,y1:y(v),x2:1016,y2:y(v),stroke:'#e3e7e1'});el('text',{x:66,y:y(v)+6,'text-anchor':'end','font-size':17,fill:'#52625d'},v)});[0,2048,4096,6144,8192].forEach(v=>el('text',{x:x(v),y:322,'text-anchor':'middle','font-size':17,fill:'#52625d'},v));el('text',{x:86,y:32,'font-size':18,fill:'#19332f'},'效率系数 λ（越大，答对后的额外奖励越多）');el('text',{x:1016,y:352,'text-anchor':'end','font-size':17,fill:'#52625d'},'Think 轨迹长度 / token');[['hard','#218b76'],['easy','#bf744b']].forEach(([key,color])=>el('polyline',{points:data.curves.map(p=>`${x(p.tokens)},${y(p[key])}`).join(' '),fill:'none',stroke:color,'stroke-width':4}));el('text',{x:795,y:82,'font-size':19,fill:'#218b76'},'较难：α = 0.18');el('text',{x:795,y:264,'font-size':19,fill:'#aa5f39'},'较易：α = 0.81');document.querySelector('#cases').innerHTML=data.cases.map(c=>`<div class="case ${c.correct?'':'bad'}"><b>${c.label}</b><div>${c.think?'Think':'NoThink'} · ${c.tokens} token</div><strong>r = ${c.reward.toFixed(4)}</strong></div>`).join('');</script></html>'''
(here / 'when2think-chart.html').write_text(template.replace('DATA', json.dumps(result, ensure_ascii=False)))
print(json.dumps({'cases':cases,'status':'executed','chart':'when2think-chart.html'},ensure_ascii=False,indent=2))
