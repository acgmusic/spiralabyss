import re
import requests
from lxml import etree
from urllib import parse
import json
import os


class MultiKeyMap:
    def __init__(self, key_list):
        self.meta_data = [{'en_name': key} for key in key_list]
        self.data_mapper = {key: i for i, key in enumerate(key_list)}

    @staticmethod
    def load_from_json(fp="data/cache/character.json"):
        try:
            d = MultiKeyMap([])
            fp = os.path.join(os.path.dirname(__file__), fp)
            with open(fp, 'r', encoding="utf-8") as f:
                data = json.loads(f.read())
                d.meta_data = data['meta_data']
                d.data_mapper = data['data_mapper']
            return d
        except FileNotFoundError:
            raise FileNotFoundError(f"缓存文件{fp}丢失，请前往github下载相应的文件并放入正确的位置。"
                                    "或选择重新安装此python库。")

    def save_as_json(self, fp="data/cache/character.json"):
        fp = os.path.join(os.path.dirname(__file__), fp)
        with open(fp, 'w', encoding="utf-8") as f:
            f.write(json.dumps({'meta_data': self.meta_data, 'data_mapper': self.data_mapper}))

    def __getitem__(self, key):
        return self.meta_data[self.data_mapper[key]]

    def __setitem__(self, key, value):
        """key: must already in MultiKeyMap.data_mapper

        value: {meta_key: meta_value}
        """
        assert type(value) == dict
        assert len(value) == 1
        assert key in self.data_mapper.keys()
        pos = self.data_mapper[key]
        self.meta_data[pos].update(value)
        self.data_mapper[list(value.values())[0]] = pos

    def __delitem__(self, key):
        del self.data_mapper[key]

    def keys(self):
        return self.data_mapper.keys()

    def get_values(self, key='en_name'):
        if len(self.meta_data) == 0:
            return []
        if key in self.meta_data[0].keys():
            return [item[key] for item in self.meta_data]
        else:
            raise KeyError(f"'{key}' is not in meta_data. You can call 'keys\(\)'")


def get_page_tree(url):
    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/100.0.4896.127 Safari/537.36 "
    }
    response = requests.get(url=url, headers=headers)
    page_text = response.text
    tree = etree.HTML(page_text)
    return tree


def download_pic(url, save_fn):
    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/100.0.4896.127 Safari/537.36 "
    }
    response = requests.get(url=url, headers=headers)
    with open(save_fn, 'wb') as f:
        f.write(response.content)


# 从百度百科，根据角色的英文名，获取中文名
def get_zh_name_from_baike(name):
    url = "https://baike.baidu.com/search/none?word=" + parse.quote(f'{name} 原神角色')
    tree = get_page_tree(url)
    for i, dd in enumerate(tree.xpath('//*[@id="body_wrapper"]/div[1]/dl/dd')):
        if '原神' in "".join(dd.xpath('p//text()')):
            url = "https://baike.baidu.com" + dd.xpath('a/@href')[0]
            break
    else:
        return get_zh_name_from_baidu(name)
    tree = get_page_tree(url)
    zh_name = tree.xpath('body/div[3]/div[2]/div/div[1]//h1/text()')[0]
    return zh_name


# 尽可能避免使用百度搜索，准确率不能保证100%。另外需要先确定中文名列表
def get_zh_name_from_baidu(name):
    # 先获取中文名列表
    url = "https://baike.baidu.com/item/%E5%8E%9F%E7%A5%9E"
    tree = get_page_tree(url)
    zh_name_list = tree.xpath(
        "/html/body/div[3]/div[2]/div/div[1]/table[@class='transparentBorder']/tr/td[1]/div[1]/b[2]/a/text()")

    url = "https://www.baidu.com/s?wd=" + parse.quote(f"{name} 原神角色")
    count_map = {zh_name: 0 for zh_name in zh_name_list}
    for i in range(5):
        tree = get_page_tree(url + f"&pn={i * 10}")
        text = "".join(tree.xpath('//div[contains(@id, "content_left")]//text()'))
        for zh_name in zh_name_list:
            count_map[zh_name] += len(re.findall(zh_name, text))
    zh_name = sorted(
        list(count_map.items()),
        key=lambda x: x[1],
        reverse=True
    )[0][0]
    return zh_name


# def load_character_map(fp="./data/cache/character.json"):
#     try:
#         character_map_load = MultiKeyMap.load_from_json(fp)
#     except FileNotFoundError:
#         raise FileNotFoundError(f"缓存文件{fp}丢失，请前往github下载相应的文件并放入正确的位置。"
#                                 "或选择重新安装此python库。")
#     return character_map_load


def change_zh_name(en_name, zh_name):
    # 读取
    character_map_load = MultiKeyMap.load_from_json()
    assert en_name in character_map_load.keys(), f"{en_name} 不是有效的英文角色名称。"
    old_zh_name = character_map_load[en_name]['zh_name']
    del character_map_load[old_zh_name]
    character_map_load[en_name] = {'zh_name': zh_name}
    print(f"角色 {en_name} 的中文名修改成功。将 {old_zh_name} 修改为了 {zh_name}")

    # 保存
    character_map_load.save_as_json()



if __name__ == '__main__':
    def print_cwd():
        import os
        print(os.path.join(os.path.dirname(__file__), 'test.txt'))
    print_cwd()




