import requests
import os

def test_link():
    link = input("Enter the link to test (e.g., https://example.com/file.pdf): ").strip()
    if not link:
        print("No link provided.")
        return

    print(f"Testing link: {link}")
    
    # Extract the filename from the link
    filename = os.path.basename(link)
    
    # Extract the base of the link (remove extension if present)
    base_link, _ = os.path.splitext(link)
    base_filename, _ = os.path.splitext(filename)
    
    # Extensions to brute-force check (Matches import requests.py)
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
    # Load examplebad.htm content for comparison
    bad_html_path = os.path.join(os.path.dirname(__file__), 'html', 'examplebad.htm')
    bad_page_content = b""
    try:
        with open(bad_html_path, 'rb') as f:
            bad_page_content = f.read()
            # We'll use a significant chunk for comparison, or specific markers
            # For robustness, let's look for the specific title tag which is unique to the Not Found page
            # <title> Department of Justice |  Page not found</title>
            match_marker = b"<title> Department of Justice |  Page not found</title>"
    except Exception as e:
        print(f"Warning: Could not load examplebad.htm: {e}")
        match_marker = b"Page not found" # Fallback

    found_file = False
    
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

    for ext in acceptable_extensions:
        candidate_link = base_link + ext
        print(f"Checking: {candidate_link}...", end=" ")
        
        try:
            # Use stream=True to check headers without downloading body immediately
            response = session.get(candidate_link, stream=True)
            
            print(f"[{response.status_code}]", end=" ")
            
            if response.status_code == 200:
                # Read the first chunk to check content
                # We use a generator to process the iterator safely
                content_iterator = response.iter_content(chunk_size=8192)
                try:
                    first_chunk = next(content_iterator)
                except StopIteration:
                    print("  -> Empty response.")
                    continue

                # Check if it matches the bad page marker
                if match_marker in first_chunk:
                    print(f"  -> Match 'examplebad.htm' content (Soft 404). Skip.")
                    continue
                
                # If we get here, it's NOT the bad page
                # Found a valid file!
                print(f"  -> FOUND MATCH!")
                
                content_length = response.headers.get('Content-Length')
                print(f"  -> Content-Length header: {content_length}")
                
                local_filename = "TEST_" + base_filename + ext
                
                print(f"  -> Downloading to {local_filename}...")
                total_bytes = 0
                with open(local_filename, 'wb') as f:
                    f.write(first_chunk) # Write the chunk we already read
                    total_bytes += len(first_chunk)
                    
                    for chunk in content_iterator:
                        f.write(chunk)
                        total_bytes += len(chunk)
                        
                print(f"  -> Download complete. Total bytes written: {total_bytes}")
                found_file = True
                break # Stop looking after finding one match
            else:
                print("") # Newline for non-200 responses
                
        except Exception as e:
            print(f"\n  -> Error: {e}")
    
    if not found_file:
        print(f"\nNo valid file found for base: {base_link}")

if __name__ == "__main__":
    test_link()
