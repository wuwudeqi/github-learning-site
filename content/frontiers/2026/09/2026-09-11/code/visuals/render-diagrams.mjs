import { readFile, writeFile } from 'node:fs/promises';
import { renderDiagram } from './render.js';

const scenes = JSON.parse(await readFile(new URL('./diagrams.json.txt', import.meta.url), 'utf8'));
const result = JSON.parse(await readFile(new URL('./practice-result.json.txt', import.meta.url), 'utf8'));
for (const scene of scenes) {
  await writeFile(new URL(`../../images/${scene.name}.svg`, import.meta.url), renderDiagram(scene, result));
  console.log(`Exported ${scene.name}.svg`);
}
