"""Generate the introductory lesson's small, single-purpose SVG diagrams."""
from pathlib import Path
from html import escape
OUT=Path(__file__).resolve().parent.parent/'images'
BLUE='#176d86'; INK='#153642'; MUTED='#526672'
def t(x,y,s,size=26,color=INK):return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}">{escape(s)}</text>'
def box(x,y,w,h,title,detail=None,fill='#e9f3f5'):
 s=f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{fill}"/>'+t(x+18,y+36,title)
 if detail:s+=t(x+18,y+72,detail,23,MUTED)
 return s
def arrow(x,y,xx,yy):return f'<path d="M{x},{y} L{xx},{yy}" stroke="{BLUE}" stroke-width="2.5" fill="none" marker-end="url(#a)"/>'
def save(name,title,desc,b,h):
 s=f'<svg xmlns="http://www.w3.org/2000/svg" width="720" height="{h}" viewBox="0 0 720 {h}" role="img" aria-labelledby="title desc"><title id="title">{escape(title)}</title><desc id="desc">{escape(desc)}</desc><defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10" fill="{BLUE}"/></marker></defs><rect width="720" height="{h}" fill="#fbfcfd"/><g font-family="PingFang SC, Microsoft YaHei, sans-serif">'+t(28,48,title,30)+t(28,88,desc,23,MUTED)+b+'</g></svg>'
 (OUT/name).write_text(s)
def main():
 b=box(28,120,664,90,'已有文字','天气很热，我想喝一杯')+arrow(350,218,350,250)
 b+=box(28,260,664,94,'模型计算下一小块的候选','可能是“冰水”，也可能是“热茶”等。')+arrow(350,362,350,394)
 b+=box(28,404,664,90,'生成程序选一个，再接回前文','这一轮假设选中“冰水”。',fill='#fff0d8')
 b+=t(28,549,'下一轮的前文：天气很热，我想喝一杯冰水',25)
 save('intro-01-overview.svg','一次生成：先算候选，再选一项','先看清每一步的工作，再逐步拆开模型内部。',b,590)
 b=t(28,141,'原文：今天很热。',28)
 for i,s in enumerate(['今天','很','热','。']):b+=box(28+i*173,181,145,64,s)
 b+=t(28,294,'上面每个框，暂时看作一个 token。',26)
 b+=box(28,327,664,112,'一个 token 可以不止一个字','具体切法取决于分词器。')
 b+=t(28,480,'这是教学切分，不是某个实际模型的输出。',23,MUTED)
 save('intro-02-token.svg','token：模型处理的文字小块','先认识单位，下一课再学怎么切分。',b,520)
 b=t(28,135,'前文：天气很热，我想喝一杯',26)
 for i,(label,p) in enumerate([('冰水',.6),('热茶',.3),('果汁',.1)]):
  y=176+i*88;b+=t(28,y+28,label,26)+f'<rect x="130" y="{y}" width="450" height="35" fill="#e7ecef"/><rect x="130" y="{y}" width="{450*p}" height="35" fill="{BLUE}"/>'+t(609,y+28,str(int(p*100))+'%',25)
 b+=t(28,461,'60% + 30% + 10% = 100%',28)
 b+=t(28,512,'候选概率是教学假设；只考虑这三个候选。',23,MUTED)
 b+=t(28,552,'概率最高的候选，也不一定每次都被选中。',23)
 save('intro-03-probabilities.svg','候选有多种，每种分到一个概率','这里用一个只有三项的教学词表。',b,590)
 b=box(28,122,664,96,'第一轮：接出“冰水”','天气很热，我想喝一杯 → 冰水')+arrow(350,226,350,258)
 b+=box(28,268,664,96,'第二轮：接出句号','天气很热，我想喝一杯冰水 → 。')+arrow(350,372,350,404)
 b+=box(28,414,664,96,'第三轮：继续写，或结束','程序按结束标记、长度限制等条件停止。')
 b+=t(28,558,'每一轮，都把已经选出的内容算进前文。',25)
 save('intro-04-loop.svg','自回归：自己写过的，也算前文','假设“冰水”是一个 token；各步选择仅作示意。',b,600)
 b=box(28,122,664,133,'训练：边练习，边调整内部的数值','看文本 → 预测 → 比较目标 → 调整参数')
 b+=box(28,288,664,133,'生成：用已经学到的数值计算','读前文 → 算候选 → 选一个 → 接回前文')
 b+=t(28,478,'“参数”就是模型里通过训练调整的数值。',25)
 b+=t(28,525,'通常的聊天生成，不会边回答边更新参数。',24)
 save('intro-05-training.svg','训练与生成，差在是否调整参数','知道两者的分工，就能避免把上下文当作训练。',b,570)
 b=''
 for i,(title,detail) in enumerate([('文字怎么进入计算？','第 2～4 课：分词、向量和矩阵。'),('前文怎样影响下一项？','第 5～14 课：注意力与 Transformer。'),('算出的数怎样变成文字？','第 15～16 课：候选分数、选择和生成。'),('这些计算方法怎样学来？','第 17～20 课：训练、误差和参数更新。')]):
  y=122+i*126;b+=box(28,y,664,97,title,detail)
  if i<3:b+=arrow(350,y+102,350,y+122)
 b+=t(28,666,'每个问题先有直觉，再加入公式和代码。',24)
 save('intro-06-connections.svg','这一课留下的问题，后面逐个回答','先建立全貌，数学推导按依赖顺序展开。',b,705)
 print('Six introductory figures generated.')
if __name__=='__main__':main()
