import os
from pdf2image import convert_from_path
import argparse
import fnmatch
import ocrmypdf
import pdf2docx
import pdf2image
import tempfile
import uuid
from pathlib import Path
import PyPDF2
import subprocess
from tqdm.auto import tqdm

from pdf2docx import Converter

parser = argparse.ArgumentParser()

parser.add_argument('pdf')
args=parser.parse_args()
pdf_file=args.pdf
os.system('cls')

def pdfconvert(pdffile):
    pdffile =os.path.join(".",pdffile)
    print (f'Input file:{pdffile}')
    #first convert the PDF to images and OCR
    print (f'Generating images from pages of {pdffile}')
    images=convert_from_path(pdffile,dpi=96)
    print (pdffile)
    #instantiate the PDF Merger
    

    #make our master PDF file
    master_pdf = Path(pdffile).stem+"_OCR.pdf"
    print (f'Output PDF will be {master_pdf}')
    #create a guid for a file name
    new_guid = uuid.uuid4()
    guid_str = str(new_guid)
    
    docx_path =os.path.join(".",Path(pdffile).stem+".docx")
    print (f'Output Word File will be {docx_path}')    
    #get the temp dir
    tempdir = tempfile.gettempdir()
    m=len(images)
    print (f'{m}: pages found')    
    merger = PyPDF2.PdfMerger()
    total = range(len(images))
        

    for i in tqdm(range(len(images))):
        #save off the image created to a file
        image_path =os.path.join(tempdir,f'{guid_str}_{i}.png')
        images[i].save(image_path)
        print (f'Temporary image file {image_path} created')    
        
        if (i==0):
            pdf_path=master_pdf
        else:
            pdf_path = os.path.join(tempdir,f'{guid_str}_{i}.pdf')
        
        #OCR the image to a PDF
        print (f'Using Optical Character Recognition to identify the text from the image file')
        ocrmypdf.ocr(image_path,pdf_path,language="eng",deskew=True,image_dpi=96) 
        print (f'{pdf_path} created')
        
        #merge that PDF into the masterPDF
       
                
        print (f'Appending {pdf_path} to master PDF')
        with open(pdf_path, 'rb') as f:
            merger.append(f)
            f.close()            
                
        #dump the old pdf file (do not do this with the master)
        print(f'Cleaning up by removing temporary PDF file {pdf_path}')
        os.remove(pdf_path)
            
        #dump the old image        
        print (f'Cleaning up by removing temporary image file {image_path}')
        os.remove(image_path)
        os.system('cls')

    print (f'Writing Master PDF File {master_pdf}')
    
    tempmaster = os.path.join(tempdir,master_pdf)
    merger.write(tempmaster)
    
    #compress it
    print (f'Compressing {master_pdf}')
    compress_pdf_with_ghostscript(tempmaster,master_pdf ,'screen' )
    print (f'all pages converted and merged in {master_pdf}.  Now beginning conversion to {docx_path}')
    #convert the file to a docx
    #instantiate the converter
    cv = Converter(master_pdf)
    cv.convert(docx_path)
    cv.close()

def compress_pdf_with_ghostscript(input_path, output_path, quality):
    """
    Compresses a PDF file using Ghostscript.
    Args:
    input_path (str): Path to the input PDF file.
    output_path (str): Path where the compressed PDF will be saved.
    quality (str): Quality setting for compression ('screen', 'ebook', 'printer', 'prepress').
    """
    subprocess.call(['gs', '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.4',
                     '-dPDFSETTINGS=/' + quality, '-dNOPAUSE', '-dQUIET', '-dBATCH',
                     '-sOutputFile=' + output_path, input_path])

if __name__ == '__main__':
    pdfconvert(pdf_file)

