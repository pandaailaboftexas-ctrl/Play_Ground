#!/usr/bin/env python3
"""
Video Downloader for MacBook
Simple script to download videos for local viewing
"""

import subprocess
import sys
import os
import re
import random
from urllib.parse import urlparse

def check_dependencies():
    """Check if required tools are installed"""
    missing = []
    
    try:
        subprocess.run(['yt-dlp', '--version'], 
                      capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        missing.append('yt-dlp')
    
    try:
        subprocess.run(['ffmpeg', '-version'], 
                      capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        missing.append('ffmpeg')
    
    return missing

def install_ytdlp():
    """Install yt-dlp"""
    print("Installing yt-dlp...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-U', 'yt-dlp'], 
                      capture_output=True, check=True)
        return True
    except:
        return False

def get_download_folder():
    """Get Downloads folder path"""
    downloads_path = os.path.join(os.path.expanduser('~'), 'Downloads')
    os.makedirs(downloads_path, exist_ok=True)
    return downloads_path

def generate_random_filename():
    """Generate random numeric filename"""
    return str(random.randint(100000000, 999999999))

def extract_embedded_video(url):
    """Try to extract embedded video source from page"""
    try:
        import urllib.request
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
            patterns = [
                r'https?://[^"\s<>]*\.m3u8[^"\s<>]*',
                r'https?://[^"\s<>]*\.mp4[^"\s<>]*',
                r'player\.vod\.com[^"\']*',
                r'iframe.*?src=["\'](https?://[^"\']+)',
                r'"url":\s*"([^"]+\.m3u8[^"]*)"',
                r'"url":\s*"([^"]+\.mp4[^"]*)"',
            ]
            
            found_urls = []
            for pattern in patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                found_urls.extend(matches)
            
            if found_urls:
                cleaned_urls = []
                for url in found_urls:
                    cleaned = url.replace('\\/', '/').replace('\\"', '"')
                    cleaned = cleaned.strip('"\'')
                    if cleaned not in cleaned_urls:
                        cleaned_urls.append(cleaned)
                return cleaned_urls
            
    except Exception:
        pass
    
    return []

def download_video_direct(video_url, output_path):
    """Download video directly using ffmpeg"""
    cmd = [
        'ffmpeg',
        '-user_agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        '-headers', f'Referer: {video_url}',
        '-i', video_url,
        '-c', 'copy',
        '-bsf:a', 'aac_adtstoasc',
        output_path,
        '-y',
        '-loglevel', 'error',
        '-stats'
    ]
    
    try:
        subprocess.run(cmd, check=True)
        return True
    except:
        return False

def download_with_ytdlp(url):
    """Download video using yt-dlp with progress bar"""
    try:
        downloads_dir = get_download_folder()
        random_name = generate_random_filename()
        output_template = os.path.join(downloads_dir, f'{random_name}.%(ext)s')
        
        print("Downloading...")
        
        cmd = [
            'yt-dlp',
            '-f', 'best',
            '--merge-output-format', 'mp4',
            '-o', output_template,
            '--newline',
            '--no-warnings',
            '--no-playlist',
            '--progress',
            '--user-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            '--referer', url,
            '--all-subs',
            '--embed-subs',
            url
        ]
        
        result = subprocess.run(cmd)
        
        if result.returncode == 0:
            cmd_filename = [
                'yt-dlp',
                '--get-filename',
                '-o', output_template,
                '--quiet',
                url
            ]
            filename_result = subprocess.run(cmd_filename, capture_output=True, text=True)
            output_path = filename_result.stdout.strip()
            
            print(f"\n✓ Saved to: {output_path}")
            subprocess.run(['open', '-R', output_path])
            return True
        
        return False
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Main function"""
    print("Video Downloader\n")
    
    # Check dependencies
    missing = check_dependencies()
    if 'yt-dlp' in missing:
        print("yt-dlp not installed.")
        response = input("Install now? (y/n): ").lower()
        if response == 'y':
            if not install_ytdlp():
                print("Error: Install manually with: pip install yt-dlp")
                sys.exit(1)
        else:
            print("Error: yt-dlp is required")
            sys.exit(1)
    
    if 'ffmpeg' in missing:
        print("Error: ffmpeg not installed. Install with: brew install ffmpeg")
        sys.exit(1)
    
    # Get URL
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("Video URL: ").strip()
    
    if not url:
        print("Error: No URL provided")
        sys.exit(1)
    
    print()
    
    # Try downloading
    success = download_with_ytdlp(url)
    
    if not success:
        print("\nTrying alternative method...")
        video_sources = extract_embedded_video(url)
        
        if video_sources:
            downloads_dir = get_download_folder()
            random_name = generate_random_filename()
            output_path = os.path.join(downloads_dir, f'{random_name}.mp4')
            
            if download_video_direct(video_sources[0], output_path):
                print(f"\n✓ Saved to: {output_path}")
                subprocess.run(['open', '-R', output_path])
                success = True
        
        if not success:
            print("\nUnable to download. Try:")
            print("  • Screen capture (Cmd+Shift+5)")
            print("  • Browser extensions")
            print("  • Check for download button on site")
    
    if success:
        print("\nDone!\n")

if __name__ == "__main__":
    main()