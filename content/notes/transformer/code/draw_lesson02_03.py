"""Exact diagrams for lessons 02 and 03, sharing values with the toy lab."""
from pathlib import Path
from html import escape
from lesson02_03_lab import train, E, CORPUS
OUT=Path(__file__).resolve().parent.parent/'images'
INK='#163748';MUTED='#526878';BLUE='#176f8a';GOLD='#a65d19'
COLORS=['#dceef7','#f9e9ce','#e2f0df']
def text(x,y,s,size=24,color=INK):return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}">{escape(str(s))}</text>'
def rect(x,y,w,h,fill='#edf3f6'):return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="7" fill="{fill}"/>'
def arrow(x,y,xx,yy):return f'<path d="M{x},{y} L{xx},{yy}" stroke="{BLUE}" stroke-width="2.5" fill="none" marker-end="url(#a)"/>'
def box(x,y,w,title,lines,fill='#edf3f6'):
 h=65+len(lines)*33;return rect(x,y,w,h,fill)+text(x+18,y+33,title,26)+''.join(text(x+18,y+69+i*33,s,22,MUTED) for i,s in enumerate(lines))
def tokens(x,y,items,marked=()):
 s=''
 for i,item in enumerate(items):
  w=max(62,22*len(item)+24);s+=rect(x,y,w,44,'#f9e9ce' if i in marked else '#e4f0f5')+text(x+12,y+30,item,25);x+=w+9
 return s

def save(name,title,subtitle,b,h=700):
 s=f'<svg xmlns="http://www.w3.org/2000/svg" width="920" height="{h}" viewBox="0 0 920 {h}" role="img" aria-labelledby="title desc"><title id="title">{escape(title)}</title><desc id="desc">{escape(subtitle)}</desc><defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10" fill="{BLUE}"/></marker></defs><rect width="920" height="{h}" fill="#fbfcfd"/><g font-family="PingFang SC, Microsoft YaHei, sans-serif">'+text(28,48,title,30)+text(28,89,subtitle,22,MUTED)+b+'</g></svg>'
 (OUT/name).write_text(s)

def main():
 vocab,rules,trace=train()
 b=box(28,122,390,'准备分词器：统计语料',['low×5 / lower×2 / new×6','字符起步 → 反复统计相邻片段','得到固定词表和有先后顺序的规则'])
 b+=arrow(431,209,485,209)+box(499,122,393,'使用分词器：编码新文本',['输入 newer','应用已保存的合并规则','new | e | r → [9,0,4]'])
 b+=box(28,341,864,'固定词表（本例从 0 开始编号）',['0:e   1:l   2:n   3:o   4:r   5:w','6:lo   7:low   8:ne   9:new'])
 b+=box(28,522,864,'编码结果的去向',['token ID → 用于查 Embedding 表 → 模型计算','解码时按同一份词表将 ID 还原；实际还需配套解码规则。'],'#fff2de')
 save('l02-01-tokenizer-lifecycle.svg','分词器先准备规则，再拿规则编码','分词器训练与语言模型的参数训练，是不同步骤。',b,695)
 b=text(28,139,'词频会计入每一对相邻片段的次数。',24)
 headers=['片段对','来自 low×5','来自 lower×2','来自 new×6','总次数']
 xs=[28,196,365,554,754]
 for x,s in zip(xs,headers):b+=text(x,188,s,22)
 pairs=[('l','o'),('o','w'),('w','e'),('e','r'),('n','e'),('e','w')]
 for i,pair in enumerate(pairs):
  y=211+i*53;b+=rect(24,y,868,46,'#f9e9ce' if i==0 else ('#edf3f6' if i%2==0 else '#f7f9fb'))
  nums=[]
  for word,n in CORPUS.items():nums.append(sum(tuple(pair)==p for p in zip(word,word[1:]))*n)
  for x,s in zip(xs,[str(pair),*nums,sum(nums)]):b+=text(x+5,y+31,s,23)
 b+=text(28,570,'l+o 与 o+w 都是 7；本例先选 l+o。',25)
 b+=text(28,614,'并列时按语料扫描的首次出现顺序；不是所有实现都如此。',21,MUTED)
 save('l02-02-pair-counts.svg','第 1 次统计：为什么先合并 l + o？','相邻指同一个词内的相邻片段；本例不跨词边界合并。',b,652)
 b=''
 for i,r in enumerate(trace):
  y=120+i*180;b+=rect(24,y,872,162,'#f1f5f7')
  b+=text(40,y+32,f"第 {i+1} 轮：{' + '.join(r['pair'])} → {''.join(r['pair'])}",25)
  b+=text(640,y+32,f"频数 {r['frequency']}；新增 ID {6+i}",21,GOLD)
  for j,w in enumerate(CORPUS):
   yy=y+45+j*36;b+=text(42,yy+24,f'{w} ×{CORPUS[w]}',22)
   b+=text(215,yy+24,' | '.join(r['before'][w]),23)+arrow(425,yy+17,463,yy+17)+text(490,yy+24,' | '.join(r['after'][w]),23)
 b+=text(28,884,'加权 token 总数：43 → 36 → 29 → 23 → 17',26)
 b+=text(28,925,'每轮都重算相邻片段；后来的片段可以由多字符组成。',22,MUTED)
 save('l02-03-merge-trace.svg','BPE 的四次合并：每一步改变下一次统计','语料只有 low×5、lower×2、new×6；字符和规则均为教学设定。',b,965)
 b=text(28,139,'未在训练词表中出现的完整单词：newer',25)
 rows=[('初始字符',['n','e','w','e','r']),('规则 1、2 无匹配',['n','e','w','e','r']),('规则 3：n+e → ne',['ne','w','e','r']),('规则 4：ne+w → new',['new','e','r'])]
 for i,(label,parts) in enumerate(rows):
  y=173+i*90;b+=text(28,y+29,label,22)+tokens(351,y,parts,((0,) if i>=2 else ()))
 b+=box(28,552,864,'查词表并解码核对',['new → 9；e → 0；r → 4；输出 ID=[9,0,4]','反向查表并拼接：new + e + r = newer'])
 b+=text(28,733,'词表和规则保持不变；不会为这一条输入重新统计词频。',22,MUTED)
 save('l02-04-encode-newer.svg','使用阶段：按已有规则处理新词','“没有整词条目”不等于“无法编码”；关键看基础片段能否覆盖。',b,775)
 b=box(28,122,864,'真实管线可能包含这些环节',['原文 → 规范化（可选）→ 预切分 → 子词算法 → 特殊 token → ID'])
 b+=text(28,280,'字符、字节和 token，是不同的计数单位。',26)
 b+=tokens(28,318,['中'])+arrow(124,340,224,340)+tokens(244,318,['E4','B8','AD'])+text(244,391,'UTF-8：三个字节（十六进制）',24)
 b+=box(28,426,864,'byte-level BPE 的起点',['基础符号覆盖 256 个字节值，再学习合并字节片段。','一个 token 的字节不一定独立构成完整 Unicode 字符。'])
 b+=box(28,606,864,'排查实践',['先看完整 encode/decode，再看单个 token；不要逐块强行解码。','如果规范化改了原文，解码未必恢复原始大小写或空格。'],'#fff2de')
 save('l02-05-bytes-boundaries.svg','中文为什么不能按“一个字一个 token”估算','本课的字符 BPE 简化了这些环节；实际实现要检查配置。',b,780)
 b=box(28,122,410,'词表大小 V',['有多少种可用 token','影响嵌入表 E 的行数','不是当前输入的长度'])
 b+=box(482,122,410,'序列长度 T',['这条输入编码后有几项','影响当前位置数量','同一词表下，不同输入的 T 不同'])
 b+=text(28,348,'本例：6 个基础片段 + 4 个合并片段 → V=10',25)
 b+=text(28,396,'lower → [7,0,4] → T=3；new → [9] → T=1',25)
 b+=box(28,446,864,'词表扩大的成本与收益',['Embedding 参数个数 = V × d（每项 token 存 d 个数）','更多合并可能缩短输入，但会扩大词表相关的参数与输出。','语义是否有用，仍需要模型训练；BPE 主要依据片段频次。'],'#fff2de')
 save('l02-06-vocab-length.svg','V 与 T：两种“大小”怎样影响模型','d 在第 3 课解释；这里先理解为每行保存的数字个数。',b,665)
 # Embedding lookup: the full ten-row table and reordered output.
 b=text(28,139,'lower → [low, e, r] → ID=[7,0,4]',26)
 b+=text(28,185,'词表 / 嵌入表 E：10 行 × 3 列',24)+text(550,185,'按输入顺序取出：X',24)
 selected={7:0,0:1,4:2}
 for i,(tok,row) in enumerate(zip(vocab,E)):
  y=207+i*42;b+=rect(24,y,466,36,COLORS[selected[i]] if i in selected else '#f0f3f6')
  b+=text(36,y+26,f'{i:>2}   {tok:<4}',22)
  for j,v in enumerate(row):b+=text(205+j*88,y+26,f'{v:.1f}',22)
 for outidx,idx in enumerate([7,0,4]):
  y=234+outidx*131;b+=rect(548,y,344,85,COLORS[outidx])+text(568,y+31,f'第 {outidx+1} 个位置 ← E[{idx}]',22)+text(568,y+66,str(E[idx]),23)
  source_y=207+idx*42+18
  b+=f'<path d="M493,{source_y} C520,{source_y} 521,{y+42} 541,{y+42}" stroke="{BLUE}" stroke-width="2" fill="none" marker-end="url(#a)"/>'
 b+=text(28,684,'输入顺序是 7、0、4，所以输出顺序也按 7、0、4。',24)
 save('l03-01-lookup.svg','Embedding 的一次前向：编号决定取哪一行','表中数字全部手工指定；不是训练所得的语义坐标。',b,729)
 # Matrix selector with one-hot 3x10.
 b=text(28,137,'S：用 0 和 1 表示“取哪一行”',25)
 for j in range(10):b+=text(169+j*60,180,j,20,MUTED)
 for i,idx in enumerate([7,0,4]):
  y=199+i*60;b+=text(28,y+33,f'ID {idx}',23)
  for j in range(10):b+=rect(150+j*60,y,52,45,COLORS[i] if j==idx else '#edf1f4')+text(168+j*60,y+31,int(j==idx),23)
 b+=text(28,422,'S 的形状：3×10；E 的形状：10×3',26)
 b+=text(28,472,'X = S E，形状：(3×10) × (10×3) = 3×3',26)
 b+=box(28,516,864,'把第 1 行、第 2 列展开',['X[0,1] = 0×E[0,1] + … + 1×E[7,1] + … + 0×E[9,1]','          = E[7,1] = 0.1','中间的 10 对齐；每行只有一个 1，留下的正是选中那行。'],'#fff2de')
 save('l03-02-onehot.svg','查表与矩阵乘法，为什么结果相同？','本图索引从 0 开始；“第 1 行”对应矩阵下标 0。',b,725)
 b=text(28,138,'ID 7 的向量：[0.8, 0.1, −0.2]',27)
 for j,v in enumerate(E[7]):
  x=180+j*195;b+=rect(x,192,162,90,COLORS[j])+text(x+20,226,f'第 {j+1} 个分量',23)+text(x+53,265,v,28)
 b+=text(28,334,'向量：一串有顺序的数；维度 d：这串数有多长。',25)
 b+=box(28,375,864,'把多行向量叠起来，得到矩阵',['T 个 token → T 行；每行 d 个数 → d 列。','本例 T=3、d=3，只是巧合，两者含义不同。'])
 b+=box(28,555,864,'不要提前替每一维命名',['不能据此说第 1 维是“冷”，第 2 维是“热”。','真实向量的用途由训练与后续计算共同决定。'],'#fff2de')
 save('l03-03-vector-shape.svg','向量与维度：先数清楚，再谈含义','表里的 0.8 与词表编号 7 是不同类型的信息。',b,720)
 b=box(28,122,864,'输入同一个 token 两次：ID=[7,0,7]',['输出第 1 行与第 3 行都来自 E[7]，查表值相同。'])
 b+=box(40,280,240,'位置 1 → E[7]',[])+box(340,280,240,'位置 2 → E[0]',[])+box(640,280,252,'位置 3 → E[7]',[])
 b+=text(305,399,'E[7]：共享的一行参数',24)+arrow(410,365,164,346)+arrow(515,365,758,346)
 b+=box(28,432,864,'训练时，这一行收到来自不同位置的调整信号',['位置 1 给：[1,0,0]；位置 3 给：[3,0,1]','汇总到 E[7]：[4,0,1]（只展示梯度累加，不是直接加到参数）'])
 b+=text(28,633,'后续模型处理位置和前文后，这两个位置的表示可以不同。',23)
 save('l03-04-shared-row.svg','同一行参数可以被多次使用','查表阶段相同，不代表经过整层网络后仍相同。',b,678)
 b=box(28,122,390,'原来的编号',['low → ID 7 → [0.8,0.1,−0.2]','e   → ID 0 → [0.1,0.2,0.3]'])
 b+=arrow(434,197,483,197)+box(499,122,393,'同步重排后',['low → 新 ID 2 → 同一组数','e   → 新 ID 9 → 同一组数'])
 b+=box(28,339,864,'真正需要保持一致的是映射关系',['若同步重排词表和 E 的行，查表结果保持不变。','若只换 tokenizer，不同步模型映射，就会取错行。'])
 b+=box(28,519,864,'关联：输入向量与检索向量',['一个 token 的输入向量，不等于一整篇文档的检索向量。','直接平均这些行虽然能得到一个向量，却不保证适合语义检索。'],'#fff2de')
 save('l03-05-mapping-invariance.svg','编号可重排，匹配关系不能错','用这个思路解释“为什么 ID 相邻不能推出语义相近”。',b,700)
 print('11 exact diagrams generated (6 for lesson 02, 5 for lesson 03).')
if __name__=='__main__':main()
