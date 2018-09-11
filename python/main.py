'''
电子书下载程序

 电子书制作：
 1. 配置好config.py
 2. 运行生成html文件 （python main.py)
 3. 用电子书制作软件生成电子书

'''
import os
import re
from config import CONFIG
from util import HtmlUtil
from urllib.parse import urlparse
import datetime

class Main(object):
    ebook_config = {}
    output_dir = None
    page_links = []

    def __init__(self, ebook_config):
        self.ebook_config = ebook_config
        self.output_dir = "output/" + ebook_config["ebook_name"]

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
        for page_link in self.page_links:
            print(page_link["url"])
            idx += 1
            filename = "page%03d.html" % idx
            url = self.canonical_url(page_link['url'])
            html = HtmlUtil.download(url)
            html = HtmlUtil.extract(html, self.ebook_config["ebook_page_tag_start"], self.ebook_config["ebook_page_tag_end"])
            self.save_page(page_link["text"], html, filename)
        print("Done!")

    def save_page(self, title, content, filename):
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

    def run(self):
        self.check_path()
        self.download_dir()
        self.download_pages()

begin = datetime.datetime.now()
main = Main(CONFIG)
main.run()
end = datetime.datetime.now()

print("Total time:", end - begin);
