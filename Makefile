
all: compile 

compile:
	pdflatex $(f).tex

open:
	open $(f).pdf

clean:
	rm -rf *.aux *.log *pdf *.dvi *-converted-*.pdf
