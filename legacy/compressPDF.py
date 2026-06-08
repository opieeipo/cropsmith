"""
PDF Compressor using Ghostscript
This script allows the user to compress PDF files using Ghostscript. It provides
options to set the compression quality.
Requirements:
- Python 3.x
- Ghostscript installed on the system
Installation of Ghostscript:
- Windows: Download and install from https://www.ghostscript.com/download/gsdnld.html.
  Make sure to add the bin directory to your PATH.
- Linux (Ubuntu/Debian): Install using `sudo apt-get install ghostscript`.
- macOS: Install using `brew install ghostscript` if you have Homebrew installed.
Usage:
Run the script from the command line with the PDF file path and optionally, the quality setting.
Example: `python pdf_compressor_ghostscript.py input.pdf --quality ebook`
Available quality settings are 'screen', 'ebook', 'printer', and 'prepress'.
If no quality setting is specified, 'screen' will be used by default.
"""

import argparse
import subprocess

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

def main():
    """
    Main function to parse command line arguments and call the PDF compression function.
    """
    parser = argparse.ArgumentParser(description="Compress a PDF file using Ghostscript.")
    parser.add_argument("input_file", help="Path to the input PDF file")
    parser.add_argument("-q", "--quality", choices=['screen', 'ebook', 'printer', 'prepress'], default="screen",
                        help="Quality setting for the output PDF (default: screen)")

    args = parser.parse_args()

    # Generate output file name by appending '-min' before the file extension
    output_file = args.input_file.rsplit('.', 1)[0] + '-min.pdf'
    compress_pdf_with_ghostscript(args.input_file, output_file, args.quality)

if __name__ == "__main__":
    main()