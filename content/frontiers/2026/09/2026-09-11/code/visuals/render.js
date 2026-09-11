// Reproducible renderer for the issue's precise diagrams.
// The scene data retains the earlier original layout, now exportable in HTML/JS.
const escape = (value) => String(value).replace(/[&<>"']/g, (c) => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&apos;',
}[c]));

function boundText(binding, result) {
  if (binding.format === 'rates') return `总通过率：${result.cases - result.transitions.kept_fail.length - result.transitions.improved.length} / ${result.cases} → ${result.cases - result.transitions.kept_fail.length - result.transitions.regressed.length} / ${result.cases}`;
  if (binding.format === 'delta') return `差值 +${result.delta_percentage_points} 个百分点；不能据此判断所有能力都改善。`;
  const value = binding.path.reduce((value, key) => value[key], result);
  return binding.format === 'length' ? value.length : value;
}

function element(node, result) {
  const attrs = Object.entries(node.attrs || {}).map(([key,value]) => ` ${key}="${escape(value)}"`).join('');
  const text = node.binding ? boundText(node.binding, result) : (node.text || '');
  return `<${node.tag}${attrs}>${escape(text)}${(node.children || []).map(n => element(n, result)).join('')}</${node.tag}>`;
}

export function renderDiagram(scene, result) {
  return element(scene.svg, result) + '\n';
}
