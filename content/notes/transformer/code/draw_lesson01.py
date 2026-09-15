"""Regenerate exact lecture diagrams. No external dependencies."""
from pathlib import Path
from html import escape
OUT=Path(__file__).resolve().parent.parent/'images'
INK='#173747'; BLUE='#147d99'; ORANGE='#a76018'; MUTED='#526574'
def t(x,y,s,size=24,color=INK):return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}">{escape(s)}</text>'
def box(x,y,w,h,title,lines,fill='#e9f3f7'):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{fill}"/>'+t(x+20,y+35,title,25)+''.join(t(x+20,y+73+34*i,s,21) for i,s in enumerate(lines))
def arrow(x,y,xx,yy):return f'<path d="M{x},{y} L{xx},{yy}" stroke="{BLUE}" stroke-width="2.5" fill="none" marker-end="url(#a)"/>'
def save(file,title,desc,body,h=700):
    s=f'<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="{h}" viewBox="0 0 1000 {h}" role="img" aria-labelledby="title desc"><title id="title">{escape(title)}</title><desc id="desc">{escape(desc)}</desc><defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10" fill="{BLUE}"/></marker></defs><rect width="1000" height="{h}" fill="#fafbfd"/><g font-family="PingFang SC, Microsoft YaHei, sans-serif">'+t(32,52,title,30)+t(32,91,desc,21,MUTED)+body+'</g></svg>'
    (OUT/file).write_text(s)

def main():
    b=box(32,124,936,132,'条件概率的链式分解',['pθ(y₁,y₂,y₃ | C) = pθ(y₁|C) · pθ(y₂|C,y₁) · pθ(y₃|C,y₁,y₂)', '每一项仍可依赖全部可见前文；没有假设 token 相互独立。'])
    b+=box(32,282,448,168,'分解：要拟合什么',['定义联合概率如何拆成条件概率。','RNN、Transformer 都可参数化这些项。','它不是一种指定的网络层。'])
    b+=box(520,282,448,168,'参数化：用什么计算',['h = fθ(C)，z = hW + b','pθ = softmax(z)','同一 θ 可以处理不同长度的前缀。'])
    b+=box(32,478,936,156,'整条路径与局部贪心',['A: 0.6 × 0.1 = 0.06；B: 0.4 × 0.9 = 0.36','第一步贪心选 A，却错过更高的两步路径 B。','后续概率不同，逐步最大化不保证整条序列概率最大。'],'#fff2df')
    save('02-factorization.svg','自回归：概率分解与网络结构分开看','路径示例只比较两步；数值为教学设定。',b,670)

    b=box(32,125,936,132,'行向量约定：每行对应一个位置',['X ∈ R^(T×d)；Q=XWQ，K=XWK，V=XWV','QKᵀ ∈ R^(T×T)；A=softmax_rows(QKᵀ/√dₖ + M)'])
    b+=box(32,284,448,220,'因果依赖矩阵 M',['        来源位置  1     2     3','查询 1               0    −∞    −∞','查询 2               0      0    −∞','查询 3               0      0      0'])
    b+=box(520,284,448,220,'可核算的两位置例子',['X=Q=K=V=[[1,0],[0,1]]','A₁=[1,0]','A₂≈[0.330238,0.669762]','(AV)₂≈[0.330238,0.669762]'])
    b+=box(32,532,936,132,'为什么只用最后位置预测新 token？',['因果约束下，hᵢ 只能利用 x₁…xᵢ；hT 对应整个当前前缀。','遮罩限制依赖；位置编码表达顺序，两者承担不同任务。'],'#fff2df')
    save('03-causal-representation.svg','前文怎样进入最后位置的表示','例子只包含单头注意力；不含位置编码、残差、归一化或 MLP。',b,695)

    b=box(32,124,448,175,'共享输出矩阵',['W = [[ln6, ln3, 0],','         [0,    ln8, 0]] ∈ R^(2×3)','h₁=[1,0]；h₂=[0,1]；b=0'])
    b+=box(520,124,448,175,'同一参数，不同分布',['p₁=[0.6,0.3,0.1]','p₂=[0.1,0.8,0.1]','顺序：冰水 / 热茶 / 果汁'])
    b+=box(32,326,936,163,'几何联系：对数概率比等于线性分数差',['log(pᵢ/pⱼ) = zᵢ − zⱼ = h·(wᵢ − wⱼ) + (bᵢ − bⱼ)','对 h₁：log(p冰水/p热茶)=ln6−ln3=ln2。','softmax 的公共分母抵消；方向 wᵢ−wⱼ 决定两候选相对偏好。'])
    b+=box(32,516,936,145,'可辨识性与结构约束',['softmax(z+c·1)=softmax(z)：绝对分数零点不可辨识。','z=hW+b；多个上下文的 Z−1b=HW，其秩不超过 d。'],'#fff2df')
    save('04-output-geometry.svg','输出层：多分类逻辑回归与表示几何','这是输出头的完整算例；h 为指定值，不声称已算出完整 Transformer。',b,695)

    b=box(32,124,936,134,'从最大似然到单位置损失',['maxθ ∏ pθ(target|prefix)  ⇔  minθ −Σ log pθ(target|prefix)','对目标 k：L=−log pₖ=−zₖ+log Σⱼ exp(zⱼ)'])
    b+=box(32,282,448,185,'对 logits 求导',['∂L/∂zⱼ = pⱼ − 1[j=k]','目标 k=冰水，p=[.6,.3,.1]','g=[−.4,.3,.1]','L=−ln(.6)≈0.510826'])
    b+=box(520,282,448,185,'沿线性层反传',['∂L/∂W = hᵀg','∂L/∂h = gWᵀ','h=[1,0] 时：','∂L/∂W=[[-.4,.3,.1],[0,0,0]]'])
    b+=box(32,497,936,164,'只更新 W 一步，学习率 η=0.1，保持 h 不变',['W′=W−η·∂L/∂W','p′≈[0.615485,0.286937,0.097578]；L′≈0.485345','有限差分检查 W 和 h 的梯度，误差应小于 10⁻⁷。'],'#fff2df')
    save('05-likelihood-gradient.svg','损失怎样改变下一 token 的概率','前向计算 → 损失 → 链式法则 → 参数更新。',b,695)

    b=box(32,124,448,223,'训练：真实前缀已知',['输入：x₁  x₂  x₃','目标：x₂  x₃  x₄','遮罩保证位置 i 不看 xᵢ₊₁。','各位置损失可一次前向计算。','通常更新 θ；使用 teacher forcing。'])
    b+=box(520,124,448,223,'生成：后续输入尚未选定',['prefill：计算已知前缀。','decode：选 y₁，再算 y₂…','通常固定 θ，追加 K/V 缓存。','缓存的是层内键和值。','增加缓存不等于训练参数。'])
    b+=box(32,376,936,145,'K/V 存储量（仅 K、V 张量）',['字节数 = 2 × L × B × T × n_kv × d_head × s','L=32，B=1，T=4096，n_kv=8，d_head=128，s=2','结果：536,870,912 bytes = 512 MiB'])
    b+=box(32,548,936,114,'复杂度取舍',['单层完整注意力约 O(T²d)；缓存后的单步注意力约 O(Td)。','这些只计注意力乘法，不包括投影、MLP、模型权重和运行时开销。'],'#fff2df')
    save('06-train-decode-cache.svg','训练的并行与生成的顺序依赖','分清参数 θ、当前激活和 KV cache 的生命周期。',b,695)

    b=box(32,124,448,206,'分布不确定性',['H(p)=−Σ pᵢ ln pᵢ，单位 nats','p₁=[.6,.3,.1]：H≈0.897946','p₂=[.1,.8,.1]：H≈0.639032','熵低说明集中，不证明事实正确。'])
    b+=box(520,124,448,206,'温度改变采样分布',['qτ(i) ∝ exp(zᵢ/τ) ∝ pᵢ^(1/τ)','τ=.5：q∝[.36,.09,.01]','q≈[.782609,.195652,.021739]','模型参数 θ 不随温度调整。'])
    b+=box(32,358,936,135,'从拟合分布到知识联系',['H(p*,pθ)=H(p*)+D_KL(p*‖pθ)','真实条件分布 p* 固定时，最小化交叉熵等价于最小化 KL。'])
    b+=box(32,521,936,142,'Agent 的评估需要再跨一步',['token 似然 → 输出合法性 → 工具执行 → 任务成功','schema 约束缩小候选集合；事实核验与工具结果检验仍要单独做。'],'#fff2df')
    save('07-entropy-decoding.svg','概率、信息量与任务正确性','同一组 logits 可以配不同解码策略；评估必须说明使用哪种分布。',b,695)
    print('Six graduate-level diagrams regenerated.')
if __name__=='__main__':main()
