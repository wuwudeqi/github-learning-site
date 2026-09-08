"""Transformer 02–05 章的数值实验；Python 3.9+，只用标准库。

python3 transformer_lab.py all
python3 transformer_lab.py attention
python3 transformer_lab.py check

两套明确分开的参数：attention 使用二维手算例子；model 使用四维、
单层、单头 Pre-LN Decoder。后者的权重只用于演示数据流，没有预训练。
loss 展示三分类输出层更新；check 还会在四维模型上验证输出层梯度。
"""

import argparse
import math
import random


TOKENS = ["小猫", "饿了", "它", "吃", "鱼", "<结束>"]
EMBEDDINGS = [
    [1.0, 0.0, 0.5, -0.5],
    [0.0, 1.0, -0.5, 0.5],
    [1.0, 1.0, 0.5, 0.5],
    [0.5, -0.5, 1.0, 0.0],
    [-0.5, 0.5, 0.0, 1.0],
    [0.0, 0.0, -0.5, -0.5],
]


def encode(text):
    """仅演示按词表最长匹配；不实现真实 BPE，也不忽略空格等字符。"""
    ids, offset = [], 0
    candidates = sorted(range(len(TOKENS)), key=lambda i: -len(TOKENS[i]))
    while offset < len(text):
        found = next((i for i in candidates if text.startswith(TOKENS[i], offset)), None)
        if found is None:
            raise ValueError(f"教学词表不支持位置 {offset} 的文本：{text[offset:]!r}")
        ids.append(found)
        offset += len(TOKENS[found])
    return ids


def decode(ids):
    return "".join(TOKENS[i] for i in ids)


def dot(a, b):
    if len(a) != len(b):
        raise ValueError("点积的两个向量必须等长")
    return sum(x * y for x, y in zip(a, b))


def linear(row, weights):
    return [dot(row, col) for col in zip(*weights)]


def add(a, b):
    if len(a) != len(b):
        raise ValueError("相加向量必须等长")
    return [x + y for x, y in zip(a, b)]


def softmax(scores):
    maximum = max(scores)
    # 减最大值不改变概率，可以避免 exp(1000) 这样的溢出。
    terms = [math.exp(s - maximum) for s in scores]
    total = sum(terms)
    return [t / total for t in terms]


def cross_entropy(logits, target):
    maximum = max(logits)
    # log-sum-exp 形式，避免先计算很小的概率再取 log。
    return maximum + math.log(sum(math.exp(z - maximum) for z in logits)) - logits[target]


def position_vector(position, width=4):
    result = []
    for pair in range(width // 2):
        angle = position / (10000 ** (2 * pair / width))
        result.extend([math.sin(angle), math.cos(angle)])
    return result


def layer_norm(row, epsilon=1e-5):
    mean = sum(row) / len(row)
    variance = sum((x - mean) ** 2 for x in row) / len(row)
    # 为看清计算，固定可学习缩放 gamma=1、偏移 beta=0。
    return [(x - mean) / math.sqrt(variance + epsilon) for x in row]


def attend(query, keys, values):
    scores = [dot(query, key) / math.sqrt(len(query)) for key in keys]
    weights = softmax(scores)
    mixed = [sum(w * row[c] for w, row in zip(weights, values)) for c in range(len(values[0]))]
    return mixed, weights


def attention_example(causal=True, inputs=None, value_scale=2.0):
    x = inputs if inputs is not None else [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]]
    # Wq=Wk=I；Wv=diag(1, 2)。这里不加位置编码、归一化或残差。
    q, k = x, x
    v = [linear(row, [[1.0, 0.0], [0.0, value_scale]]) for row in x]
    outputs, rows = [], []
    for i, query in enumerate(q):
        end = i + 1 if causal else len(x)
        output, weights = attend(query, k[:end], v[:end])
        outputs.append(output)
        rows.append(weights + [0.0] * (len(x) - end))
    return outputs, rows


class TinyDecoder:
    """单层单头、四维 Pre-LN Decoder，ReLU FFN；无 dropout。"""

    def __init__(self):
        rng = random.Random(7)

        def matrix(rows, cols):
            return [[rng.uniform(-0.5, 0.5) for _ in range(cols)] for _ in range(rows)]

        self.wq, self.wk, self.wv, self.wo = [matrix(4, 4) for _ in range(4)]
        self.w1, self.w2 = matrix(4, 8), matrix(8, 4)
        self.head = matrix(4, len(TOKENS))

    def input_row(self, token, position):
        return add(EMBEDDINGS[token], position_vector(position))

    def finish_block(self, x, attention_output):
        u = add(x, linear(attention_output, self.wo))
        expanded = linear(layer_norm(u), self.w1)
        activated = [max(0.0, value) for value in expanded]
        h = add(u, linear(activated, self.w2))
        return layer_norm(h)

    def forward(self, ids):
        if not ids:
            raise ValueError("至少提供一个输入 Token")
        xs = [self.input_row(token, i) for i, token in enumerate(ids)]
        normalized = [layer_norm(x) for x in xs]
        qs = [linear(x, self.wq) for x in normalized]
        ks = [linear(x, self.wk) for x in normalized]
        vs = [linear(x, self.wv) for x in normalized]
        hidden, logits = [], []
        for i, query in enumerate(qs):
            mixed, _ = attend(query, ks[: i + 1], vs[: i + 1])
            h = self.finish_block(xs[i], mixed)
            hidden.append(h)
            logits.append(linear(h, self.head))
        return hidden, logits

    def step(self, token, cache):
        # 第一个位置为 0；已有 K 的数量就是新 Token 的绝对位置。
        x = self.input_row(token, len(cache["k"]))
        norm = layer_norm(x)
        q, k, v = linear(norm, self.wq), linear(norm, self.wk), linear(norm, self.wv)
        cache["k"].append(k)
        cache["v"].append(v)
        mixed, _ = attend(q, cache["k"], cache["v"])
        return linear(self.finish_block(x, mixed), self.head)


def fmt(row):
    return "[" + ", ".join(f"{x:.6f}" for x in row) + "]"


def demo_input():
    text = "小猫饿了它"
    ids = encode(text)
    print("输入实验：", text, "→", ids, "→", decode(ids))
    for pos, token in enumerate(ids):
        print(TOKENS[token], "E=", fmt(EMBEDDINGS[token]), "P=", fmt(position_vector(pos)))
        print("  X=", fmt(add(EMBEDDINGS[token], position_vector(pos))))


def demo_attention():
    output, weights = attention_example()
    print("二维手算实验：因果注意力矩阵 A")
    for row in weights:
        print(fmt(row))
    print("A @ V：")
    for row in output:
        print(fmt(row))
    unmasked, _ = attention_example(causal=False)
    print("取消遮罩后，第一个位置的输出：", fmt(unmasked[0]))


def demo_model():
    model = TinyDecoder()
    ids = encode("小猫饿了它")
    hidden, logits = model.forward(ids)
    print("四维单层模型：未预训练，输出只演示计算流程")
    print("末尾表示 h：", fmt(hidden[-1]))
    print("词表 logits：", fmt(logits[-1]))
    print("词表概率：", fmt(softmax(logits[-1])))
    cache = {"k": [], "v": []}
    cached_logits = None
    for token in ids:
        cached_logits = model.step(token, cache)
    for step in range(4):
        _, full = model.forward(ids)
        error = max(abs(a - b) for a, b in zip(full[-1], cached_logits))
        token = max(range(len(TOKENS)), key=lambda i: cached_logits[i])
        print(f"生成步 {step + 1}：前缀={decode(ids)!r}，选择={TOKENS[token]}，缓存误差={error:.2e}")
        ids.append(token)
        if token == 5:
            break
        cached_logits = model.step(token, cache)
    print("停止条件：生成 <结束> 或达到 4 个新 Token 的预算。")


def demo_loss():
    h = [1.0, 2.0]
    weights = [[math.log(2), 0.0, 0.0], [0.0, 0.0, 0.0]]
    target, rate = 1, 0.1  # 三个候选为 鱼、猫粮、球；目标是猫粮。
    old = linear(h, weights)
    p = softmax(old)
    dz = [prob - float(j == target) for j, prob in enumerate(p)]
    dw = [[value * gradient for gradient in dz] for value in h]
    new_weights = [[w - rate * g for w, g in zip(row, grad)] for row, grad in zip(weights, dw)]
    new = linear(h, new_weights)
    print("三分类输出层实验：候选 [鱼, 猫粮, 球]，目标=猫粮")
    print("旧 logits：", fmt(old), "旧概率：", fmt(p))
    print("dL/dz：", fmt(dz))
    print("dL/dW：", [fmt(row) for row in dw])
    print("新 logits：", fmt(new), "新概率：", fmt(softmax(new)))
    print(f"损失：{cross_entropy(old, target):.6f} → {cross_entropy(new, target):.6f}")


def verify():
    count = 0

    def check(condition, description):
        nonlocal count
        if not condition:
            raise AssertionError(description)
        count += 1
        print("PASS", description)

    def close(a, b, tolerance=1e-10):
        return len(a) == len(b) and all(abs(x - y) < tolerance for x, y in zip(a, b))

    check(decode(encode("小猫饿了它吃鱼<结束>")) == "小猫饿了它吃鱼<结束>", "词表编码与解码往返")
    check(close(softmax([1000, 1001]), softmax([0, 1])), "Softmax 平移不变且大分数不溢出")
    out, a = attention_example()
    r = math.exp(1 / math.sqrt(2))
    expected = [1 / (2 + r), 1 / (2 + r), r / (2 + r)]
    check(close(a[-1], expected), "第三行权重与独立手算公式相符")
    check(close(out[-1], [1 - expected[1], 2 * (1 - expected[0])]), "加权结果与手算相符")
    check(all(abs(sum(row) - 1) < 1e-12 for row in a), "每行注意力权重之和为 1")
    check(all(a[i][j] == 0 for i in range(3) for j in range(i + 1, 3)), "未来位置权重严格为 0")
    changed = [[1.0, 0.0], [0.0, 1.0], [20.0, -20.0]]
    masked, _ = attention_example(inputs=changed)
    check(close(masked[0], out[0]) and close(masked[1], out[1]), "改动未来输入不影响过去的输出")
    plain_before, _ = attention_example(causal=False)
    plain_after, _ = attention_example(causal=False, inputs=changed)
    check(not close(plain_before[0], plain_after[0]), "取消遮罩后，未来输入确实能影响过去")
    other, other_a = attention_example(value_scale=4)
    check(all(close(x, y) for x, y in zip(a, other_a)) and not close(other[-1], out[-1]), "只改 V 会改变输出，不改变权重")

    model = TinyDecoder()
    ids = [0, 1, 2, 3, 4]
    _, full = model.forward(ids)
    cache = {"k": [], "v": []}
    cached = [model.step(token, cache) for token in ids]
    check(all(close(x, y) for x, y in zip(full, cached)), "带位置编码、残差和 FFN 的整层缓存结果等于重算")
    _, altered = model.forward([0, 1, 4, 5, 2])
    check(all(close(full[i], altered[i]) for i in (0, 1)), "整层网络保持因果性")
    check(len(cache["k"]) == len(ids) == len(cache["v"]), "缓存每个位置保存一对 K/V")

    # 固定前面的网络，只检查输出层；数值差分不调用解析求导公式。
    hidden, logits = model.forward([0, 1, 2])
    h, target, epsilon = hidden[-1], 3, 1e-6
    p = softmax(logits[-1])
    gradients = [[value * (p[j] - float(j == target)) for j in range(6)] for value in h]
    max_error = 0.0
    for i in range(4):
        for j in range(6):
            original = model.head[i][j]
            model.head[i][j] = original + epsilon
            plus = cross_entropy(linear(h, model.head), target)
            model.head[i][j] = original - epsilon
            minus = cross_entropy(linear(h, model.head), target)
            model.head[i][j] = original
            max_error = max(max_error, abs((plus - minus) / (2 * epsilon) - gradients[i][j]))
    check(max_error < 1e-7, f"输出层 24 个梯度通过中心差分核对（最大误差 {max_error:.2e}）")
    before = cross_entropy(logits[-1], target)
    for i in range(4):
        for j in range(6):
            model.head[i][j] -= 0.1 * gradients[i][j]
    after = cross_entropy(linear(h, model.head), target)
    check(after < before, "此样本上的一次输出层更新降低损失")
    print(f"共 {count} 项机制检查通过。它们不评估真实语言模型的回答质量。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("experiment", nargs="?", default="all", choices=["all", "input", "attention", "model", "loss", "check"])
    args = parser.parse_args()
    demos = {"input": demo_input, "attention": demo_attention, "model": demo_model, "loss": demo_loss, "check": verify}
    if args.experiment == "all":
        for demo in demos.values():
            demo()
            print()
    else:
        demos[args.experiment]()
