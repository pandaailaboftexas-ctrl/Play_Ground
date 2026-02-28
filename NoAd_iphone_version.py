#!/usr/bin/env python3
"""
iPhone-Compatible Video Downloader
Downloads videos in iPhone-friendly format (H.264 + AAC in MP4)
"""

import subprocess
import sys
import os
from pathlib import Path

def check_ytdlp():
    """Check if yt-dlp is installed"""
    try:
        subprocess.run(['yt-dlp', '--version'], 
                      capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_ytdlp():
    """Try to install yt-dlp"""
    print("📦 Installing yt-dlp...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'yt-dlp'], 
                      check=True)
        print("✅ yt-dlp installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install yt-dlp. Please run: pip install yt-dlp")
        return False

def get_download_folder():
    """Get the user's Downloads folder path"""
    if sys.platform == 'darwin':  # macOS
        downloads_path = os.path.join(os.path.expanduser('~'), 'Downloads')
    elif sys.platform == 'win32':  # Windows
        downloads_path = os.path.join(os.path.expanduser('~'), 'Downloads')
    else:  # Linux
        downloads_path = os.path.join(os.path.expanduser('~'), 'Downloads')
    
    # Create folder if it doesn't exist
    os.makedirs(downloads_path, exist_ok=True)
    return downloads_path

def get_video_info(url):
    """Get video information"""
    try:
        cmd = ['yt-dlp', '--get-title', '--get-duration', url]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')
        return {'title': lines[0] if lines else 'Unknown', 
                'duration': lines[1] if len(lines) > 1 else 'Unknown'}
    except:
        return {'title': 'Unknown', 'duration': 'Unknown'}

def download_for_iphone(url, quality='720'):
    """Download video in iPhone-compatible format (H.264 + AAC)"""
    try:
        print("\n" + "🔍 " + "Fetching video information...")
        info = get_video_info(url)
        print(f"✅ Video: {info['title']}")
        print(f"⏱️  Duration: {info['duration']}")
        print(f"📁 Download location: {get_download_folder()}")
        print(f"🎬 Quality: {quality}p")
        print(f"📱 Format: iPhone-compatible (H.264 + AAC)")
        
        print("\n" + "="*60)
        print("📥 Starting download (ad-free)...")
        print("="*60 + "\n")
        
        # Use Downloads folder
        downloads_dir = get_download_folder()
        output_template = os.path.join(downloads_dir, '%(title)s.%(ext)s')
        
        # Download and convert to iPhone-compatible format
        # Use a more flexible format selection that works with all videos
        cmd = [
            'yt-dlp',
            '-f', f'bv*[height<={quality}]+ba/b[height<={quality}]/bv*+ba/b',
            '--merge-output-format', 'mp4',
            # Force H.264 video codec and AAC audio codec (iPhone compatible)
            '--recode-video', 'mp4',
            '--postprocessor-args', 'ffmpeg:-c:v libx264 -preset fast -crf 22 -c:a aac -b:a 128k -movflags +faststart',
            '-o', output_template,
            '--progress',
            '--console-title',
            '--no-warnings',
            url
        ]
        
        # Run without capturing output so progress is shown
        result = subprocess.run(cmd, check=True)
        
        # Get the actual filename
        cmd_get_filename = [
            'yt-dlp',
            '--get-filename',
            '-o', output_template,
            url
        ]
        filename_result = subprocess.run(cmd_get_filename, capture_output=True, text=True, check=True)
        output_path = filename_result.stdout.strip()
        
        print("\n" + "="*60)
        print("✅ Download complete!")
        print("="*60)
        print(f"📂 Saved to: {output_path}")
        print(f"\n📱 iPhone Transfer Instructions:")
        print("   1. Connect your iPhone to your computer")
        print("   2. Open iTunes or Finder (macOS Catalina+)")
        print("   3. Drag the video file to your iPhone's Files app")
        print("   Or use AirDrop on macOS:")
        print("   1. Right-click the file")
        print("   2. Select 'Share' → 'AirDrop'")
        print("   3. Choose your iPhone")
        
        # Open folder containing the file
        print("\n🗂️  Opening download folder...")
        if sys.platform == 'win32':
            subprocess.run(['explorer', '/select,', output_path])
        elif sys.platform == 'darwin':  # macOS
            subprocess.run(['open', '-R', output_path])
        else:  # Linux
            subprocess.run(['xdg-open', downloads_dir])
        
        print("✨ Video is ready for your iPhone!\n")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error occurred: {e}")
        print("💡 Tip: Make sure the URL is valid and ffmpeg is installed")
        return False
    except KeyboardInterrupt:
        print("\n\n⏹️  Download cancelled by user")
        return False

def main():
    """Main function"""
    print("\n" + "="*60)
    print("📱 iPhone Video Downloader")
    print("="*60 + "\n")
    
    # Check and install yt-dlp if needed
    if not check_ytdlp():
        print("⚠️  yt-dlp is not installed.")
        response = input("📦 Would you like to install it now? (y/n): ").lower()
        if response == 'y':
            if not install_ytdlp():
                sys.exit(1)
        else:
            print("❌ yt-dlp is required. Please install: pip install yt-dlp")
            sys.exit(1)
    
    print("✅ yt-dlp is ready!\n")
    
    # Get video URL
    if len(sys.argv) > 1:
        url = sys.argv[1]
        print(f"🔗 URL: {url}\n")
    else:
        url = input("🔗 Enter video URL (YouTube, etc.): ").strip()
    
    if not url:
        print("❌ No URL provided. Exiting.")
        sys.exit(1)
    
    # Get quality preference
    print()
    quality = input("🎯 Max quality (360/480/720/1080) [default: 720]: ").strip()
    quality = quality if quality in ['360', '480', '720', '1080'] else '720'
    download_for_iphone(url, quality)
    
    print("\n" + "="*60)
    print("🎉 Done! Transfer to your iPhone and enjoy!")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()