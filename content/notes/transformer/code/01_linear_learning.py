"""第 01 章：复现打印店案例，所有订单和价格均为合成教学数据。

直接运行：python3 code/01_linear_learning.py
修改实验时，调整文件末尾的 samples、learning_rate、steps。
"""

from math import isclose


def predict(x, w, b):
    return w * x + b


def mean_squared_error(samples, w, b):
    return sum((predict(x, w, b) - y) ** 2 for x, y in samples) / len(samples)


def update(samples, w, b, learning_rate):
    # 所有误差和梯度都基于同一组旧参数，最后一起更新。
    errors = [predict(x, w, b) - y for x, y in samples]
    gw = sum(2 * e * x for (x, _), e in zip(samples, errors)) / len(samples)
    gb = sum(2 * e for e in errors) / len(samples)
    return w - learning_rate * gw, b - learning_rate * gb


def demonstrate():
    orders = [(1.0, 2.0), (2.0, 4.0), (3.0, 6.0)]
    print("第 2 节：比较两套估价规则")
    for name, w, b in [("A", 1.0, 0.0), ("B", 1.0, 2.0)]:
        errors = [predict(x, w, b) - y for x, y in orders]
        loss = mean_squared_error(orders, w, b)
        print(f"模型 {name}：误差和={sum(errors):.1f}，均方误差={loss:.6f}")
    assert isclose(mean_squared_error(orders, 1, 0), 14 / 3)
    assert isclose(mean_squared_error(orders, 1, 2), 2 / 3)

    print("\n第 3 节：固定 b=0，轻轻改变 w")
    for w in [0.99, 1.0, 1.01]:
        print(f"w={w:.2f}，预测={predict(2, w, 0):.2f}，损失={(predict(2, w, 0)-4)**2:.4f}")
    approximate_gradient = ((2 * 1.01 - 4) ** 2 - 4) / 0.01
    assert isclose(approximate_gradient, -7.96)
    print(f"向前试探得到的变化率约为 {approximate_gradient:.2f}，精确导数为 -8")

    print("\n第 4 节：每次都从 w=1、b=0 出发，更新一次")
    single_order = [(2.0, 4.0)]
    for rate, expected_loss in [(0.01, 3.24), (0.1, 0.0), (0.3, 16.0)]:
        w, b = update(single_order, 1.0, 0.0, rate)
        loss = mean_squared_error(single_order, w, b)
        print(f"学习率={rate:.2f}，w={w:.2f}，b={b:.2f}，预测={predict(2,w,b):.2f}，损失={loss:.2f}")
        assert isclose(loss, expected_loss, abs_tol=1e-12)
    w, b = update(single_order, 1.0, 0.0, 0.3)
    w, b = update(single_order, w, b, 0.3)
    print(f"学习率 0.30 再更新一次：预测={predict(2,w,b):.1f}，损失={mean_squared_error(single_order,w,b):.1f}")
    assert isclose(predict(2, w, b), -4.0)
    assert isclose(mean_squared_error(single_order, w, b), 64.0)

    w, b = update(single_order, 1.0, 0.0, 0.1)
    print("单张订单学对后，检查其他页数：")
    for x in [1, 2, 3, 4]:
        print(f"页数={x}，预测={predict(x,w,b):.1f}，目标={2*x}")

    print("\n第 5 节：黑白和彩色订单，使用独立的一组价格")
    inputs = [[2, 3], [1, 4]]
    weights, bias = [0.5, 1.0], 0.2
    predictions = [sum(x * w for x, w in zip(row, weights)) + bias for row in inputs]
    print(f"两张订单的预测费用：{predictions}")
    assert all(isclose(actual, expected) for actual, expected in zip(predictions, [4.2, 4.7]))

    print("\n第 6 节：阶梯优惠，费用 = 2x - ReLU(x-2)")
    for x, expected in [(1, 2), (2, 4), (3, 5), (4, 6)]:
        relu = max(0, x - 2)
        fee = 2 * x - relu
        print(f"页数={x}，ReLU(x-2)={relu}，费用={fee}")
        assert fee == expected
    print("\n固定教学案例核对通过。下面开始可修改的训练实验。")


def train(samples, learning_rate, steps):
    w, b = 1.0, 0.0
    print(f"\n共同训练：样本={samples}，学习率={learning_rate}，更新次数={steps}")
    for step in range(steps + 1):
        loss = mean_squared_error(samples, w, b)
        if step % 50 == 0 or step == steps:
            print(f"step={step:3d}，loss={loss:.6f}，w={w:.4f}，b={b:.4f}")
        if step < steps:
            w, b = update(samples, w, b, learning_rate)
    print("训练后逐单检查：")
    for x, y in samples:
        print(f"页数={x:g}，预测={predict(x,w,b):.4f}，目标={y:g}")
    # 改成阶梯优惠实验时，x=4 已包含在训练集中，目标也不再是 8。
    print(f"额外查询 x=4：预测={predict(4,w,b):.4f}（是否见过、目标多少，请按实验数据判断）")


if __name__ == "__main__":
    demonstrate()

    # 第 8 节的三项实验从这里修改，每次只改变一个条件。
    samples = [(1.0, 2.0), (2.0, 4.0), (3.0, 6.0)]
    learning_rate = 0.05
    steps = 200
    train(samples, learning_rate, steps)
