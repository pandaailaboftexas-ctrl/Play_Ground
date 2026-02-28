#!/usr/bin/env python3
"""
YouTube Ad-Free Player - Web Interface with Integrated Search
Uses yt-dlp for searching - more reliable!
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import subprocess
import shutil
import json
import webbrowser
import threading
import re

class YouTubeHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(self.get_html().encode())
        elif self.path == '/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            status = {
                'mpv': shutil.which('mpv') is not None,
                'iina': shutil.which('iina') is not None,
                'yt_dlp': shutil.which('yt-dlp') is not None,
                'brew': shutil.which('brew') is not None
            }
            self.wfile.write(json.dumps(status).encode())
        else:
            self.send_error(404)
    
    def do_POST(self):
        if self.path == '/play':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            
            query = data.get('query', '')
            player = data.get('player', 'auto')
            
            result = self.play_video(query, player)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        
        elif self.path == '/search':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            
            query = data.get('query', '')
            result = self.search_youtube(query)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
    
    def search_youtube(self, query):
        """Search YouTube using yt-dlp"""
        try:
            # Check if yt-dlp is available
            if not shutil.which('yt-dlp'):
                return {
                    'success': False,
                    'message': 'yt-dlp not installed. Install with: brew install yt-dlp',
                    'videos': []
                }
            
            # Use yt-dlp to search YouTube
            search_url = f"ytsearch12:{query}"
            
            cmd = [
                'yt-dlp',
                '--dump-json',
                '--no-playlist',
                '--flat-playlist',
                search_url
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode != 0:
                return {
                    'success': False,
                    'message': f'Search failed: {result.stderr}',
                    'videos': []
                }
            
            # Parse results
            videos = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                try:
                    video_data = json.loads(line)
                    video_id = video_data.get('id', '')
                    
                    videos.append({
                        'id': video_id,
                        'title': video_data.get('title', 'Unknown Title'),
                        'author': video_data.get('uploader', video_data.get('channel', 'Unknown Author')),
                        'duration': self.format_duration(video_data.get('duration', 0)),
                        'views': self.format_views(video_data.get('view_count', 0)),
                        'thumbnail': video_data.get('thumbnail', f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg"),
                        'url': f"https://youtube.com/watch?v={video_id}"
                    })
                except json.JSONDecodeError:
                    continue
            
            if videos:
                return {'success': True, 'videos': videos, 'source': 'yt-dlp'}
            else:
                return {
                    'success': False,
                    'message': 'No videos found',
                    'videos': []
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'message': 'Search timed out. Try again.',
                'videos': []
            }
        except Exception as e:
            return {
                'success': False,
                'message': str(e),
                'videos': []
            }
    
    def format_duration(self, seconds):
        """Format duration in seconds to MM:SS or HH:MM:SS"""
        if not seconds:
            return "Unknown"
        try:
            seconds = int(seconds)
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            if hours > 0:
                return f"{hours}:{minutes:02d}:{secs:02d}"
            return f"{minutes}:{secs:02d}"
        except:
            return "Unknown"
    
    def format_views(self, views):
        """Format view count"""
        try:
            if not views:
                return "Unknown views"
            views = int(views)
            if views >= 1000000000:
                return f"{views/1000000000:.1f}B views"
            elif views >= 1000000:
                return f"{views/1000000:.1f}M views"
            elif views >= 1000:
                return f"{views/1000:.1f}K views"
            return f"{views} views"
        except:
            return "Unknown views"
    
    def play_video(self, query, player):
        """Play video based on query and player selection"""
        try:
            has_mpv = shutil.which('mpv') is not None
            has_iina = shutil.which('iina') is not None
            has_yt_dlp = shutil.which('yt-dlp') is not None
            
            # Determine URL
            if query.startswith('http'):
                url = query
                is_url = True
            else:
                url = query
                is_url = False
            
            # Play based on selection
            if player == 'web' or not is_url:
                return self._play_web(query)
            elif player == 'mpv' or (player == 'auto' and has_mpv and has_yt_dlp):
                if not has_mpv or not has_yt_dlp:
                    return {'success': False, 'message': 'MPV or yt-dlp not installed'}
                return self._play_mpv(url)
            elif player == 'iina' or (player == 'auto' and has_iina and has_yt_dlp):
                if not has_iina or not has_yt_dlp:
                    return {'success': False, 'message': 'IINA or yt-dlp not installed'}
                return self._play_iina(url)
            else:
                return self._play_web(query)
                
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def _play_mpv(self, url):
        """Play with MPV"""
        subprocess.Popen([
            'mpv',
            '--no-terminal',
            '--force-window=immediate',
            '--ytdl-format=bestvideo[height<=1080]+bestaudio/best',
            url
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {'success': True, 'message': 'MPV player launched!', 'player': 'MPV'}
    
    def _play_iina(self, url):
        """Play with IINA"""
        subprocess.Popen(['iina', url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {'success': True, 'message': 'IINA player launched!', 'player': 'IINA'}
    
    def _play_web(self, query):
        """Play in web browser via Invidious"""
        if query.startswith('http'):
            if 'watch?v=' in query:
                video_id = query.split('watch?v=')[1].split('&')[0]
                url = f"https://yewtu.be/watch?v={video_id}"
            elif 'youtu.be/' in query:
                video_id = query.split('youtu.be/')[1].split('?')[0]
                url = f"https://yewtu.be/watch?v={video_id}"
            else:
                url = query
        else:
            encoded = urllib.parse.quote(query)
            url = f"https://yewtu.be/search?q={encoded}"
        
        webbrowser.open(url)
        return {'success': True, 'message': 'Browser opened!', 'player': 'Web', 'url': url}
    
    def get_html(self):
        """Return the HTML interface"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Ad-Free Player</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 1200px;
            width: 100%;
            margin: 0 auto;
        }
        
        h1 {
            color: #333;
            margin-bottom: 10px;
            text-align: center;
            font-size: 32px;
        }
        
        .subtitle {
            color: #666;
            text-align: center;
            margin-bottom: 30px;
            font-size: 14px;
        }
        
        .status {
            background: #f0f7ff;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            font-size: 13px;
        }
        
        .status-item {
            display: inline-block;
            margin-right: 15px;
            margin-bottom: 5px;
        }
        
        .status-ok { color: #00d4aa; font-weight: 600; }
        .status-error { color: #ff6b6b; font-weight: 600; }
        
        .search-section {
            margin-bottom: 30px;
        }
        
        .search-box {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .search-input {
            flex: 1;
            padding: 15px;
            border: 2px solid #ddd;
            border-radius: 10px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        
        .search-input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .search-btn {
            padding: 15px 30px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: background 0.3s;
            white-space: nowrap;
        }
        
        .search-btn:hover {
            background: #5568d3;
        }
        
        .search-btn:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        
        .results {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .video-card {
            background: #f8f9fa;
            border-radius: 12px;
            overflow: hidden;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .video-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.15);
        }
        
        .video-thumbnail {
            width: 100%;
            height: 180px;
            object-fit: cover;
            background: #e0e0e0;
        }
        
        .video-info {
            padding: 15px;
        }
        
        .video-title {
            font-weight: 600;
            color: #333;
            margin-bottom: 8px;
            font-size: 14px;
            line-height: 1.4;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }
        
        .video-meta {
            font-size: 12px;
            color: #666;
            margin-bottom: 4px;
        }
        
        .video-stats {
            font-size: 12px;
            color: #999;
        }
        
        .player-options {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        
        .radio-btn {
            flex: 1;
            min-width: 120px;
        }
        
        .radio-btn input[type="radio"] {
            display: none;
        }
        
        .radio-btn label {
            display: block;
            padding: 12px;
            background: #f5f5f5;
            border-radius: 8px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: 500;
            font-size: 13px;
        }
        
        .radio-btn input[type="radio"]:checked + label {
            background: #667eea;
            color: white;
        }
        
        .radio-btn label:hover {
            background: #e0e0e0;
        }
        
        .radio-btn input[type="radio"]:checked + label:hover {
            background: #5568d3;
        }
        
        .message {
            margin-top: 20px;
            padding: 15px;
            border-radius: 8px;
            font-size: 14px;
            display: none;
        }
        
        .message.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .message.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .message.warning {
            background: #fff3cd;
            color: #856404;
            border: 1px solid #ffeaa7;
        }
        
        .setup-info {
            margin-top: 20px;
            padding: 15px;
            background: #fff3cd;
            border-radius: 8px;
            font-size: 13px;
            line-height: 1.6;
        }
        
        .setup-info strong {
            color: #856404;
        }
        
        code {
            background: #f5f5f5;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Monaco', 'Courier New', monospace;
            font-size: 12px;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        
        .loading-spinner {
            display: inline-block;
            width: 40px;
            height: 40px;
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-bottom: 10px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .no-results {
            text-align: center;
            padding: 40px;
            color: #999;
        }
        
        .section-title {
            font-size: 18px;
            font-weight: 600;
            color: #333;
            margin-bottom: 15px;
        }
        
        .api-info {
            font-size: 11px;
            color: #999;
            text-align: right;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎬 YouTube Ad-Free Player</h1>
        <p class="subtitle">Search and watch YouTube videos without advertisements</p>
        
        <div class="status" id="status">
            <strong>System Status:</strong> <span id="status-text">Checking...</span>
        </div>
        
        <div class="search-section">
            <div class="search-box">
                <input 
                    type="text" 
                    id="searchInput" 
                    class="search-input"
                    placeholder="Search: 'funny cats' or paste URL: 'https://youtube.com/watch?v=...'"
                    autofocus
                >
                <button class="search-btn" id="searchBtn" onclick="handleSearch()">🔍 Search</button>
            </div>
        </div>
        
        <div id="resultsContainer" style="display: none;">
            <div class="section-title">Search Results:</div>
            <div class="results" id="results"></div>
            <div class="api-info" id="apiInfo"></div>
        </div>
        
        <div class="player-options">
            <div class="radio-btn">
                <input type="radio" id="auto" name="player" value="auto" checked>
                <label for="auto">🎯 Auto</label>
            </div>
            <div class="radio-btn">
                <input type="radio" id="mpv" name="player" value="mpv">
                <label for="mpv">🎥 MPV</label>
            </div>
            <div class="radio-btn">
                <input type="radio" id="iina" name="player" value="iina">
                <label for="iina">📺 IINA</label>
            </div>
            <div class="radio-btn">
                <input type="radio" id="web" name="player" value="web">
                <label for="web">🌐 Web</label>
            </div>
        </div>
        
        <div class="message" id="message"></div>
        
        <div class="setup-info" id="setupInfo" style="display: none;">
            <strong>⚙️ Setup Required for Search & Players:</strong><br>
            Install yt-dlp to enable search functionality:<br>
            <code>brew install yt-dlp</code><br><br>
            Optional players (choose one or both):<br>
            <code>brew install mpv</code><br>
            <code>brew install --cask iina</code><br><br>
            You can still paste YouTube URLs and use Web mode!
        </div>
    </div>

    <script>
        window.onload = function() {
            checkStatus();
            
            document.getElementById('searchInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    handleSearch();
                }
            });
        };
        
        function checkStatus() {
            fetch('/status')
                .then(r => r.json())
                .then(data => {
                    let status = [];
                    let hasPlayer = data.mpv || data.iina;
                    let canSearch = data.yt_dlp;
                    
                    if (data.mpv) status.push('<span class="status-ok">✓ MPV</span>');
                    else status.push('<span class="status-error">✗ MPV</span>');
                    
                    if (data.iina) status.push('<span class="status-ok">✓ IINA</span>');
                    else status.push('<span class="status-error">✗ IINA</span>');
                    
                    if (data.yt_dlp) status.push('<span class="status-ok">✓ yt-dlp</span>');
                    else status.push('<span class="status-error">✗ yt-dlp</span>');
                    
                    document.getElementById('status-text').innerHTML = status.join(' ');
                    
                    if (!canSearch || !hasPlayer) {
                        document.getElementById('setupInfo').style.display = 'block';
                        if (!canSearch) {
                            showMessage('⚠️ yt-dlp not installed. Search disabled. You can still paste URLs!', 'warning');
                        }
                    }
                });
        }
        
        function handleSearch() {
            const input = document.getElementById('searchInput').value.trim();
            if (!input) {
                showMessage('Please enter a search term or URL', 'error');
                return;
            }
            
            // Check if it's a URL
            if (input.startsWith('http://') || input.startsWith('https://')) {
                playVideo(input);
            } else {
                searchVideos();
            }
        }
        
        function searchVideos() {
            const query = document.getElementById('searchInput').value.trim();
            if (!query) {
                showMessage('Please enter a search term', 'error');
                return;
            }
            
            const resultsDiv = document.getElementById('results');
            const container = document.getElementById('resultsContainer');
            const btn = document.getElementById('searchBtn');
            
            btn.disabled = true;
            btn.textContent = '⏳ Searching...';
            
            resultsDiv.innerHTML = `
                <div class="loading">
                    <div class="loading-spinner"></div>
                    <div>🔍 Searching YouTube...</div>
                    <div style="font-size: 12px; margin-top: 10px; color: #999;">This may take 10-15 seconds</div>
                </div>
            `;
            container.style.display = 'block';
            hideMessage();
            
            fetch('/search', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({query})
            })
            .then(r => r.json())
            .then(data => {
                if (data.success && data.videos.length > 0) {
                    displayResults(data.videos);
                    document.getElementById('apiInfo').textContent = 
                        `Found ${data.videos.length} results using ${data.source}`;
                    showMessage('✅ Search completed!', 'success');
                } else {
                    resultsDiv.innerHTML = 
                        '<div class="no-results">😕 ' + 
                        (data.message || 'No videos found. Try a different search term.') +
                        '<br><br><small>You can still paste YouTube URLs directly!</small></div>';
                    if (data.message && data.message.includes('not installed')) {
                        showMessage('⚠️ ' + data.message, 'warning');
                    }
                }
            })
            .catch(err => {
                resultsDiv.innerHTML = 
                    '<div class="no-results">❌ Search failed: ' + err.message + 
                    '<br><br>Try pasting a YouTube URL directly instead!</div>';
                showMessage('❌ Search error: ' + err.message, 'error');
            })
            .finally(() => {
                btn.disabled = false;
                btn.textContent = '🔍 Search';
            });
        }
        
        function displayResults(videos) {
            const resultsDiv = document.getElementById('results');
            resultsDiv.innerHTML = videos.map(video => `
                <div class="video-card" onclick="playVideo('${video.url}')">
                    <img src="${video.thumbnail}" 
                         alt="${escapeHtml(video.title)}" 
                         class="video-thumbnail"
                         loading="lazy"
                         onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22320%22 height=%22180%22%3E%3Crect fill=%22%23ddd%22 width=%22320%22 height=%22180%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 dominant-baseline=%22middle%22 text-anchor=%22middle%22 fill=%22%23999%22 font-size=%2214%22%3E🎬 Video%3C/text%3E%3C/svg%3E'">
                    <div class="video-info">
                        <div class="video-title">${escapeHtml(video.title)}</div>
                        <div class="video-meta">${escapeHtml(video.author)}</div>
                        <div class="video-stats">${video.views} • ${video.duration}</div>
                    </div>
                </div>
            `).join('');
        }
        
        function playVideo(url) {
            const player = document.querySelector('input[name="player"]:checked').value;
            
            hideMessage();
            showMessage('⏳ Loading player...', 'success');
            
            fetch('/play', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({query: url, player})
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    showMessage('✅ ' + data.message, 'success');
                } else {
                    showMessage('❌ Error: ' + data.message, 'error');
                }
            })
            .catch(err => {
                showMessage('❌ Error: ' + err.message, 'error');
            });
        }
        
        function showMessage(text, type) {
            const msg = document.getElementById('message');
            msg.textContent = text;
            msg.className = 'message ' + type;
            msg.style.display = 'block';
        }
        
        function hideMessage() {
            document.getElementById('message').style.display = 'none';
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
    </script>
</body>
</html>
        """
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass

def main():
    PORT = 8088
    server = HTTPServer(('localhost', PORT), YouTubeHandler)
    
    print("\n" + "="*60)
    print("   🎬 YouTube Ad-Free Player with Search")
    print("="*60)
    print(f"\n✅ Server started at: http://localhost:{PORT}")
    print(f"\n🌐 Opening in your browser...")
    print(f"\n💡 Search powered by yt-dlp (direct from YouTube!)")
    print(f"   - More reliable than API services")
    print(f"   - Requires: brew install yt-dlp")
    print(f"\n💡 Press Ctrl+C to stop the server\n")
    
    # Open browser
    threading.Timer(1.5, lambda: webbrowser.open(f'http://localhost:{PORT}')).start()
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped. Goodbye!")
        server.shutdown()

if __name__ == "__main__":
    main()