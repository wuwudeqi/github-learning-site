"""A two-dimensional geometry check, not a CKDA training reproduction."""
import json
import math
import platform
from pathlib import Path

def mm(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(2)) for j in range(2)] for i in range(2)]

def mv(a, v):
    return [sum(a[i][k] * v[k] for k in range(2)) for i in range(2)]

theta = math.pi / 6
k = [math.cos(theta / 2), math.sin(theta / 2)]
D = [[-1, 0], [0, 1]]
H = [[(1 if i == j else 0) - 2 * k[i] * k[j] for j in range(2)] for i in range(2)]
A = mm(H, D)
R = [[math.cos(theta), -math.sin(theta)], [math.sin(theta), math.cos(theta)]]
matrix_error = max(abs(A[i][j] - R[i][j]) for i in range(2) for j in range(2))
points = [[1.0, 0.0]]
for _ in range(12):
    points.append(mv(A, points[-1]))
norm_error = max(abs(math.hypot(*v) - 1) for v in points)
closure_error = math.dist(points[0], points[-1])
reflection_error = max(abs(mm(H, H)[i][j] - (i == j)) for i in range(2) for j in range(2))
assert max(matrix_error, norm_error, closure_error, reflection_error) < 1e-12
result = dict(python=platform.python_version(), angleDegrees=30, k=k, D=D, H=H, A=A,
              points=points, matrixError=matrix_error, normError=norm_error,
              closureError=closure_error, reflectionError=reflection_error,
              scope="二维线性代数合成例子；不代表训练后的CKDA或长序列泛化结果")
out = Path(__file__).parent
(out / "rotation-results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
(out / "rotation-results.js").write_text("window.rotationData = " + json.dumps(result, ensure_ascii=False) + ";\n")
print(json.dumps(result, ensure_ascii=False, indent=2))
