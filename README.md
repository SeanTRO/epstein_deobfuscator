# epstein_deobfuscator
Search for obfuscated files in the Epstein archive

## Features
* Searches through a list of links extracted from HTML files located in the `html` folder.
* Identifies and extracts relevant files with acceptable extensions (e.g., .mp4)

## Usage
* Run this script to automatically search through the provided HTML files, identify matching files, and download them locally.

**Important Notes:**

* To add new files, please search for "no images produced" in the Epstein Library website. Save the resulting HTML pages as `p[pagenumber].html` (e.g., `p1.html`, `p2.html`, etc.) and place them in the `html` folder.
* Be cautious: the government website may block you if you make too many requests. This script retains only the cookie needed to bypass the age filter, but occasional blocks are still possible. To mitigate this, consider using a VPN or hopping between IP addresses.
* If no file type is found for a link (i.e., it's not a valid download), the link will be added to `missing_files.txt` for later processing.

**Additional Information:**

* This script skips links that have already been processed, so you don't need to re-run it unnecessarily.