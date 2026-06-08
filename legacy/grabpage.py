#!/usr/bin/env python3
"""
Website Spider to PDF
Crawls an entire website and converts all content to a PDF file.
"""

import requests
from bs4 import BeautifulSoup
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
import argparse
import sys
from urllib.parse import urlparse, urljoin, urldefrag
import re
from collections import deque
import time


class WebsiteSpider:
    """Spider that crawls a website and extracts content."""
    
    def __init__(self, start_url, max_pages=50, timeout=30, user_agent=None, delay=1.0, quiet=False):
        self.start_url = start_url
        self.max_pages = max_pages
        self.timeout = timeout
        self.delay = delay
        self.quiet = quiet
        self.user_agent = user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        
        # Parse the base domain to stay within the same site
        parsed = urlparse(start_url)
        self.base_domain = f"{parsed.scheme}://{parsed.netloc}"
        self.domain = parsed.netloc
        
        # Track visited URLs and pages to scrape
        self.visited = set()
        self.to_visit = deque([start_url])
        self.scraped_pages = []
        
    def normalize_url(self, url):
        """Normalize URL by removing fragments and trailing slashes."""
        # Remove fragment
        url, _ = urldefrag(url)
        # Remove trailing slash
        if url.endswith('/') and url != self.base_domain + '/':
            url = url.rstrip('/')
        return url
    
    def is_valid_url(self, url):
        """Check if URL should be crawled."""
        parsed = urlparse(url)
        
        # Must be http or https
        if parsed.scheme not in ['http', 'https']:
            return False
        
        # Must be same domain
        if parsed.netloc != self.domain:
            return False
        
        # Skip common non-content URLs
        skip_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.zip', 
                          '.mp4', '.mp3', '.css', '.js', '.xml', '.json']
        if any(url.lower().endswith(ext) for ext in skip_extensions):
            return False
        
        # Skip common non-content paths
        skip_patterns = ['/wp-admin', '/admin', '/login', '/logout', 
                        '/cart', '/checkout', '/account']
        if any(pattern in url.lower() for pattern in skip_patterns):
            return False
        
        return True
    
    def extract_links(self, soup, current_url):
        """Extract all valid links from a page."""
        links = set()
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Convert relative URLs to absolute
            absolute_url = urljoin(current_url, href)
            
            # Normalize and validate
            normalized = self.normalize_url(absolute_url)
            
            if self.is_valid_url(normalized) and normalized not in self.visited:
                links.add(normalized)
        
        return links
    
    def scrape_page(self, url):
        """Scrape content from a single page."""
        try:
            if not self.quiet:
                print(f"  Scraping: {url}")
            
            headers = {'User-Agent': self.user_agent}
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                script.decompose()
            
            # Extract title
            title = soup.find('title')
            title = title.get_text().strip() if title else url
            
            # Extract main content
            main_content = None
            for tag in ['main', 'article', '[role="main"]']:
                main_content = soup.select_one(tag)
                if main_content:
                    break
            
            if not main_content:
                # Try to find content divs
                for tag in soup.find_all('div', class_=re.compile(r'content|main|article', re.I)):
                    main_content = tag
                    break
            
            if not main_content:
                main_content = soup.find('body')
            
            # Extract text from paragraphs and headings
            content_elements = []
            if main_content:
                for element in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li', 'blockquote']):
                    text = element.get_text().strip()
                    if text and len(text) > 1:  # Skip empty or single-char elements
                        content_elements.append({
                            'type': element.name,
                            'text': text
                        })
            
            # Extract links for crawling
            links = self.extract_links(soup, url)
            
            return {
                'url': url,
                'title': title,
                'content': content_elements,
                'links': links
            }
            
        except requests.exceptions.RequestException as e:
            if not self.quiet:
                print(f"  Error fetching {url}: {e}")
            return None
        except Exception as e:
            if not self.quiet:
                print(f"  Error processing {url}: {e}")
            return None
    
    def crawl(self):
        """Crawl the website starting from the start URL."""
        if not self.quiet:
            print(f"Starting crawl from: {self.start_url}")
            print(f"Maximum pages: {self.max_pages}")
            print()
        
        while self.to_visit and len(self.visited) < self.max_pages:
            # Get next URL to visit
            current_url = self.to_visit.popleft()
            
            # Skip if already visited
            if current_url in self.visited:
                continue
            
            # Mark as visited
            self.visited.add(current_url)
            
            # Scrape the page
            page_data = self.scrape_page(current_url)
            
            if page_data and page_data['content']:
                self.scraped_pages.append(page_data)
                
                # Add new links to queue
                for link in page_data['links']:
                    if link not in self.visited:
                        self.to_visit.append(link)
            
            # Be polite - delay between requests
            if self.to_visit:
                time.sleep(self.delay)
        
        if not self.quiet:
            print()
            print(f"Crawl complete. Scraped {len(self.scraped_pages)} pages.")
        
        return self.scraped_pages


def create_pdf(pages, output_file, start_url):
    """
    Create a PDF from scraped pages.
    
    Args:
        pages: List of page data dictionaries
        output_file: Path to output PDF file
        start_url: Original start URL
    """
    doc = SimpleDocTemplate(
        output_file,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor='#2C3E50',
        spaceAfter=12,
        alignment=TA_LEFT
    )
    
    page_title_style = ParagraphStyle(
        'PageTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor='#2C3E50',
        spaceAfter=10,
        spaceBefore=10
    )
    
    url_style = ParagraphStyle(
        'URLStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor='#7F8C8D',
        spaceAfter=20
    )
    
    heading_styles = {
        'h1': styles['Heading1'],
        'h2': styles['Heading2'],
        'h3': styles['Heading3'],
        'h4': styles['Heading4'],
        'h5': styles['Heading5'],
        'h6': styles['Heading6']
    }
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=11,
        alignment=TA_JUSTIFY,
        spaceAfter=12
    )
    
    list_style = ParagraphStyle(
        'ListStyle',
        parent=styles['BodyText'],
        fontSize=11,
        leftIndent=20,
        spaceAfter=6
    )
    
    quote_style = ParagraphStyle(
        'QuoteStyle',
        parent=styles['BodyText'],
        fontSize=10,
        leftIndent=30,
        rightIndent=30,
        textColor='#34495E',
        spaceAfter=12
    )
    
    # Add main title
    domain = urlparse(start_url).netloc
    elements.append(Paragraph(f"Website Content: {domain}", title_style))
    elements.append(Paragraph(f"Source: {start_url}", url_style))
    elements.append(Paragraph(f"Pages scraped: {len(pages)}", url_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Add each page
    for i, page in enumerate(pages):
        # Page title
        elements.append(Paragraph(page['title'], page_title_style))
        elements.append(Paragraph(f"URL: {page['url']}", url_style))
        
        # Page content
        for item in page['content']:
            text = item['text'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            # Truncate very long text
            if len(text) > 1000:
                text = text[:1000] + '...'
            
            try:
                if item['type'] in heading_styles:
                    elements.append(Spacer(1, 0.1*inch))
                    elements.append(Paragraph(text, heading_styles[item['type']]))
                elif item['type'] == 'li':
                    elements.append(Paragraph(f"• {text}", list_style))
                elif item['type'] == 'blockquote':
                    elements.append(Paragraph(text, quote_style))
                else:  # paragraph
                    elements.append(Paragraph(text, body_style))
            except Exception as e:
                # Skip problematic content
                continue
        
        # Page break between pages (except last page)
        if i < len(pages) - 1:
            elements.append(PageBreak())
    
    # Build PDF
    try:
        doc.build(elements)
        print(f"PDF successfully created: {output_file}")
    except Exception as e:
        print(f"Error creating PDF: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Spider/crawl a website and convert all content to PDF',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s https://example.com
  %(prog)s https://example.com -o output.pdf --max-pages 100
  %(prog)s https://example.com -o research.pdf --delay 2 --timeout 60
  %(prog)s https://example.com --max-pages 20 --quiet
        """
    )
    
    # Required arguments
    parser.add_argument(
        'url',
        help='Starting URL to spider/crawl'
    )
    
    # Optional arguments
    parser.add_argument(
        '-o', '--output',
        help='Output PDF filename (default: auto-generated from URL)',
        default=None,
        metavar='FILE'
    )
    
    parser.add_argument(
        '--max-pages',
        help='Maximum number of pages to crawl (default: 50)',
        type=int,
        default=50,
        metavar='N'
    )
    
    parser.add_argument(
        '-t', '--timeout',
        help='Request timeout in seconds (default: 30)',
        type=int,
        default=30,
        metavar='SECONDS'
    )
    
    parser.add_argument(
        '--delay',
        help='Delay between requests in seconds (default: 1.0)',
        type=float,
        default=1.0,
        metavar='SECONDS'
    )
    
    parser.add_argument(
        '--user-agent',
        help='Custom User-Agent string',
        default='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        metavar='STRING'
    )
    
    parser.add_argument(
        '-q', '--quiet',
        help='Suppress output messages',
        action='store_true'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 2.0'
    )
    
    args = parser.parse_args()
    
    # Generate default output filename if not provided
    if args.output is None:
        domain = urlparse(args.url).netloc.replace('www.', '')
        safe_domain = re.sub(r'[^\w\-_.]', '_', domain)
        args.output = f"{safe_domain}_spider.pdf"
    
    # Create spider and crawl
    spider = WebsiteSpider(
        start_url=args.url,
        max_pages=args.max_pages,
        timeout=args.timeout,
        user_agent=args.user_agent,
        delay=args.delay,
        quiet=args.quiet
    )
    
    pages = spider.crawl()
    
    if not pages:
        print("No content was scraped. Exiting.")
        sys.exit(1)
    
    if not args.quiet:
        print(f"Creating PDF: {args.output}")
    
    create_pdf(pages, args.output, args.url)
    
    if not args.quiet:
        print("Done!")


if __name__ == '__main__':
    main()