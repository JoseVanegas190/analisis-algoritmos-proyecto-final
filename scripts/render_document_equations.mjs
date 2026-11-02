"use strict";

import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const sharp = require("sharp");
const { mathjax } = require("mathjax-full/js/mathjax.js");
const { TeX } = require("mathjax-full/js/input/tex.js");
const { SVG } = require("mathjax-full/js/output/svg.js");
const { liteAdaptor } = require("mathjax-full/js/adaptors/liteAdaptor.js");
const { RegisterHTMLHandler } = require("mathjax-full/js/handlers/html.js");
const { AllPackages } = require("mathjax-full/js/input/tex/AllPackages.js");

const output = path.resolve(process.argv[2] || "output/evidence/formulas");
fs.mkdirSync(output, { recursive: true });
const adaptor = liteAdaptor();
RegisterHTMLHandler(adaptor);
const document = mathjax.document("", { InputJax: new TeX({ packages: AllPackages }), OutputJax: new SVG({ fontCache: "local" }) });
const equations = {
  levenshtein: String.raw`D_{i,j}=\min\begin{cases}D_{i-1,j}+1\\D_{i,j-1}+1\\D_{i-1,j-1}+costo(a_i,b_j)\end{cases}`,
  needleman: String.raw`S_{i,j}=\max\begin{cases}S_{i-1,j-1}+s(a_i,b_j)\\S_{i-1,j}+gap\\S_{i,j-1}+gap\end{cases}`,
  jaccard: String.raw`J(A,B)=\frac{|A\cap B|}{|A\cup B|}`,
  tfidf: String.raw`TFIDF(t,d)=\frac{f(t,d)}{|d|}\left(\log\frac{N+1}{df(t)+1}+1\right)`,
  cosine: String.raw`\cos(\vec{u},\vec{v})=\frac{\sum_{i=1}^{m}u_i v_i}{\sqrt{\sum_{i=1}^{m}u_i^2}\sqrt{\sum_{i=1}^{m}v_i^2}}`,
  distance: String.raw`d(\vec{u},\vec{v})=1-\cos(\vec{u},\vec{v})`,
  single: String.raw`D_{single}(A,B)=\min_{x\in A,\,y\in B}d(x,y)`,
  complete: String.raw`D_{complete}(A,B)=\max_{x\in A,\,y\in B}d(x,y)`,
  average: String.raw`D_{average}(A,B)=\frac{1}{|A||B|}\sum_{x\in A}\sum_{y\in B}d(x,y)`,
  silhouette: String.raw`s(i)=\frac{b(i)-a(i)}{\max(a(i),b(i))}`,
};

async function main() {
  for (const [name, latex] of Object.entries(equations)) {
    let svg = adaptor.outerHTML(document.convert(latex, { display: true }));
    svg = svg.replace(/<\?xml[^>]*>/g, "");
    if (!svg.includes('xmlns="http://www.w3.org/2000/svg"')) svg = svg.replace("<svg ", '<svg xmlns="http://www.w3.org/2000/svg" ');
    svg = svg.replace(/currentColor/g, "#000000");
    await sharp(Buffer.from(svg)).png().toFile(path.join(output, `${name}.png`));
  }
}
main().catch((error) => { console.error(error); process.exit(1); });
