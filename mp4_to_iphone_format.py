import subprocess
import sys
import os
from pathlib import Path

def convert_to_iphone_format(input_file, output_file=None):
    """
    Convert MP4 video to iPhone-compatible format.
    
    Args:
        input_file: Path to input MP4 file
        output_file: Path to output file (optional, will auto-generate if not provided)
    """
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found")
        return False
    
    # Generate output filename if not provided
    if output_file is None:
        input_path = Path(input_file)
        output_file = str(input_path.parent / f"{input_path.stem}_iphone{input_path.suffix}")
    
    # FFmpeg command for iPhone-compatible video
    # H.264 codec with AAC audio, optimized for iOS devices
    command = [
        'ffmpeg',
        '-i', input_file,
        '-c:v', 'libx264',           # H.264 video codec
        '-preset', 'medium',          # Encoding speed/quality tradeoff
        '-crf', '23',                 # Quality (lower = better, 18-28 is good range)
        '-profile:v', 'high',         # H.264 profile
        '-level', '4.0',              # H.264 level
        '-pix_fmt', 'yuv420p',        # Pixel format compatible with iPhone
        '-c:a', 'aac',                # AAC audio codec
        '-b:a', '128k',               # Audio bitrate
        '-movflags', '+faststart',    # Enable fast start for web/streaming
        '-y',                         # Overwrite output file if exists
        output_file
    ]
    
    print(f"Converting: {input_file}")
    print(f"Output: {output_file}")
    print("This may take a while depending on video size...")
    
    try:
        # Run FFmpeg
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode == 0:
            print(f"\n✓ Conversion successful!")
            print(f"Output saved to: {output_file}")
            return True
        else:
            print(f"\n✗ Conversion failed!")
            print(f"Error: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("\n✗ Error: FFmpeg not found!")
        print("Please install FFmpeg:")
        print("  - Mac: brew install ffmpeg")
        print("  - Ubuntu/Debian: sudo apt-get install ffmpeg")
        print("  - Windows: Download from https://ffmpeg.org/download.html")
        return False
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py input_video.mp4 [output_video.mp4]")
        print("\nExample:")
        print("  python script.py video.mp4")
        print("  python script.py video.mp4 output.mp4")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    convert_to_iphone_format(input_file, output_file)

if __name__ == "__main__":
    main()