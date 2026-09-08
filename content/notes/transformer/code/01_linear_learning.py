"""第 01 章：纯 Python 线性模型，所有数据均为合成教学数据。"""
x, y, w, b = 2.0, 4.0, 1.0, 0.0
e = w * x + b - y
gw, gb = 2 * e * x, 2 * e
w, b = w - 0.1 * gw, b - 0.1 * gb
print(f"单样本更新：w={w:.1f}, b={b:.1f}, prediction={w*x+b:.1f}")
assert abs(w - 1.8) < 1e-12 and abs(b - 0.4) < 1e-12

samples = [(1.0, 2.0), (2.0, 4.0), (3.0, 6.0)]
w, b = 1.0, 0.0
learning_rate = 0.05
for step in range(201):
    errors = [w * x + b - y for x, y in samples]
    loss = sum(e * e for e in errors) / len(samples)
    if step % 50 == 0:
        print(f"step={step:3d}, loss={loss:.6f}, w={w:.4f}, b={b:.4f}")
    if step == 200:
        break
    gw = sum(2 * e * x for (x, _), e in zip(samples, errors)) / len(samples)
    gb = sum(2 * e for e in errors) / len(samples)
    w, b = w - learning_rate * gw, b - learning_rate * gb
print(f"未参与训练的输入 x=4：prediction={w*4+b:.4f}, target=8")
