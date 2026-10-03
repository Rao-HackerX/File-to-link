from Adarsh.vars import Var
from Adarsh.bot import StreamBot
from Adarsh.utils.human_readable import humanbytes
from Adarsh.utils.file_properties import get_file_ids
from Adarsh.server.exceptions import InvalidHash
import urllib.parse
import aiofiles
import logging
import aiohttp
import os

async def render_page(id, secure_hash):
    file_data = await get_file_ids(StreamBot, int(Var.BIN_CHANNEL), int(id))
    if not file_data or file_data.unique_id[:6] != secure_hash:
        logging.debug(f'Invalid hash for message ID {id}')
        raise InvalidHash
    
    src = urllib.parse.urljoin(Var.URL, f'{secure_hash}{str(id)}')
    
    mime_type = getattr(file_data, 'mime_type', 'video/mp4') or 'video/mp4'
    media_type = str(mime_type).split('/')[0].strip() if '/' in str(mime_type) else 'video'
    file_name = getattr(file_data, 'file_name', 'Video') or 'Video'

    # Check path flexibility for templates
    template_path = 'Adarsh/template/req.html'
    if not os.path.exists(template_path):
        template_path = 'template/req.html'

    dl_template_path = 'Adarsh/template/dl.html'
    if not os.path.exists(dl_template_path):
        dl_template_path = 'template/dl.html'

    if media_type in ['video', 'audio']:
        async with aiofiles.open(template_path, mode='r') as r:
            heading = f"{'Watch' if media_type == 'video' else 'Listen'} {file_name}"
            html = await r.read()
            html = html.replace('{HEADING}', heading)
            html = html.replace('{FILE_NAME}', file_name)
            html = html.replace('{SRC}', src)
            html = html.replace('tag', media_type)
            return html
    else:
        async with aiofiles.open(dl_template_path, mode='r') as r:
            async with aiohttp.ClientSession() as s:
                async with s.get(src) as u:
                    heading = f"Download {file_name}"
                    file_size = humanbytes(int(u.headers.get('Content-Length', 0)))
                    html = await r.read()
                    html = html.replace('{HEADING}', heading)
                    html = html.replace('{FILE_NAME}', file_name)
                    html = html.replace('{SRC}', src)
                    html = html.replace('{SIZE}', file_size)
                    return html
