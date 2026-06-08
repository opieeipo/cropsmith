import sys
import os
import argparse
from pathlib import Path

from pdf2docx import Converter

parser = argparse.ArgumentParser()

parser.add_argument('pdf')
args=parser.parse_args()
pdf_file=args.pdf


def pdfconvert(pdffile):
    
    docxfile = Path(pdffile).stem+".docx"

    cv = Converter(pdffile)
    cv.convert(docxfile)
    cv.close()

if __name__ == '__main__':
    pdfconvert(pdf_file)
