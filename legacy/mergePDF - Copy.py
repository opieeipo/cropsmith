import PyPDF2
import sys
import os
import argparse
from pathlib import Path

parser = argparse.ArgumentParser()

parser.add_argument('folder')
parser.add_argument('outputfile')
args=parser.parse_args()
folder=args.folder
outputfile=args.outputfile

def merge_pdfs(pdf_files, output_file):
	"""Merges multiple PDF files into one."""

	merger = PyPDF2.PdfMerger()
	
	for pdf_file in pdf_files:
		fname =os.path.join(folder,pdf_file.name)
		#only add PDFs
		ext=(Path(fname).suffix).upper()		
		if (ext=='.PDF'):
			print (f'Adding in {fname} to {output_file}')
			with open(fname, 'rb') as f:
				merger.append(f)

	print (f'Writing pdfs to {outputfile}')
	with open(output_file, 'wb') as f:
		merger.write(f)

if __name__ == '__main__':
	pdf_files = os.scandir(folder)
	outputfile = os.path.join(".",outputfile)
	merge_pdfs(pdf_files, outputfile)

