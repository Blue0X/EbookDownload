'''
电子书并发下载

 电子书制作：
 1. 配置好config.py
 2. 运行生成html文件 （python async.py)
 3. 用电子书制作软件生成电子书

'''

import os
import re
from config import CONFIG
from util import HtmlUtil
from urllib.parse import urlparse
import asyncio
import aiohttp
from contextlib import closing
from tqdm import tqdm


class Main(object):
    ebook_config = {}
    output_dir = None
    page_links = []
    sem = None
    pbar = None

    def __init__(self, ebook_config):
        self.ebook_config = ebook_config
        self.output_dir = "output/" + ebook_config["ebook_name"]
        self.sem = asyncio.BoundedSemaphore(5)

    def check_path(self):
        if not os.path.isdir(self.output_dir):
            os.mkdir(self.output_dir)

    def download_dir(self):
        html = HtmlUtil.download(self.ebook_config["ebook_url"])
        # print(html)
        # 目录部分
        html = HtmlUtil.extract(html, self.ebook_config['ebook_dir_tag_start'], self.ebook_config['ebook_dir_tag_end'])
        html = html.replace('</a>', '</A>')
        # 提取链接
        a_tags = html.split("</A>")
        pattern = re.compile(r"^.*<a ", re.I)
        pattern_text = re.compile(r"<a.*?>|</a>", re.I)
        for a_tag in a_tags:
            a_tag = pattern.sub('<a ', a_tag)
            a_href = HtmlUtil.extract_url(a_tag)
            if len(a_href) == 0:
                continue
            a_text = pattern_text.sub("", a_tag)
            self.page_links.append({"url": a_href[0], "text": a_text.strip()})
        # print(self.page_links)
        self.save_index()
        print("Creating index OK")

    def save_index(self):
        html = '''
            <!doctype html>
            <html>
              <head>
                <meta charset="UTF-8">
                <title>目录</title>
                <link href="css/style.css" rel="stylesheet" type="text/css">
              </head>
              <body class="ebook-index">
                <h3>目录</h3>
                {dirs}
              </body>
            </html>
        '''
        dirs = ""
        idx = 0
        for page_link in self.page_links:
            idx += 1
            dirs += "<p><a href=\"page%03d.html\">%s</a></p>\n" % (idx, page_link["text"])
        html = html.format(dirs=dirs)
        fh = open(self.output_dir + "/index.html", "w", encoding='utf-8')
        fh.write(html)
        fh.close()

    def canonical_url(self, url):
        parts = urlparse(self.ebook_config["ebook_url"])
        domain = parts.scheme + "://" + parts.netloc
        if url[0] == '/':
            return domain + url
        elif re.match(r"http://", url):
            return url
        else:
            return domain + "/" + os.path.dirname(parts.path) + '/' + url

    def download_pages(self):
        idx = 0
        tasks = []
        self.pbar = tqdm(total=len(self.page_links))

        with closing(asyncio.get_event_loop()) as loop:
            with aiohttp.ClientSession(loop=loop) as session:
                for page_link in self.page_links:
                    # print(page_link["url"])
                    idx += 1
                    filename = "page%03d.html" % idx
                    url = self.canonical_url(page_link['url'])
                    # tasks.append(self.fetch_and_save(session, url, page_link["text"], filename))
                    tasks.append(self.bound_fetch(session, url, page_link["text"], filename))
                loop.run_until_complete(asyncio.wait(tasks))
        self.pbar.close()
        print("Done!")

    async def bound_fetch(self, session, url, title, filename):
        with (await self.sem):
            await self.fetch_and_save(session, url, title, filename)

    async def fetch_and_save(self, session, url, title, filename):
        # print("Fetching %s, %s" % (url, filename))
        async with session.get(url) as response:
            assert response.status == 200
            html = await response.text()
            html = HtmlUtil.extract(html, self.ebook_config["ebook_page_tag_start"],
                                    self.ebook_config["ebook_page_tag_end"])
            self.save_page(title, html, filename)

    def save_page(self, title, content, filename):
        self.pbar.update(1)
        html = '''
            <!doctype html>
            <html>
              <head>
                <meta charset="UTF-8">
                <title>{title}</title>
                <link href="css/style.css" rel="stylesheet" type="text/css">
              </head>
              <body class="ebook-page">
                <h3 class="ebook-title">{title}</h3>
                <div class="ebook-content">
                {content}
                </div>
              </body>
            </html>
        '''
        html = html.format(title=title, content=content)
        fh = open(self.output_dir + "/" + filename, 'w', encoding='utf-8')
        fh.write(html)
        fh.close()
        # print("Saved file %s" % filename)

    def run(self):
        self.check_path()
        self.download_dir()
        self.download_pages()

if __name__ = '__main__':
    main = Main(CONFIG)
    main.run()
