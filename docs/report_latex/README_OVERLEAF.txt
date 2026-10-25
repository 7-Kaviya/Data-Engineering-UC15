UC15 ERPDP - CAPSTONE PROJECT REPORT (LaTeX project for Overleaf)

OPEN IT IN OVERLEAF
1. overleaf.com > New Project > Upload Project > choose this zip file.
2. main.tex opens. Click Recompile (compiler: pdfLaTeX, main document: main.tex - the defaults).
3. Download the PDF with the "Download PDF" button above the preview.
   Compile twice if the table of contents or the numbers of tables look wrong.

FILL IN THE TITLE PAGE (top of main.tex, about line 33)
   \newcommand{\institution}{}      ->  \newcommand{\institution}{Name of your institute}
   \newcommand{\guide}{}            ->  \newcommand{\guide}{Name of your guide or professor}
   \newcommand{\reportdate}{October 2026}   (change the date if needed)
   A line that is left empty is not printed.
   The three names are in the title page block, a few lines below.

FILES
   main.tex                         the whole report
   figures/Architecture_Layers.png  Figure 3.1
   figures/ERD_uc15_dw.png          Figure 3.2
   figures/Lineage_Diagram.png      Figure B.1 (appendix, printed sideways)

TIPS FOR EDITING
   - Chapters are marked with \chapter{...}, sections with \section{...}.
   - File names and code go inside \code{...} and are written as they are (underscores need no backslash there).
   - Outside \code{}, write \_ \% \& \# \$ with a backslash.
   - Do not put \code{...} inside a \caption{...} or a \section{...} title; use \texttt{...} with \_ there.
   - Tables are written with & between cells and \\ at the end of a row; the long tables are generated sections of main.tex.
   - References are cited with \cite{kimball} and listed at the end of the file.
