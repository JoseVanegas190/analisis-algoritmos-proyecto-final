"""Genera ecuaciones renderizadas para el informe cuando no se requiere edición en Word."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt


FORMULAS = {
    "levenshtein": r"$D_{i,j}=\min\{D_{i-1,j}+1,\ D_{i,j-1}+1,\ D_{i-1,j-1}+costo(a_i,b_j)\}$",
    "needleman": r"$S_{i,j}=\max\{S_{i-1,j-1}+s(a_i,b_j),\ S_{i-1,j}+gap,\ S_{i,j-1}+gap\}$",
    "jaccard": r"$J(A,B)=\frac{|A\cap B|}{|A\cup B|}$",
    "tfidf": r"$TFIDF(t,d)=\frac{f(t,d)}{|d|}\left(\log\frac{N+1}{df(t)+1}+1\right)$",
    "cosine": r"$\cos(\vec{u},\vec{v})=\frac{\sum_{i=1}^{m}u_i v_i}{\sqrt{\sum_{i=1}^{m}u_i^2}\sqrt{\sum_{i=1}^{m}v_i^2}}$",
    "distance": r"$d(\vec{u},\vec{v})=1-\cos(\vec{u},\vec{v})$",
    "single": r"$D_{single}(A,B)=\min_{x\in A,\ y\in B}d(x,y)$",
    "complete": r"$D_{complete}(A,B)=\max_{x\in A,\ y\in B}d(x,y)$",
    "average": r"$D_{average}(A,B)=\frac{1}{|A||B|}\sum_{x\in A}\sum_{y\in B}d(x,y)$",
    "silhouette": r"$s(i)=\frac{b(i)-a(i)}{\max(a(i),b(i))}$",
}


def main() -> None:
    output = Path(__file__).parents[1] / "output" / "evidence" / "formulas"
    output.mkdir(parents=True, exist_ok=True)
    for name, formula in FORMULAS.items():
        figure = plt.figure(figsize=(8, 0.65))
        figure.text(.5, .5, formula, ha="center", va="center", fontsize=18)
        plt.axis("off")
        figure.savefig(output / f"{name}.png", dpi=250, transparent=True, bbox_inches="tight", pad_inches=.05)
        plt.close(figure)


if __name__ == "__main__":
    main()
