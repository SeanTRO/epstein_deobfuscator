import os
import glob
from bs4 import BeautifulSoup
import requests
import concurrent.futures
import threading

# Load examplebad.htm content for comparison once globally
# This prevents reading the file thousands of times in parallel
bad_html_path = os.path.join(os.path.dirname(__file__), 'html', 'examplebad.htm')
match_marker = b"<title> Department of Justice |  Page not found</title>"
try:
    with open(bad_html_path, 'rb') as f:
        # Verify we can read it, though we rely on the constant marker mostly
        f.read(100)
except Exception as e:
    print(f"Warning: Could not load examplebad.htm from {bad_html_path}: {e}")
    match_marker = b"Page not found" # Fallback

# Lock for writing to the missing files log
file_lock = threading.Lock()

def process_link(link):
    # Extract the filename from the link
    filename = os.path.basename(link)
    
    # Extract the base of the link (remove extension if present)
    base_link, _ = os.path.splitext(link)
    base_filename, _ = os.path.splitext(filename)

    # Check if file already exists (any extension)
    existing_files = glob.glob(f"{base_filename}.*")
    if existing_files:
        # print(f"Skipping {base_filename}, already exists: {existing_files[0]}")
        return
    
    print(f"Processing link: {link}")
    
    # Extensions to brute-force check
    acceptable_extensions = [
        # Video (Exhaustive)
        '.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv', '.webm', '.m4v', 
        '.mpg', '.mpeg', '.3gp', '.ts', '.mts', '.m2ts', '.vob', '.ogv', 
        '.qt', '.rm', '.rmvb', '.asf', '.amv', '.m4p', '.mpe', '.mpv', 
        '.m2v', '.svi', '.3g2', '.mxf', '.roq', '.nsv', '.f4v', '.f4p', '.f4a', '.f4b',
        
        # Image (Exhaustive)
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.tiff', '.tif',
        '.ico', '.heic', '.heif', '.raw', '.cr2', '.nef', '.orf', '.sr2', 
        '.psd', '.ai', '.eps', '.indd', '.cdr', '.xcf',
        
        # Audio
        '.mp3', '.wav', '.aac', '.flac', '.ogg', '.m4a',
        # Archives
        '.zip', '.rar', '.7z', '.tar', '.gz',
        # Documents
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt'
    ]
    
    # Use a session for better connection handling
    session = requests.Session()
    
    # Full browser headers to bypass strict server checks
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
    }
    session.headers.update(headers)
    
    # Add age verification cookie
    session.cookies.update({'justiceGovAgeVerified': 'true'})
    
    found_file = False
    for ext in acceptable_extensions:
        candidate_link = base_link + ext
        # print(f"Checking: {candidate_link}") 
        
        try:
            # Use stream=True to check headers without downloading body immediately
            response = session.get(candidate_link, stream=True)
            
            if response.status_code == 200:
                # Read the first chunk to check content
                # We use a generator to process the iterator safely
                content_iterator = response.iter_content(chunk_size=8192)
                try:
                    first_chunk = next(content_iterator)
                except StopIteration:
                    # Empty response
                    continue

                # Check if it matches the bad page marker OR starts with HTML
                # Safe assumption: Binary files (mp4, jpg, zip) rarely start with "<!DOCTYPE html" or "<html"
                first_chunk_start = first_chunk[:50].lower()
                
                if b'<!doctype html' in first_chunk_start or b'<html' in first_chunk_start or match_marker in first_chunk:
                    # Skip HTML/Soft 404
                    continue
                    
                # Found a valid file!
                print(f"Found match: {candidate_link}")
                local_filename = base_filename + ext
                
                # Check if we should overwrite? Defaulting to overwrite for now as script logic implies
                with open(local_filename, 'wb') as f:
                    f.write(first_chunk) # Write the chunk we already read
                    for chunk in content_iterator:
                        f.write(chunk)
                print(f"File downloaded: {local_filename}")
                found_file = True
                break # Stop looking for other extensions for this link
                
        except Exception as e:
            print(f"Error checking {candidate_link}: {e}")
    
    if not found_file:
        print(f"No valid file found for base: {base_link}")
        with file_lock:
            with open("missing_files.txt", "a") as f:
                f.write(f"{link}\n")

# Define the path to the html folder
html_folder = os.path.join(os.path.dirname(__file__), 'html')

# Find all files matching p*.htm* in the html folder
files = glob.glob(os.path.join(html_folder, 'p*.htm*'))

for file_path in files:
    print(f"Processing file: {file_path}")
    # Load the HTML content
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        continue

    # Parse the HTML using BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')

    links_to_process = []
    # Find all div elements with class "result-item"
    for div in soup.find_all('div', {'class': 'result-item'}):
        # Find the anchor tag (href attribute contains the link)
        a_tag = div.find('a')
        if a_tag:
            link = a_tag.get('href')
            if link:
                links_to_process.append(link)
    
    # Process links in parallel
    # Reducing max_workers slightly to be polite given we are downloading larger files now
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(process_link, links_to_process)
