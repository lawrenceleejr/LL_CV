TEXFILE=LL_CV

pdflatex "\def\internalbool{true} \input{LL_CV.tex}"
mv LL_CV.pdf LL_CV_internal.pdf

pdflatex "\def\internalbool{false} \input{LL_CV.tex}"

rm -f *.aux *.log *.toc *.out *.lof *.lot *.bbl *.blg *.synctex.gz *.fls *.fdb_latexmk *.nav *.snm *.vrb
