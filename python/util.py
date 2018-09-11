from urllib import request
import re


class HtmlUtil(object):
    @staticmethod
    def download(url, charset="utf-8"):
        with request.urlopen(url) as response:
            if response.status != 200:
                return None
            else:
                return response.read().decode(charset)

    @staticmethod
    def extract(html, begin, end):
        html = html.replace("\r", "")
        html = html.replace("\n", "")
        begin_index = html.find(begin)
        if begin_index > -1:
            begin_index += len(begin)
            html = html[begin_index:]

        end_index = html.find(end)
        if end_index > -1:
            html = html[0:end_index]
        return html

    @staticmethod
    def extract_url(html):
        pattern = re.compile(r'<a[^>]*href=[\'"]?([^>\'"\s]*)[\'"]?[^>]*>', re.I)
        return pattern.findall(html)

    @staticmethod
    def extract_img(html):
        pattern = re.compile(r'<img[^>]*src=[\'"]?([^>\'"\s]*)[\'"]?[^>]*>', re.I)
        return pattern.findall(html)
