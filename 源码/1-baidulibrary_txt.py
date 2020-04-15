# coding=utf-8
import requests
import re
import json


class BaiduLibrary:
    def __init__(self, url):
        self.url = url
        self.param_url = "https://wenku.baidu.com/api/doc/getdocinfo?callback=cb&doc_id={}"
        self.data_url = "https://wkretype.bdimg.com/retype/text/{}?md5sum={}&pn=1&rn={}&type={}&rsign={}"
        self.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36"}

    def parse_url(self, url, encoding='utf-8'):  # 发送请求，获取响应
        response = requests.get(url, headers=self.headers)
        return response.content.decode(encoding)

    def get_title_and_docId_and_type(self, html):  # 提取字段 — title 和 docId 和 type
        title = re.findall("'title': '(.*?)',", html)[0]
        docId = re.findall("'docId': '(.*?)',", html)[0]
        type = re.findall("'docType': '(.*?)',", html)[0]
        # print(title, '\n', docId, '\n', type)
        return title, docId, type

    def get_md5sum_and_totalnum_and_rsign(self, param_str):  # 提取字段 — rn 和 md5sum 和 rsign
        param_str = re.findall(r'/\*\*/cb\((.*?)\)', param_str)[0]
        rect = json.loads(param_str)
        rn = rect['docInfo']['totalPageNum']
        md5sum = re.findall("&md5sum=(.*)", rect['md5sum'])[0]
        rsign = rect['rsign']
        # print(rn, '\n', rsign)
        return rn, md5sum, rsign

    @staticmethod
    def get_data(data_str):  # 提取数据
        rect = json.loads(data_str)
        content = ""
        for c in rect:
            content += c['parags'][0]['c']
        return content

    def save(self, content, title):  # 保存
        print(content)
        with open(title + ".txt", 'w', encoding="utf-8") as f:
            f.write(content)
        print("下载完成！")

    def run(self):
        # 1.构建url地址
        # 2.发送请求，获取响应
        html = self.parse_url(self.url, encoding='gbk')
        title, docId, type = self.get_title_and_docId_and_type(html)

        param_str = self.parse_url(self.param_url.format(docId))
        rn, md5sum, rsign = self.get_md5sum_and_totalnum_and_rsign(param_str)

        # print(docId, '----', md5sum, '----', rn, '----', type, '----', rsign)
        data_str = self.parse_url(self.data_url.format(docId, md5sum, rn, type, rsign))
        # 3.提取数据
        content = self.get_data(data_str)
        # 4.保存
        self.save(content, title)


if __name__ == '__main__':
    url = input("请输入要下载的文库Url地址：")  # https://wenku.baidu.com/view/cbb4af8b783e0912a3162a89.html?from=search
    # url = "https://wenku.baidu.com/view/cbb4af8b783e0912a3162a89.html?from=search"
    bdl = BaiduLibrary(url)
    bdl.run()

# "https://wkretype.bdimg.com/retype/text/{}?md5sum={}&pn=1&rn={}&type={}&rsign={}"
# cbb4af8b783e0912a3162a89 ---- 6e7a10b16f3ad8d3b40ecd0dfe8d1b67&sign=16541bdb24 ---- 4 ---- txt ---- p_4-r_0-s_460f0
# https://wkretype.bdimg.com/retype/text/cbb4af8b783e0912a3162a89?md5sum=6e7a10b16f3ad8d3b40ecd0dfe8d1b67&sign=16541bdb24&pn=1&rn=4&type=txt&rsign=p_4-r_0-s_460f0