// Builds case-study.html: inserts the case study data from ../page/src/data.js into case-study.src.html.
import { readFileSync, writeFileSync } from 'node:fs';
const data = readFileSync('../page/src/data.js', 'utf8').replace(/export const /g, 'var ');
const src = readFileSync('case-study.src.html', 'utf8');
writeFileSync('case-study.html', src.replace('/*DATA*/', data));
console.log('wrote case-study.html');
