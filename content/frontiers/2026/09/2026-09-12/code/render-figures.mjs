// Reproduce the three precise diagrams from source facts and local measurements.
// Node.js 18+: node render-figures.mjs
import { readFile, writeFile, mkdir } from 'node:fs/promises';
const out = new URL('../images/', import.meta.url);
await mkdir(out, { recursive: true });
const data = JSON.parse(await readFile(new URL('./results.json.txt', import.meta.url), 'utf8'));
const palette = { ink: '#142e38', muted: '#526b72', teal: '#087f83', blue: '#426fa0', orange: '#b95630', bg: '#fbfaf6', line: '#cfdad9' };
const esc = s => String(s).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
const txt = (x, y, s, size = 24, fill = palette.ink, weight = 400, anchor = 'start') => `<text x="${x}" y="${y}" font-size="${size}" fill="${fill}" font-weight="${weight}" text-anchor="${anchor}">${esc(s)}</text>`;
const rect = (x, y, w, h, fill = '#fff', stroke = palette.line) => `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="14" fill="${fill}" stroke="${stroke}" stroke-width="2"/>`;
const path = (d, color = palette.teal, dashed = false) => `<path d="${d}" fill="none" stroke="${color}" stroke-width="3" ${dashed ? 'stroke-dasharray="8 7"' : ''} marker-end="url(#arrow)"/>`;
const frame = (title, desc, body, height) => `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1120 ${height}" role="img" aria-labelledby="title-${height} desc-${height}">
<title id="title-${height}">${esc(title)}</title><desc id="desc-${height}">${esc(desc)}</desc>
<defs><marker id="arrow-${height}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="context-stroke"/></marker></defs>
<rect width="1120" height="${height}" fill="${palette.bg}"/>
<g font-family="PingFang SC,Microsoft YaHei,system-ui,sans-serif">${txt(44, 60, title, 32, palette.ink, 700)}${body.replaceAll('url(#arrow)', `url(#arrow-${height})`)}</g></svg>\n`;

const kimiRows = [
  { y: 160, entry: 'kimi-for-coding', setting: '开启思考', actual: 'K2.8 Preview', detail: 'low / high / max，默认 max', color: palette.teal },
  { y: 288, entry: 'K3 系列入口', setting: '开启思考', actual: '所选 K3 型号', detail: '默认 high；会员条件另计', color: palette.blue },
  { y: 416, entry: '以上两类入口', setting: '关闭思考', actual: 'K2.8 Preview 无思考版', detail: '关闭后，实际执行模型相同', color: palette.orange },
];
let body = txt(44, 106, '2026-09-12 核验｜模型 ID 与实际执行模型要分开记录', 21, palette.muted);
for (const [x, label] of [[62, '调用入口'], [450, '思考配置'], [752, '实际执行']]) body += txt(x, 145, label, 20, palette.muted, 600);
for (const r of kimiRows) {
  body += rect(44, r.y, 316, 96) + txt(62, r.y + 56, r.entry, 25, r.color, 600);
  body += rect(431, r.y, 190, 96) + txt(526, r.y + 56, r.setting, 25, r.color, 600, 'middle');
  body += rect(734, r.y, 342, 96, '#fff', r.color) + txt(752, r.y + 39, r.actual, 24, r.color, 700) + txt(752, r.y + 73, r.detail, 19, palette.muted);
  body += path(`M 360 ${r.y + 48} H 425`, r.color) + path(`M 621 ${r.y + 48} H 728`, r.color);
}
body += txt(44, 554, '来源：Kimi Code 模型规格 / 最新动态；HTML + JavaScript 制作', 18, palette.muted);
const kimi = frame('关闭思考后，K3 入口也会交给 K2.8 处理', '三个条件分支，对照模型入口、思考配置和最终执行模型。', body, 585);

body = txt(44, 104, '2026-09-12 核验｜依据更新日志与当前价格页', 21, palette.muted);
body += rect(44, 138, 1032, 94, '#fff2eb', '#e3b7a4');
body += txt(64, 174, '旧发布文章仍写：9 月 14 日将 Pro 转到 V4.1 Flash', 24, palette.orange, 600);
body += txt(64, 210, '当前两个服务页面已改为：Pro 继续提供，计费不变，后续另行通知。', 21, palette.ink);
body += rect(44, 267, 404, 92) + txt(66, 318, 'deepseek-v4-pro', 26, palette.teal, 600);
body += path('M 448 313 H 664');
body += rect(672, 267, 404, 92, '#eef8f4', palette.teal) + txt(694, 310, 'DeepSeek-V4-Pro-0813', 25, palette.teal, 700) + txt(694, 339, '继续提供；当前表列为无视觉输入', 19, palette.muted);
body += rect(44, 395, 404, 64) + txt(66, 436, 'deepseek-flash', 25, palette.blue, 600);
body += rect(44, 485, 404, 99) + txt(66, 521, 'deepseek-v4-flash', 22, palette.blue) + txt(66, 555, 'deepseek-v4-flash-vision-exp', 22, palette.blue);
body += path('M 448 427 H 570 V 469 H 664', palette.blue) + path('M 448 534 H 570 V 490 H 664', palette.blue);
body += rect(672, 424, 404, 117, '#eef3fa', palette.blue) + txt(694, 472, 'V4.1 Flash', 27, palette.blue, 700) + txt(694, 513, '支持视觉；旧 Flash 别名仍临时路由至此', 18, palette.muted);
body += txt(44, 625, '服务页面存在更新差异；本图未使用付费请求验证后端。', 20, palette.muted);
body += txt(44, 660, '来源：DeepSeek 更新日志与模型价格页；HTML + JavaScript 制作', 18, palette.muted);
const deepseek = frame('保留 Pro，不等于恢复旧 Flash', '将旧公告与当前状态分开，画出 Pro 和 Flash 别名各自的路由。', body, 692);

const trials = ['blocking', 'cooperative'].map(mode => data.trials.find(r => r.mode === mode));
const xmax = Math.ceil(Math.max(...trials.flatMap(r => r.tick_ms)) / 50) * 50;
const X = ms => 215 + 810 * ms / xmax;
body = txt(44, 103, '本站实测｜Python ' + data.python + ' · 相同 400 万次运算 · 心跳目标间隔 5 ms', 21, palette.muted);
for (let t = 0; t <= xmax; t += 50) {
  body += `<line x1="${X(t)}" y1="144" x2="${X(t)}" y2="386" stroke="${palette.line}"/>`;
  body += txt(X(t), 418, t, 19, palette.muted, 400, 'middle');
}
trials.forEach((r, i) => {
  const y = 199 + i * 121, color = i === 0 ? palette.orange : palette.teal;
  body += txt(44, y - 12, i === 0 ? '连续计算' : '分块让出执行权', 23, color, 700);
  body += txt(44, y + 20, '第 1 次运行', 18, palette.muted);
  body += rect(X(r.work_start_ms), y - 29, X(r.work_end_ms) - X(r.work_start_ms), 59, i === 0 ? '#f4ddcf' : '#d9eee7', 'none');
  for (const tick of r.tick_ms) body += `<line x1="${X(tick)}" y1="${y - 40}" x2="${X(tick)}" y2="${y + 39}" stroke="${color}" stroke-width="2"/>`;
});
body += txt(1025, 449, '从启动心跳起计时（ms）', 19, palette.muted, 400, 'end');
body += txt(215, 481, '色块 = CPU 工作区间；竖线 = 心跳实际获得执行的时间', 20, palette.muted);
const b = data.summary.blocking, c = data.summary.cooperative;
body += rect(44, 514, 1032, 157);
body += txt(65, 552, '每种方式各运行 5 次，以下取中位数', 22, palette.ink, 600);
body += txt(65, 598, '最大心跳迟到：', 22) + txt(285, 598, b.max_heartbeat_delay_ms_median.toFixed(2) + ' ms → ' + c.max_heartbeat_delay_ms_median.toFixed(2) + ' ms', 26, palette.teal, 700);
body += txt(65, 641, 'CPU 工作耗时：', 22) + txt(285, 641, b.work_ms_median.toFixed(2) + ' ms → ' + c.work_ms_median.toFixed(2) + ' ms', 26, palette.orange, 700);
body += txt(44, 713, '改善的是调度响应；本实验没有证明计算加速，也不是 Habitat 性能复现。', 20, palette.muted);
body += txt(44, 748, '数据：results.json.txt；代码：event_loop_probe.py；HTML + JavaScript 制图', 18, palette.muted);
const practice = frame('让出执行权后，心跳不必等整段计算结束', '实际时间轴和五次实验中位数，区分 CPU 工作耗时与心跳迟到。', body, 778);
const outputs = { 'news-kimi-routing.svg': kimi, 'news-deepseek-routing.svg': deepseek, 'practice-event-loop.svg': practice };
for (const [name, svg] of Object.entries(outputs)) await writeFile(new URL(name, out), svg);
const html = `<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>09-12 精确关系与实测图</title><style>body{margin:0;background:#f1f2ef;color:#142e38;font:18px/1.7 system-ui,sans-serif}main{max-width:1120px;margin:auto;padding:24px}nav{display:flex;gap:10px;flex-wrap:wrap}button{padding:8px 16px;border:1px solid #9fb5b6;border-radius:8px;background:white;cursor:pointer;font:inherit}button[aria-pressed=true]{background:#087f83;color:white}figure{margin:24px 0}svg{width:100%;height:auto;display:block}a{color:#087f83}footer{margin:20px 0}</style><main><h1>09-12 精确关系与实测图</h1><p>点击切换图表。数字取自官方说明或本地实验；完整复现方式见 README.txt。</p><nav>${Object.keys(outputs).map((n,i)=>`<button type="button" data-i="${i}" aria-pressed="${i===0}">${['Kimi 路由','DeepSeek 服务状态','事件循环实测'][i]}</button>`).join('')}</nav>${Object.values(outputs).map((s,i)=>`<figure data-i="${i}" ${i?'hidden':''}>${s}</figure>`).join('')}<footer><a href="render-figures.mjs">JavaScript 源码</a> · <a href="results.json.txt">实验原始数据</a></footer></main><script>document.querySelectorAll('button').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('button').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));document.querySelectorAll('figure').forEach(f=>f.hidden=f.dataset.i!==b.dataset.i)}));</script></html>\n`;
await writeFile(new URL('./figures.html', import.meta.url), html);
console.log('Wrote ' + Object.keys(outputs).join(', ') + ' and figures.html');
