import PyPDF2
from PIL import Image
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

def get_file_type(file_path):
    """Determines the file type (PDF, Image, or Other) based on its extension."""
    ext = Path(file_path).suffix.upper()
    if ext == '.PDF':
        return 'PDF'
    elif ext in ['.PNG', '.JPG', '.JPEG']:
        return 'IMAGE'
    else:
        return 'OTHER'

def merge_pdfs(pdf_files, output_file):
    """Merges multiple PDF files into one."""
    merger = PyPDF2.PdfMerger()
    for pdf_file in pdf_files:
        print(f'Adding {pdf_file} to PDF merger')
        with open(pdf_file, 'rb') as f:
            merger.append(f)
    print(f'Writing combined PDFs to {output_file}')
    with open(output_file, 'wb') as f:
        merger.write(f)

def merge_images(image_files, output_file):
    """Combines multiple image files into a single PDF."""
    image_list = []
    for image_file in image_files:
        try:
            print(f'Converting {image_file} to PDF')
            img = Image.open(image_file).convert('RGB')
            image_list.append(img)
        except Exception as e:
            print(f"Error processing image {image_file}: {e}")
    if not image_list:
        print("No valid images found to combine.")
        return
    # Save the first image, with subsequent images as additional pages
    image_list[0].save(output_file, save_all=True, append_images=image_list[1:])
    print(f'Combined images into PDF at {output_file}')


if __name__ == '__main__':
    pdf_files = []
    image_files = []
    # Iterate through the folder and categorize files
    for entry in os.scandir(folder):
        if entry.is_file():
            file_path = os.path.join(folder, entry.name)
            file_type = get_file_type(file_path)
            if file_type == 'PDF':
                pdf_files.append(file_path)
            elif file_type == 'IMAGE':
                image_files.append(file_path)
    if pdf_files:
        print("PDF files found. Merging PDFs...")
        merge_pdfs(pdf_files, outputfile)
    elif image_files:
        print("Image files found. Merging images into a single PDF...")
        merge_images(image_files, outputfile)
    else:
        print("No supported PDF or image files (.png, .jpg, .jpeg) found in the specified folder.")
