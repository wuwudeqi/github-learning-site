import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const dir = path.dirname(fileURLToPath(import.meta.url));
const result = JSON.parse(await readFile(path.join(dir, 'etag-results.json.txt'), 'utf8'));
if (!result.passed || result.rows.map(r => r.status).join(',') !== '200,304,200') {
  throw new Error('Expected the verified three-step experiment; inspect the data before rendering.');
}
const esc = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&apos;'}[c]));
const tags = new Map([...new Set(result.rows.map(r => r.responseETag))].map((tag, i) => [tag, String.fromCharCode(65+i)]));
const txt = (x,y,s,size=22,fill='#24364a',weight=400,anchor='start') => `<text x="${x}" y="${y}" font-size="${size}" fill="${fill}" font-weight="${weight}" text-anchor="${anchor}">${esc(s)}</text>`;
const panels = result.rows.map((r,i) => {
  const y = 135+i*270, cached = r.status===304, tag=tags.get(r.responseETag);
  return `<g>
  <rect x="20" y="${y}" width="600" height="250" rx="18" fill="${cached?'#fff6dd':'#ffffff'}" stroke="${cached?'#dcb660':'#d5dfe9'}"/>
  ${txt(42,y+37,`${r.step}. ${r.label}`,25,'#122e48',650)}
  <line x1="115" y1="${y+72}" x2="115" y2="${y+179}" stroke="#c3cfdc" stroke-dasharray="5 5"/>
  <line x1="525" y1="${y+72}" x2="525" y2="${y+179}" stroke="#c3cfdc" stroke-dasharray="5 5"/>
  <line x1="122" y1="${y+92}" x2="513" y2="${y+92}" stroke="#2767ae" stroke-width="3" marker-end="url(#blue)"/>
  ${txt(320,y+81,r.requestETag?`GET · If-None-Match: ${tags.get(r.requestETag)}`:'GET · 没有旧标签',22,'#22598f',500,'middle')}
  <line x1="515" y1="${y+150}" x2="128" y2="${y+150}" stroke="#168074" stroke-width="3" marker-end="url(#green)"/>
  ${txt(320,y+138,`${r.status} · 正文 ${r.responseBytes} B · ETag ${tag}`,23,'#11645d',650,'middle')}
  ${txt(42,y+205,cached?`客户端复用 ${r.usedBytes} B 缓存，内容仍为 ${tag}`:`客户端保存 ${r.usedBytes} B 正文，内容变为 ${tag}`,24,'#122e48',600)}
  ${txt(42,y+232,cached?'0 B 指响应正文，不是应用显示内容为空':i===0?'源站与客户端现在持有相同版本':'旧标签 A 已不匹配，必须获取新正文',19,'#54677a')}
  </g>`;
}).join('');
const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="640" height="1030" viewBox="0 0 640 1030" role="img" aria-labelledby="title desc">
<title id="title">ETag 本地实验：200、304、200</title><desc id="desc">三次实际请求分别收到25、0、46字节响应正文；第二次复用25字节缓存。数据来自已通过断言的本地实验。</desc>
<defs><marker id="blue" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8" fill="#2767ae"/></marker><marker id="green" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8" fill="#168074"/></marker></defs>
<rect width="640" height="1030" fill="#f3f6fa"/>
<g font-family="PingFang SC, Microsoft YaHei, sans-serif">
${txt(28,44,'没有新正文，也可以是有效结果',29,'#102d48',700)}
${txt(28,79,'ETag · 2026-09-13 本机真实响应',21,'#5a6f83')}
${txt(115,119,'客户端',23,'#122e48',650,'middle')}${txt(525,119,'源站',23,'#122e48',650,'middle')}
${panels}
${txt(28,987,'A / B 是内容哈希简称 · 只验证本地测试数据',20,'#5a6f83')}
${txt(28,1014,'JS 依据 etag-results.json.txt 生成',18,'#5a6f83')}
</g></svg>`;
await mkdir(path.join(dir,'../images'),{recursive:true});
await writeFile(path.join(dir,'../images/practice-etag.svg'),svg);
await writeFile(path.join(dir,'etag-flow.html'),`<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>ETag 三次请求</title><style>body{margin:0;background:#f3f6fa}main{max-width:640px;margin:auto}svg{display:block;width:100%;height:auto}</style><main>${svg}</main></html>`);
console.log('Rendered verified ETag data to SVG and HTML.');
