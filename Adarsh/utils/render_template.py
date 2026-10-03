from Adarsh.vars import Var
from Adarsh.bot import StreamBot
from Adarsh.utils.human_readable import humanbytes
from Adarsh.utils.file_properties import get_file_ids
from Adarsh.server.exceptions import InvalidHash
import urllib.parse
import aiofiles
import logging
import aiohttp

async def render_page(id, secure_hash):
    file_data = await get_file_ids(StreamBot, int(Var.BIN_CHANNEL), int(id))
    if not file_data or not hasattr(file_data, 'unique_id') or file_data.unique_id[:6] != secure_hash:
        logging.debug(f'Invalid hash for message ID {id}')
        raise InvalidHash
    
    src = urllib.parse.urljoin(Var.URL, f'{secure_hash}{str(id)}')
    
    raw_mime = getattr(file_data, 'mime_type', 'video/mp4') or 'video/mp4'
    media_type = str(raw_mime).split('/')[0].strip() if '/' in str(raw_mime) else 'video'
    file_name = getattr(file_data, 'file_name', 'video.mp4') or 'video.mp4'

    if media_type in ['video', 'audio']:
        async with aiofiles.open('Adarsh/template/req.html') as r:
            heading = f"{'Watch' if media_type == 'video' else 'Listen'} {file_name}"
            template_str = await r.read()
            html = template_str.replace('tag', media_type) % (heading, file_name, src)
    else:
        async with aiofiles.open('Adarsh/template/dl.html') as r:
            async with aiohttp.ClientSession() as s:
                async with s.get(src) as u:
                    heading = f"Download {file_name}"
                    file_size = humanbytes(int(u.headers.get('Content-Length', 0)))
                    html = (await r.read()) % (heading, file_name, src, file_size)
    return html
