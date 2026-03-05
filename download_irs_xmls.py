"""
IRS Form 990 XML Files Downloader
Automatically detects and downloads ZIP files from the IRS and extracts them to organized folders.
Organizes files by year with separate folders for zips and extracted files.
"""

import os
import requests
import zipfile
from pathlib import Path
from typing import List, Optional, Dict
import time

class IRSXMLDownloader:
    BASE_URL = "https://apps.irs.gov/pub/epostcard/990/xml"
    
    def __init__(self, base_dir: str = "."):
        """
        Initialize the downloader.
        
        Args:
            base_dir: Base directory where files will be downloaded (default: current directory)
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def detect_available_batches(self, year: int, max_batches: int = 15) -> List[str]:
        """
        Auto-detect available batches for a year by probing URLs.
        Handles different URL formats for different year ranges.
        
        Args:
            year: Year to check
            max_batches: Maximum batches to check
            
        Returns:
            List of available batch codes
        """
        available = []
        
        if year <= 2020:
            # 2019-2020 use different format: download990xml_YEAR_1.zip through _8.zip
            # Also try TEOS_XML_C1.zip format
            
            # Try download990xml format (download990xml_2020_1.zip)
            for num in range(1, 10):
                batch_code = f"download990xml_{year}_{num}"
                url = f"{self.BASE_URL}/{year}/{batch_code}.zip"
                if self._url_exists(url):
                    available.append(batch_code)
            
            # Try TEOS_XML_C format (TEOS_XML_C1.zip)
            for num in range(1, 10):
                batch_code = f"TEOS_XML_C{num}"
                url = self.build_url(year, batch_code)
                if self._url_exists(url):
                    available.append(batch_code)
        else:
            # 2021+ use standard format: TEOS_XML_01A.zip
            # Test standard batches (01A-12A)
            for month in range(1, 13):
                batch = f"{month:02d}A"
                url = self.build_url(year, batch)
                if self._url_exists(url):
                    available.append(batch)
            
            # Test sub-batches for months that might have B, C variants
            for month in range(1, 13):
                for variant in ['B', 'C', 'D', 'E']:
                    batch = f"{month:02d}{variant}"
                    url = self.build_url(year, batch)
                    if self._url_exists(url):
                        available.append(batch)
        
        return sorted(available)
    
    def _url_exists(self, url: str) -> bool:
        """
        Check if a URL exists without downloading the full file.
        
        Args:
            url: URL to check
            
        Returns:
            True if URL returns 200, False otherwise
        """
        try:
            response = self.session.head(url, timeout=5, allow_redirects=True)
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def build_url(self, year: int, batch: str) -> str:
        """Build download URL for a specific year and batch."""
        return f"{self.BASE_URL}/{year}/{year}_TEOS_XML_{batch}.zip"
    
    def download_file(self, url: str, filepath: Path, retries: int = 3) -> bool:
        """
        Download a file with retry logic.
        
        Args:
            url: URL to download from
            filepath: Path where file will be saved
            retries: Number of retry attempts
            
        Returns:
            True if successful, False otherwise
        """
        for attempt in range(retries):
            try:
                print(f"Downloading: {url}")
                response = self.session.get(url, timeout=30, stream=True)
                response.raise_for_status()
                
                # Get total file size
                total_size = int(response.headers.get('content-length', 0))
                
                # Download with progress
                with open(filepath, 'wb') as f:
                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size:
                                percent = (downloaded / total_size) * 100
                                print(f"  Progress: {percent:.1f}%", end='\r')
                
                print(f"\n✓ Downloaded: {filepath.name}")
                return True
                
            except requests.RequestException as e:
                attempt_num = attempt + 1
                print(f"✗ Attempt {attempt_num}/{retries} failed: {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
        
        return False
    
    def extract_zip(self, zip_path: Path, extract_dir: Path) -> bool:
        """
        Extract ZIP file to destination directory.
        
        Args:
            zip_path: Path to ZIP file
            extract_dir: Directory to extract to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            extract_dir.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            print(f"✓ Extracted to: {extract_dir}")
            return True
        except Exception as e:
            print(f"✗ Extraction failed: {e}")
            return False
    
    def download_batch(self, year: int, batch: str, keep_zip: bool = True) -> bool:
        """
        Download and extract a single batch.
        Handles different URL formats for different years.
        
        Args:
            year: Year (e.g., 2025)
            batch: Batch code (e.g., '01A', '02B', 'download990xml_2020_1')
            keep_zip: Whether to keep the ZIP file after extraction
            
        Returns:
            True if successful, False otherwise
        """
        # Create folder structure: XMLs/2025/zips and XMLs/2025/extracted
        year_dir = self.base_dir / "XMLs" / str(year)
        zips_dir = year_dir / "zips"
        extracted_dir = year_dir / "extracted"
        
        zips_dir.mkdir(parents=True, exist_ok=True)
        extracted_dir.mkdir(parents=True, exist_ok=True)
        
        # Build URL based on batch format
        if batch.startswith("download990xml"):
            # Old format: download990xml_2020_1
            url = f"{self.BASE_URL}/{year}/{batch}.zip"
            zip_filename = f"{batch}.zip"
            extract_folder_name = batch
        else:
            # Standard format: TEOS_XML_01A or TEOS_XML_C1
            url = self.build_url(year, batch)
            zip_filename = f"{year}_TEOS_XML_{batch}.zip"
            extract_folder_name = f"{year}_TEOS_XML_{batch}"
        
        zip_path = zips_dir / zip_filename
        
        if not self.download_file(url, zip_path):
            return False
        
        # Extract to extracted folder
        extract_target = extracted_dir / extract_folder_name
        if not self.extract_zip(zip_path, extract_target):
            return False
        
        # Clean up ZIP if requested
        if not keep_zip:
            zip_path.unlink()
            print(f"  Removed ZIP file")
        
        return True
    
    def download_multiple_batches(self, year: int, batches: List[str], 
                                 keep_zip: bool = True) -> dict:
        """
        Download multiple batches for a year.
        
        Args:
            year: Year to download
            batches: List of batch codes (e.g., ['01A', '02A', '03A'])
            keep_zip: Whether to keep ZIP files
            
        Returns:
            Dictionary with results for each batch
        """
        results = {}
        total = len(batches)
        
        print(f"\n{'='*60}")
        print(f"Downloading {total} batches for {year}")
        print(f"{'='*60}\n")
        
        for i, batch in enumerate(batches, 1):
            print(f"[{i}/{total}] Processing {year}_TEOS_XML_{batch}...")
            success = self.download_batch(year, batch, keep_zip)
            results[batch] = success
            if i < total:
                time.sleep(1)  # Be respectful to the server
        
        return results
    
    def print_summary(self, results: dict):
        """Print summary of download results."""
        successful = sum(1 for v in results.values() if v)
        total = len(results)
        
        print(f"\n{'='*60}")
        print(f"SUMMARY: {successful}/{total} batches downloaded successfully")
        print(f"{'='*60}")
        
        for batch, success in results.items():
            status = "✓" if success else "✗"
            print(f"{status} {batch}")


def main():
    """Main function - auto-detects and downloads specified years."""
    
    # Initialize downloader
    base_directory = r"D:\XMLs"
    downloader = IRSXMLDownloader(base_directory)
    
    
    # For single year: years = [2025]
    # For multiple years: years = [2025, 2024, 2023]
    # For all years: years = list(range(2019, 2027))  # 2019-2026
    years = list(range(2019, 2021))  # <<< Download all years 2019-2026
    # ================================================================
    
    print(f"\n{'='*70}")
    print(f"IRS XML DOWNLOADER - Processing Years: {years}")
    print(f"{'='*70}\n")
    
    # First, detect available batches for each year
    year_batches = {}
    print("STEP 1: Detecting available batches for each year...\n")
    
    for year in years:
        print(f"Scanning {year}...", end=" ", flush=True)
        batches = downloader.detect_available_batches(year)
        if batches:
            year_batches[year] = batches
            print(f"Found {len(batches)} batches: {', '.join(batches[:5])}{'...' if len(batches) > 5 else ''}")
        else:
            print("No batches found")
        time.sleep(0.5)  # Be respectful to server
    
    # Now download all detected batches
    print(f"\n{'='*70}")
    print("STEP 2: Downloading and extracting files...\n")
    print(f"{'='*70}\n")
    
    total_years = len(year_batches)
    for year_idx, (year, batches) in enumerate(sorted(year_batches.items(), reverse=True), 1):
        print(f"\n[{year_idx}/{total_years}] YEAR {year} ({len(batches)} batches)")
        print(f"{'-'*70}")
        
        results = downloader.download_multiple_batches(year, batches, keep_zip=True)
        
        successful = sum(1 for v in results.values() if v)
        print(f"\n  ✓ Year {year}: {successful}/{len(batches)} downloaded successfully")
    
    # Final summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    total_batches = sum(len(b) for b in year_batches.values())
    print(f"Total years processed: {total_years}")
    print(f"Total batches found: {total_batches}")
    print(f"\nFolder structure created:")
    print(f"  XMLs/")
    for year in sorted(year_batches.keys()):
        print(f"    {year}/")
        print(f"      zips/          (ZIP files kept for reference)")
        print(f"      extracted/     (Unzipped XML files)")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
