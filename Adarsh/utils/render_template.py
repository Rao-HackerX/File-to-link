import os
import urllib.parse
import logging
import aiofiles
import aiohttp
from Adarsh.vars import Var
from Adarsh.bot import StreamBot
from Adarsh.utils.human_readable import humanbytes
from Adarsh.utils.file_properties import get_file_ids
from Adarsh.server.exceptions import InvalidHash, FIleNotFound

FALLBACK_REQ_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>__HEADING__</title>
    <link rel="stylesheet" href="https://cdn.plyr.io/3.6.9/plyr.css" />
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        html, body { width: 100vw; height: 100vh; background-color: #000; overflow: hidden; }
        .container { width: 100vw; height: 100vh; display: flex; justify-content: center; align-items: center; }
        .plyr { width: 100vw; height: 100vh; }
    </style>
</head>
<body>
    <div class="container">
        <tag src="__SRC__" class="player"></tag>
    </div>
    <script src="https://cdn.plyr.io/3.6.9/plyr.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', () => {
            new Plyr('.player', {
                controls: ['play-large', 'rewind', 'play', 'fast-forward', 'progress', 'current-time', 'duration', 'mute', 'volume', 'captions', 'settings', 'pip', 'airplay', 'fullscreen']
            });
        });
    </script>
</body>
</html>"""

async def render_page(id: int, secure_hash: str) -> str:
    try:
        file_data = await get_file_ids(StreamBot, int(Var.BIN_CHANNEL), int(id))
    except Exception as e:
        logging.error(f"Error getting file_ids for ID {id}: {e}")
        raise FIleNotFound

    if not file_data or not hasattr(file_data, 'unique_id') or file_data.unique_id[:6] != secure_hash:
        logging.debug(f'Invalid hash for message ID {id}')
        raise InvalidHash

    src = urllib.parse.urljoin(Var.URL, f'{secure_hash}{str(id)}')
    
    raw_mime = getattr(file_data, 'mime_type', None) or 'video/mp4'
    media_type = str(raw_mime).split('/')[0].strip() if '/' in str(raw_mime) else 'video'
    file_name = getattr(file_data, 'file_name', None) or 'Video'

    template_paths = ['Adarsh/template/req.html', 'template/req.html', 'req.html']
    template_file = None
    for path in template_paths:
        if os.path.exists(path):
            template_file = path
            break

    if media_type in ['video', 'audio']:
        heading = f"{'Watch' if media_type == 'video' else 'Listen'} {file_name}"
        if template_file:
            try:
                async with aiofiles.open(template_file, mode='r') as r:
                    content = await r.read()
            except Exception as e:
                logging.error(f"Failed to read template file {template_file}: {e}")
                content = FALLBACK_REQ_HTML
        else:
            content = FALLBACK_REQ_HTML

        html = content.replace('__HEADING__', heading)
        html = html.replace('__SRC__', src)
        html = html.replace('tag', media_type)
        
        if '%s' in html:
            try:
                html = html % (heading, file_name, src)
            except Exception:
                pass
        return html
    else:
        dl_paths = ['Adarsh/template/dl.html', 'template/dl.html', 'dl.html']
        dl_file = None
        for path in dl_paths:
            if os.path.exists(path):
                dl_file = path
                break
        
        heading = f"Download {file_name}"
        file_size = "Unknown Size"
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(src) as u:
                    file_size = humanbytes(int(u.headers.get('Content-Length', 0)))
        except Exception as e:
            logging.error(f"Error fetching content length for download template: {e}")

        if dl_file:
            try:
                async with aiofiles.open(dl_file, mode='r') as r:
                    content = await r.read()
                    if '%s' in content:
                        return content % (heading, file_name, src, file_size)
                    return content.replace('__HEADING__', heading).replace('__SRC__', src).replace('__SIZE__', file_size)
            except Exception as e:
                logging.error(f"Error reading dl template: {e}")

        return f"<html><body><h1>{heading}</h1><p>Size: {file_size}</p><a href='{src}'>Download File</a></body></html>"
