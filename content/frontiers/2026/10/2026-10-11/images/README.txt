2026-10-11 前沿：配图来源与使用范围
来源图未裁切、未重画、未改动数据。原尺寸文件与许可随文保存。
Qwen两幅仅用于非商业学习、研究评价；适用Qwen研究许可及Notice。
Youtu结构图来自官方模型卡，适用自定义许可并保留欧盟地域限制；不代表不受限开源。
Iris、EMA、Voxtral模型卡标注Apache-2.0，完整许可附于licenses/Apache-2.0.txt。
四篇论文图作者名单与版本见正文，CC BY 4.0：https://creativecommons.org/licenses/by/4.0/
项目界面/图按各原仓库MIT或Apache-2.0；版权与NOTICE见licenses/。
Managed Agents为AI生成概念示意，提示词与采用输出路径见prompts.txt。
实践矩阵由本机Python结果生成，HTML与JSON在../code/，非论文复现。

qwen-input.png
source-original
先看输入：四张参考图分别提供对象或空间条件，并非四个独立生成结果。图来自Qwen团队模型卡，完整引用该示例，未修改；按研究许可用于本期非商业学习评议，许可与署名见本期配图说明（[来源原图](https://huggingface.co/Qwen/Qwen-Image-2.1-Turbo)；[查看原尺寸](images/qwen-input.png)。）
原始来源/数据：https://huggingface.co/Qwen/Qwen-Image-2.1-Turbo/resolve/main/assets/turbo-interior-input-grid.png
SHA256：dcfd59fe3eacdabab99d5a077e0c6a149a8634261f40d0e9a035fc5cf5f17612

qwen-output.png
source-original
再看输出：家具被放进房间，读图重点是跨参考图的对象组合及布局，不是对尺寸正确性的保证。Qwen官方演示原图，未裁切、未在本站复现；与上一张配对阅读（[来源原图](https://huggingface.co/Qwen/Qwen-Image-2.1-Turbo)；[查看原尺寸](images/qwen-output.png)。）
原始来源/数据：https://huggingface.co/Qwen/Qwen-Image-2.1-Turbo/resolve/main/assets/turbo-interior.png
SHA256：90d37b3880d179caa158a0273dd61756f567c5ca16144f61fd08cca2e608da49

managed-workflow-concept.png
imagegen
从中间的协调台读向三个工作位，再看共同的预算和汇总区：分工可以变化，预算和结果仍需统一管理。AI生成的概念示意，非官方界面；三个角色只是例子，不代表固定数量，也不代表系统自动保证安全（[事实依据：官方编排文档](https://platform.claude.com/docs/en/managed-agents/multiagent-orchestration)；[查看原尺寸](images/managed-workflow-concept.png)。）
原始来源/数据：https://platform.claude.com/docs/en/release-notes/overview
SHA256：913416096fbc2cb0407abea7a23fb68e54eb9a2e423e64625251d15d0ad01c6f

iris-photo.webp
source-original
先看输入中的近处柱子、沙发与远处墙面。Sperid Labs官方模型卡原图，Apache-2.0，完整引用单个演示输入，未修改（[来源原图](https://huggingface.co/speridlabs/iris-3b)；[查看原尺寸](images/iris-photo.webp)。）
原始来源/数据：https://huggingface.co/speridlabs/iris-3b/resolve/main/assets/downstream/depth-1-photo.webp
SHA256：d1c2ef980ed858ae2ae1f11ac1ba4b9cb26b9105da2251321df135c4cf9e36aa

iris-depth.webp
source-original
与上图对照物体边界和前后层次；颜色不是以米计的测量结果，也没有真实深度误差标尺。Sperid Labs官方演示输出原图，Apache-2.0，本站未复现（[来源原图](https://huggingface.co/speridlabs/iris-3b)；[查看原尺寸](images/iris-depth.webp)。）
原始来源/数据：https://huggingface.co/speridlabs/iris-3b/resolve/main/assets/downstream/depth-1-depth.webp
SHA256：03bce4a42d18bf637b3bbbf8eee933778738e5e0282d6061be2b8fb38ce3cf1c

youtu-architecture.png
source-original
读下半图：视觉与音频先经过各自输入层，再在共享编码器中交互；最右侧输出是结构化JSON。上半图是对照的双塔方式。腾讯官方架构原图，完整保留；许可全文及署名随本期保存（[来源原图](https://huggingface.co/tencent/Youtu-Parsing-Omni)；[查看原尺寸](images/youtu-architecture.png)。）
原始来源/数据：https://huggingface.co/tencent/Youtu-Parsing-Omni/resolve/main/assets/arch_figure.png
SHA256：3b07e4e480c3e3fe024dddec508aa8fedad32385983c2fa9107b8bce52583792

voxtral-delay.png
source-original
先看橙线：从80到480毫秒，平均CER从10.64%降到8.82%，继续到720毫秒为8.80%。这展示等待与准确率的取舍，不是本机测速。Mistral官方图，Apache-2.0；七项评估的具体条件见模型卡，未改坐标或图例（[来源原图](https://huggingface.co/mistralai/Voxtral-Mini-4B-Realtime-Arabic)；[查看原尺寸](images/voxtral-delay.png)。）
原始来源/数据：https://huggingface.co/mistralai/Voxtral-Mini-4B-Realtime-Arabic/resolve/main/assets/avg_evals_by_delay.png
SHA256：d5b5d794266ebe7dca3224f1d77f4382984ef793dfd8e50a6ccd02bdafa66160

ema-architecture.png
source-original
先沿上半图从左到右读：文本规范化→编码及持续时间预测→对齐→四步生成→音频解码。下半图展开对齐和共享调制，不是额外四个模型。作者架构原图，Apache-2.0，保留全部公式；手机可打开原尺寸查看（[来源原图](https://huggingface.co/canberkkkkkk/ema-lightning)；[查看原尺寸](images/ema-architecture.png)。）
原始来源/数据：https://huggingface.co/canberkkkkkk/ema-lightning/resolve/main/assets/architecture.png
SHA256：a0dfc341328b5a6591418e9c18db180c332c5c7feb66505e2262b830b6797a44

tokenrouter.png
source-original
论文图2(b)对应的架构原图。紫色为客户请求，蓝色为解码，黑色为模型间传递；三条循环分开后才便于保留状态和批调度。Tianyu Fu等，CC BY 4.0；引用单个架构面板的原始图片文件，未重画。（[来源原图](https://arxiv.org/html/2610.12242v1)；[查看原尺寸](images/tokenrouter.png)。）
原始来源/数据：https://arxiv.org/html/2610.12242v1/architecture.png
SHA256：ff4fd9ae108f75ea1af0cc8180deb3f6f403efa24a3bbcc44e7b4b9bf8bd69eb

learn2play.png
source-original
论文图4原图：横轴对齐五轮/十轮计分窗口，纵轴是按论文规则归一化及加权后的分数。比较曲线走势，勿把横轴看成实际耗时。Yibo Li等，CC BY 4.0；完整保留原图。（[来源原图](https://arxiv.org/html/2610.08215v2)；[查看原尺寸](images/learn2play.png)。）
原始来源/数据：https://arxiv.org/html/2610.08215v2/figures/memory_backbones_learning_curve.png
SHA256：12db8aebc0e9a4af307f7d3a071321e2528d8c423fe342691d3df077c74d88aa

testprism.png
source-original
论文图1原图。重点看右侧：初始状态应失败，五个正确实现应通过，五个错误实现应失败；773是候选测试池，最终测试任务为300。Han Li等，CC BY 4.0；完整引用构建图，未改数字。（[来源原图](https://arxiv.org/html/2610.12289v1)；[查看原尺寸](images/testprism.png)。）
原始来源/数据：https://arxiv.org/html/2610.12289v1/testprism_overview.png
SHA256：23f97c39342040ed9280d6c731743bc5a963f5b37e765aa95068045d6845eea1

srd.png
source-original
论文图2原图。顺着上半部先看行动和反馈，再回到下半部的知识/风险提示及蒸馏目标；教师能看见学生事前没有的事后信息。Haoxiang Zhang等，CC BY 4.0，完整保留原图和公式。（[来源原图](https://arxiv.org/html/2610.08077v2)；[查看原尺寸](images/srd.png)。）
原始来源/数据：https://arxiv.org/html/2610.08077v2/fig/srd-fig2.png
SHA256：7cae00987adc2d129617e3b0b0a1004d7712261532c97599db8a01b85ff2f9b0

bigarrow.png
source-original
绿色箭头把提示文字关联到具体控件，橙色圈标出另一处入口。这是Franz Enzenhofer的作者演示原图，MIT；显示的是操作指引，不能证明工具已替用户授予权限。（[来源原图](https://github.com/franzenzenhofer/big-arrow-on-the-screen)；[查看原尺寸](images/bigarrow.png)。）
原始来源/数据：https://raw.githubusercontent.com/franzenzenhofer/big-arrow-on-the-screen/9c75dce6e87916d15cbdf6a2caa51ebd46c87665/docs/images/real/settings.png
SHA256：fde57206289a51f3601d23b9a65479ea77d3f1bf5a705e84bf34ad6e9a13d145

talorys-memory.png
source-original
先看右侧记忆卡的分类和编辑入口：这是rociiu提供的示例界面与示例数据，用于解释人工管理记忆；不是本站运行截图。原图按MIT许可引用，未裁切。（[来源原图](https://github.com/rociiu/talorys)；[查看原尺寸](images/talorys-memory.png)。）
原始来源/数据：https://raw.githubusercontent.com/rociiu/talorys/4aa1db8f997ff034a84b1ff9256b67abfa4f4b2b/docs/screenshots/memory.png
SHA256：6e6cd55cb5921d745caf2f017e793ed09bbcf2b29fa05e741c1fb52920da0109

pinrail-review.png
source-original
从左侧发现列表选项，再看中间差异及右侧决定区，可以理解为什么返回值不只是一个“通过”。Forgeplane作者演示原图，Apache-2.0，未改动；密集代码请打开原尺寸。（[来源原图](https://github.com/forgeplane/pinrail)；[查看原尺寸](images/pinrail-review.png)。）
原始来源/数据：https://raw.githubusercontent.com/forgeplane/pinrail/62182e6d9ecd54ab5b1df845242e8b0a364db7b2/.github/assets/review.png
SHA256：1fe710d39379c055ab9f4f5802e8f54610bf6fb58b6c25e8a34ed5d10dd1ea73

docflare-widget.png
source-original
看右侧回答下方的来源入口，读者可回到文档核对内容。p10node作者原图按MIT引用；截图仅说明问答交互，安装步骤以当前README的资源创建和迁移流程为准。（[来源原图](https://github.com/p10node/docflare-ai)；[查看原尺寸](images/docflare-widget.png)。）
原始来源/数据：https://raw.githubusercontent.com/p10node/docflare-ai/6c00950c87ce190ba43c376d3a02b5b6c5238d8d/docs/images/widget.png
SHA256：a8a23c37ea7e65e5c74bf88164ba0420a69f2095f8c963ff78a71879b3abdb6b

agentgarten.png
source-original
上半部左侧看同一几何如何变成不同外观，可理解已开放渲染器的作用；下半部是作者研究中的完整练习循环，目前并未随仓库全部开放。MirroS-Lab原图，Apache-2.0，未改动；图中的轮数是作者示例，不是本站测量。（[来源原图](https://github.com/MirroS-Lab/AgentGarten)；[查看原尺寸](images/agentgarten.png)。）
原始来源/数据：https://raw.githubusercontent.com/MirroS-Lab/AgentGarten/06bb4621deb9b380c34abb6dac42fe0b31eec2e3/assets/teaser.png
SHA256：48dd87a140a9a446be679eac59962feaf5182ab9eab3bb5d3e2f2f4fff6a51fd

trace2env-overview.png
source-original
左侧说明规则与证据从哪里来；右侧区分提议下一步的世界模型与保存状态的运行框架。ruyue0001及论文作者原图，Apache-2.0；输入轨迹不完整时，不能据此保证模拟世界正确。（[来源原图](https://github.com/ruyue0001/trace2env)；[查看原尺寸](images/trace2env-overview.png)。）
原始来源/数据：https://raw.githubusercontent.com/ruyue0001/trace2env/037c13a69cd50467ca75e1b5c912d574e6b4b942/assets/overview.png
SHA256：ef3abf9967469e7e395b9c7c3bcd18765c5ad21f3e1e822ffa392dcea625b889

procinsh-space.png
source-original
先看进程之间的连线和分组，再打开原尺寸观察节点标签；三维视图帮助发现关系，CPU或内存结论仍需核对具体指标。akawashiro作者原图，MIT，未裁切。（[来源原图](https://github.com/akawashiro/procinsh)；[查看原尺寸](images/procinsh-space.png)。）
原始来源/数据：https://raw.githubusercontent.com/akawashiro/procinsh/a209faa307ff07c642cf9a781566ef71bc708d42/images/procinsh_top.png
SHA256：49880547697834589011181af073cfdc9b49c71c90ffff8771cd9d6135663462

test-diversity-results.png
html-js
本机一个合成任务，2正确4错误；精确单元格来自JSON，不是论文复现。
原始来源/数据：https://arxiv.org/abs/2610.12289v1
SHA256：67fe9bf3d4ecea92dcf107e7af36b9b2309ccbc9101e1448aea84568f1c505e7
