#!/usr/bin/env python3
"""
视频下载器 - 支持 huavod.top 等视频网站
使用说明：python3 downloader.py "视频页面URL"
"""

import subprocess
import sys
import os
import re
import random
import json
import http.cookiejar
from urllib.parse import urlparse, urljoin

def check_dependencies():
    """检查依赖是否安装"""
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
    """安装 yt-dlp"""
    print("正在安装 yt-dlp...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-U', 'yt-dlp'], 
                      check=True)
        return True
    except:
        return False

def get_download_folder():
    """获取下载文件夹路径"""
    downloads_path = os.path.join(os.path.expanduser('~'), 'Downloads', 'Videos')
    os.makedirs(downloads_path, exist_ok=True)
    return downloads_path

def generate_filename(url):
    """根据URL生成文件名"""
    parsed = urlparse(url)
    path_parts = parsed.path.strip('/').split('/')
    
    if path_parts:
        base_name = path_parts[-1].replace('.html', '')
        base_name = re.sub(r'[^\w\-]', '_', base_name)
        return base_name
    
    return str(random.randint(100000000, 999999999))

def extract_video_with_browser_cookies(url):
    """使用浏览器 cookies 提取视频源"""
    try:
        import urllib.request
        import ssl
        
        # 创建 cookie 处理器
        cookie_jar = http.cookiejar.CookieJar()
        
        # 创建支持 cookies 和 SSL 的 opener
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(cookie_jar),
            urllib.request.HTTPSHandler(context=context)
        )
        
        # 设置请求头
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        print("正在访问页面（可能需要等待验证）...")
        
        # 第一次请求，可能会被重定向到验证页
        req = urllib.request.Request(url, headers=headers)
        try:
            response = opener.open(req, timeout=30)
            html = response.read()
            
            # 尝试解码
            try:
                html = html.decode('utf-8')
            except:
                html = html.decode('gbk', errors='ignore')
            
            # 检查是否有验证页面
            if 'verify' in response.geturl().lower() or '验证' in html:
                print("检测到验证页面，尝试自动通过...")
                
                # 等待几秒
                import time
                time.sleep(3)
                
                # 再次请求原始 URL
                req = urllib.request.Request(url, headers=headers)
                response = opener.open(req, timeout=30)
                html = response.read()
                try:
                    html = html.decode('utf-8')
                except:
                    html = html.decode('gbk', errors='ignore')
            
            print("正在分析页面...")
            
            # 查找视频源
            video_sources = []
            
            # 多种匹配模式
            patterns = [
                # m3u8
                r'https?://[^"\s<>\']+\.m3u8[^"\s<>\']*',
                r'"url":\s*"([^"]+\.m3u8[^"]*)"',
                r"'url':\s*'([^']+\.m3u8[^']*)'",
                r'url:\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
                
                # mp4
                r'https?://[^"\s<>\']+\.mp4[^"\s<>\']*',
                r'"url":\s*"([^"]+\.mp4[^"]*)"',
                r"'url':\s*'([^']+\.mp4[^']*)'",
                r'url:\s*["\']([^"\']+\.mp4[^"\']*)["\']',
                
                # 常见播放器配置
                r'player_aaaa\s*=\s*({[^}]+})',
                r'var\s+player[^=]*=\s*({.+?});',
                
                # iframe
                r'<iframe[^>]+src=["\'](https?://[^"\']+)["\']',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
                for match in matches:
                    if match.strip().startswith('{'):
                        try:
                            data = json.loads(match)
                            if 'url' in data:
                                video_sources.append(data['url'])
                        except:
                            pass
                    else:
                        cleaned = match.replace('\\/', '/').replace('\\"', '"').strip('"\'')
                        if cleaned.startswith('http') and ('m3u8' in cleaned or 'mp4' in cleaned):
                            video_sources.append(cleaned)
            
            # 去重
            video_sources = list(dict.fromkeys(video_sources))
            
            return video_sources
            
        except Exception as e:
            print(f"访问错误: {e}")
            return []
            
    except Exception as e:
        print(f"提取错误: {e}")
        return []

def download_with_ytdlp(url, video_url=None, use_cookies=False):
    """使用 yt-dlp 下载视频"""
    try:
        downloads_dir = get_download_folder()
        filename = generate_filename(url)
        output_template = os.path.join(downloads_dir, f'{filename}.%(ext)s')
        
        target_url = video_url if video_url else url
        
        print(f"\n开始下载...")
        print(f"目标: {target_url[:80]}...\n")
        
        cmd = [
            'yt-dlp',
            '-f', 'best',
            '--merge-output-format', 'mp4',
            '-o', output_template,
            '--no-warnings',
            '--no-playlist',
            '--user-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            '--referer', url,
            '--add-header', 'Accept:*/*',
            '--add-header', 'Accept-Language:zh-CN,zh;q=0.9',
            '--retries', '10',
            '--fragment-retries', '10',
            '--progress',
            '--newline'
        ]
        
        # 如果需要使用浏览器 cookies（会触发钥匙串授权）
        if use_cookies:
            print("⚠️  即将访问浏览器 cookies，macOS 会请求钥匙串授权...")
            # 尝试从不同浏览器读取 cookies
            for browser in ['chrome', 'firefox', 'safari', 'edge']:
                cmd.extend(['--cookies-from-browser', browser])
                break
        
        cmd.extend(['--all-subs', '--embed-subs', target_url])
        
        result = subprocess.run(cmd)
        
        if result.returncode == 0:
            for file in os.listdir(downloads_dir):
                if file.startswith(filename):
                    output_path = os.path.join(downloads_dir, file)
                    print(f"\n✓ 下载完成！")
                    print(f"保存位置: {output_path}")
                    subprocess.run(['open', '-R', output_path], stderr=subprocess.DEVNULL)
                    return True
        
        return False
        
    except Exception as e:
        print(f"下载错误: {e}")
        return False

def download_with_ffmpeg(video_url, url, filename):
    """使用 ffmpeg 直接下载"""
    downloads_dir = get_download_folder()
    output_path = os.path.join(downloads_dir, f'{filename}.mp4')
    
    print(f"\n使用 ffmpeg 下载...")
    print(f"源: {video_url[:80]}...\n")
    
    cmd = [
        'ffmpeg',
        '-user_agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        '-headers', f'Referer: {url}\r\n',
        '-i', video_url,
        '-c', 'copy',
        '-bsf:a', 'aac_adtstoasc',
        '-y',
        output_path,
        '-loglevel', 'warning',
        '-stats'
    ]
    
    try:
        result = subprocess.run(cmd)
        if result.returncode == 0 and os.path.exists(output_path):
            print(f"\n✓ 下载完成！")
            print(f"保存位置: {output_path}")
            subprocess.run(['open', '-R', output_path], stderr=subprocess.DEVNULL)
            return True
    except Exception as e:
        print(f"FFmpeg 错误: {e}")
    
    return False

def interactive_browser_method():
    """交互式浏览器方法"""
    print("\n" + "=" * 60)
    print("手动获取视频源方法:")
    print("=" * 60)
    print("\n步骤:")
    print("1. 在浏览器中打开视频页面并播放视频")
    print("2. 按 F12 打开开发者工具")
    print("3. 切换到 'Network' (网络) 标签")
    print("4. 在过滤框中输入: m3u8 或 mp4")
    print("5. 找到视频文件，右键复制链接")
    print("6. 将链接粘贴到这里\n")
    
    video_url = input("请输入视频源地址 (直接回车跳过): ").strip()
    
    if video_url:
        return video_url
    
    return None

def main():
    """主函数"""
    print("=" * 60)
    print("视频下载器 - huavod.top 专用版")
    print("=" * 60)
    
    # 检查依赖
    missing = check_dependencies()
    if 'yt-dlp' in missing:
        print("\n⚠ yt-dlp 未安装")
        response = input("是否现在安装? (y/n): ").lower()
        if response == 'y':
            if not install_ytdlp():
                print("安装失败！请手动安装: pip3 install yt-dlp")
                sys.exit(1)
            print("安装成功！")
        else:
            print("需要 yt-dlp 才能运行")
            sys.exit(1)
    
    if 'ffmpeg' in missing:
        print("\n⚠ ffmpeg 未安装")
        print("请安装: brew install ffmpeg")
        sys.exit(1)
    
    # 获取URL
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        print("\n请输入视频页面地址:")
        url = input("URL: ").strip()
    
    if not url:
        print("错误: 未提供URL")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    
    success = False
    
    # 询问是否使用浏览器 cookies
    print("\n是否使用浏览器 cookies？")
    print("  - 优点: 可以访问需要登录的内容")
    print("  - 缺点: macOS 会弹出钥匙串授权请求")
    use_cookies_choice = input("使用浏览器 cookies? (y/n，默认 n): ").lower().strip()
    use_cookies = use_cookies_choice == 'y'
    
    # 方法1: 直接下载
    if use_cookies:
        print("\n[方法1] 使用浏览器会话下载...")
        success = download_with_ytdlp(url, use_cookies=True)
    else:
        print("\n[方法1] 尝试直接下载...")
        success = download_with_ytdlp(url, use_cookies=False)
    
    if not success:
        # 方法2: 提取视频源
        print("\n[方法2] 尝试提取视频源...")
        video_sources = extract_video_with_browser_cookies(url)
        
        if video_sources:
            print(f"\n找到 {len(video_sources)} 个视频源:")
            for i, src in enumerate(video_sources, 1):
                print(f"  {i}. {src[:80]}...")
            
            filename = generate_filename(url)
            for i, video_url in enumerate(video_sources, 1):
                print(f"\n尝试源 {i}/{len(video_sources)}...")
                
                if download_with_ytdlp(url, video_url, use_cookies=False):
                    success = True
                    break
                
                if download_with_ffmpeg(video_url, url, filename):
                    success = True
                    break
    
    if not success:
        # 方法3: 手动输入视频源
        video_url = interactive_browser_method()
        
        if video_url:
            filename = generate_filename(url)
            
            print("\n尝试下载手动提供的视频源...")
            if download_with_ytdlp(url, video_url, use_cookies=False):
                success = True
            elif download_with_ffmpeg(video_url, url, filename):
                success = True
    
    if not success:
        print("\n" + "=" * 60)
        print("下载失败！")
        print("=" * 60)
        print("\n可能原因:")
        print("  • 网站有访客验证保护")
        print("  • 需要登录账号")
        print("  • 视频源加密或有防护")
        print("\n推荐方案:")
        print("  1. 先在浏览器中正常访问并播放视频")
        print("  2. 然后使用上面的手动方法获取视频源")
        print("  3. 或使用屏幕录制 (Cmd+Shift+5)")
        print("  4. 或使用浏览器扩展 (Video DownloadHelper)")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("任务完成！")
        print("=" * 60)

if __name__ == "__main__":
    main()