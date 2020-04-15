# coding=utf-8
import requests
import re
import json
import math
import time


class BaiduLibrary:
    def __init__(self, url):
        self.url = url
        self.param_url_txt = "https://wenku.baidu.com/api/doc/getdocinfo?callback=cb&doc_id={}"
        self.data_url_txt = "https://wkretype.bdimg.com/retype/text/{}?md5sum={}&pn=1&rn={}&type={}&rsign={}"

        self.param_url_doc = "https://wenku.baidu.com/browse/getrequest?doc_id={}&type=html&rn=50&pn=1"
        self.headers = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36"}
        self.data_re = re.compile(r"wenku_\d+\((.*)\)")  # 匹配数据的正则

    def parse_url(self, url, encoding='utf-8'):  # 发送请求，获取响应
        response = requests.get(url, headers=self.headers)
        return response.content.decode(encoding)

    @staticmethod
    def get_title_and_docId_and_type(html):  # 提取字段 — title 和 docId 和 type
        title = re.findall("'title': '(.*?)',", html)[0]
        docId = re.findall("'docId': '(.*?)',", html)[0]
        type = re.findall("'docType': '(.*?)',", html)[0]
        # print(title, '\n', docId, '\n', type)
        return title, docId, type

    # --------- txt 类型 ---------------
    def txt_get_md5sum_and_totalnum_and_rsign(self, param_str):  # 提取字段 — rn 和 md5sum 和 rsign
        param_str = re.findall(r'/\*\*/cb\((.*?)\)', param_str)[0]
        rect = json.loads(param_str)
        rn = rect['docInfo']['totalPageNum']
        md5sum = re.findall("&md5sum=(.*)", rect['md5sum'])[0]
        rsign = rect['rsign']
        # print(rn, '\n', rsign)
        return rn, md5sum, rsign

    @staticmethod
    def txt_get_data(data_str):  # 提取数据
        rect = json.loads(data_str)
        content = ""
        for c in rect:
            content += c['parags'][0]['c']
        return content

    # --------- doc 类型 ---------------
    @staticmethod
    def doc_get_data_url_list(param_str):  # 提取所有保存有数据的url
        rect = json.loads(param_str)
        url_list = []
        for i in rect['json']:
            url_list.append(i['pageLoadUrl'])
        # print(url_list)
        return url_list

    # def doc_get_data(self, data_str):  # 提取数据  例子：https://wenku.baidu.com/view/da49031bcc7931b765ce153f.html
    #     data_str = self.data_re.findall(data_str)[0]
    #     body = json.loads(data_str)['body']
    #     content = ""
    #
    #     for index, item in enumerate(body):
    #         if not isinstance(item['c'], dict):
    #             content += item['c']
    #
    #             # 根据y值的不同 判断 是否需要换行
    #             current_y = str(item['p']['y'])
    #             next_y = str(body[index + 1]['p']['y']) if index != len(body) - 1 else current_y
    #             if current_y != next_y:
    #                 content += '\r\n'
    #     return content

    # def doc_get_data(self, data_str):  # 提取数据  例子：https://wenku.baidu.com/view/64835d0e28ea81c758f578e6.html
    #     data_str = self.data_re.findall(data_str)[0]
    #     body = json.loads(data_str)['body']
    #     content = ""
    #
    #     for index, item in enumerate(body):
    #         if not isinstance(item['c'], dict) and item['c'] != '':
    #             content += item['c']
    #
    #             # 根据y值的不同 判断 是否需要换行
    #             current_y = str(item['p']['y'])
    #             next_y = str(body[index + 1]['p']['y']) if index != len(body) - 1 else current_y
    #             next_c = str(body[index + 1]['c']) if index != len(body) - 1 else item['c']
    #             if current_y != next_y and abs(float(current_y)-float(next_y)) >= 4 \
    #                     and (not ((next_c == ' ' and item['c'] == '') or (next_c == '' and item['c'] == ' '))):  # abs(current_y-next_y) 加粗的字体y轴可能有多少偏差
    #                 content += '\r\n'
    #     return content

    def doc_get_data(self, data_str):  # 提取数据  例子：https://wenku.baidu.com/view/8e2373ae71fe910ef12df87d?pcf=2&from=singlemessage
        data_str = self.data_re.findall(data_str)[0]
        body = json.loads(data_str)['body']
        content = ""

        is_line_feed = True  # 是否已换行
        for index, item in enumerate(body):
            if not isinstance(item['c'], dict) and item['c'] != '':
                # 根据y值的不同 判断 是否需要换行
                current_y = str(item['p']['y'])
                next_y = str(body[index + 1]['p']['y']) if index != len(body) - 1 else current_y
                next_c = str(body[index + 1]['c']) if index != len(body) - 1 else item['c']

                last_y = str(body[index - 1]['p']['y']) if index != 0 else current_y
                content, is_line_feed = self.doc_add_space(is_line_feed, last_y, current_y, next_y, item, next_c, index, content)

                content += item['c']

                if not ((next_c == ' ' and item['c'] == '') or (next_c == '' and item['c'] == ' ')):  # abs(current_y-next_y) 加粗的字体y轴可能有多少偏差
                    if current_y != next_y and abs(float(current_y)-float(next_y)) >= 4:
                        content += '\r\n'
                        is_line_feed = True
                    else:
                        is_line_feed = False
                else:
                    is_line_feed = False
        return content

    def doc_add_space(self, is_line_feed, last_y, current_y, next_y, item, next_c, index, content):  # 添加空格，缩进
        if not ((next_c == ' ' and item['c'] == '') or (next_c == '' and item['c'] == ' ')):  # abs(current_y-next_y) 加粗的字体y轴可能有多少偏差
            if current_y == next_y or abs(float(current_y)-float(next_y)) <= 4:    # 确保是 上一个内容与当前内容 同一行
                content, is_line_feed = self.doc_do_add_space(is_line_feed, item, index, content)
            elif current_y == last_y or abs(float(current_y)-float(last_y)) <= 4:  # 确保是 下一个内容与当前内容 同一行
                content, is_line_feed = self.doc_do_add_space(is_line_feed, item, index, content)
            elif item['p']['x'] < 200:  # 当前内容 就是 一行
                content, is_line_feed = self.doc_do_add_space(is_line_feed, item, index, content)
        return content, is_line_feed

    def doc_do_add_space(self, is_line_feed, item, index, content):  # 添加空格，缩进
        # 同一行中只有开头才需要添加缩进
        if is_line_feed:
            space_count = int(math.ceil(item['p']['x'] / 4.5))  # 向上取整，最后转为int类型

            if item['p']['x'] < 200:
                for i in range(space_count):
                    content += " "
                is_line_feed = False
            elif index == 0:
                for i in range(space_count):
                    content += " "
                is_line_feed = False
        return content, is_line_feed

    def save(self, content, title):  # 保存
        # print(content)
        with open(title+".txt", 'w', encoding="utf-8") as f:
            f.write(content)
        print("下载完成！")

    def run(self):
        # 1.构建url地址
        # 2.发送请求，获取响应
        html = self.parse_url(self.url, encoding='gbk')
        title, docId, type = self.get_title_and_docId_and_type(html)

        if type == 'txt':  # txt类型
            param_str = self.parse_url(self.param_url_txt.format(docId))
            rn, md5sum, rsign = self.txt_get_md5sum_and_totalnum_and_rsign(param_str)

            # print(docId, '----', md5sum, '----', rn, '----', type, '----', rsign)
            data_str = self.parse_url(self.data_url_txt.format(docId, md5sum, rn, type, rsign))
            # 3.提取数据
            content = self.txt_get_data(data_str)

        elif type == 'doc':  # doc类型
            param_str = self.parse_url(self.param_url_doc.format(docId))
            url_list = self.doc_get_data_url_list(param_str)

            content = ""
            for url in url_list:
                data_str = self.parse_url(url)
                # 3.提取数据
                content += self.doc_get_data(data_str)
                content += '\r\n'

        else:
            print("下载失败！")
            return

        # 4.保存
        self.save(content, title)


if __name__ == '__main__':
    url = input("请输入要下载的文库Url地址：")
    # https://wenku.baidu.com/view/cbb4af8b783e0912a3162a89.html?from=search
    # https://wenku.baidu.com/view/da49031bcc7931b765ce153f.html
    # https://wenku.baidu.com/view/64835d0e28ea81c758f578e6.html
    # https://wenku.baidu.com/view/077faca8951ea76e58fafab069dc5022aaea4687.html
    # https://wenku.baidu.com/view/8e2373ae71fe910ef12df87d?pcf=2&from=singlemessage
    bdl = BaiduLibrary(url)
    bdl.run()

    print("5秒后自动关闭，也可手动关闭。")
    time.sleep(5)

