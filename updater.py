from .utils import *
import re
# import requests
# from lxml import etree
# from urllib import parse
import os
import json

__all__ = ['update_local_cache']


def update_local_cache():
    character_map_load = MultiKeyMap.load_from_json()

    print("正在更新...")
    url = "https://spiralabyss.org/zh/floor-12-usage-rate"
    tree_main = get_page_tree(url)
    option_list = tree_main.xpath(
        "//*[@id='__next']/div[2]/div[1]/div/main/div/section/div[5]/div[2]/table/thead/tr/td[1]/select[1]/option")

    character_list = []
    id_list = []

    for option in option_list:
        if option.xpath('@value')[0]:
            character_list.append(option.xpath("text()")[0])
            id_list.append(option.xpath("@value")[0])

    character_map = MultiKeyMap(character_list)

    for character, id_ in zip(character_list, id_list):
        character_map[character] = {'id': int(id_)}


    # 更新中文名
    for character in character_list:
        if character in character_map_load.keys():
            zh_name = character_map_load[character]['zh_name']
            character_map[character] = {'zh_name': zh_name}
        else:
            zh_name = get_zh_name_from_baike(character)
            character_map[character] = {'zh_name': zh_name}
            print(f"角色 {character} 从百度获取的中文名为 {zh_name}。"
                  "如果有误，请手动更改。\n"
                  "更改方式为运行以下函数：change_zh_name('角色英文名', ‘角色中文名’)")

    # 从b站wiki更新信息
    tree_bili_wiki = get_page_tree("https://wiki.biligame.com/ys/%E8%A7%92%E8%89%B2%E7%AD%9B%E9%80%89")
    element = {}
    rarity = {}
    for tr in tree_bili_wiki.xpath('//table[@id="CardSelectTr"]/tbody/tr'):
        if tr.xpath("./td[2]/a/text()"):
            name = tr.xpath("./td[2]/a/text()")[0]
            if tr.xpath("@data-param3"):
                element[name] = tr.xpath("@data-param3")[0]
            else:
                element[name] = None
            if tr.xpath("@data-param1") and tr.xpath("@data-param1")[0]:
                rarity[name] = int(tr.xpath("@data-param1")[0].replace('星', ''))
            else:
                rarity[name] = None
    element['旅行者'] = '岩'
    for i in range(len(character_map.meta_data)):
        zh_name = character_map.meta_data[i]['zh_name']
        character_map.meta_data[i]['rarity'] = rarity[zh_name]
        character_map.meta_data[i]['element'] = element[zh_name]

    character_map.save_as_json()

    print("角色中文信息更新完成。")

    # 更新人物头像
    src_list = tree_main.xpath('//*[@id="__next"]/div[2]/div[1]/div/main/div/section/div[2]//@src')
    title_list = tree_main.xpath('//*[@id="__next"]/div[2]/div[1]/div/main/div/section/div[2]//@title')

    imag_path = os.path.join(os.path.dirname(__file__), "data/cache/pics")
    pic_list = [fn.split('.')[0] for fn in os.listdir(imag_path)]

    for src, title in zip(src_list, title_list):
        if title not in pic_list:
            download_pic(url=src, save_fn=imag_path + title + src[-4:])
            print(f"{title} 头像图片更新成功")

    print("角色头像更新完成。")

    # 更新敌人信息及头像
    enemy_teams = tree_main.xpath("//*[@id='__next']/div[2]/div[1]/div/main/div/section/div[4]/table/tbody/tr")
    enemy_info = {}

    for i, enemy_team in enumerate(enemy_teams):
        [first_half, second_half] = [td.xpath('.//img/@title') for td in enemy_team.xpath('td')[1:]]
        enemy_info[f'12-{i + 1}'] = {'first_half': first_half, 'second_half': second_half}

    print("原魔基本信息更新完成。")
    # 获取当前版本号
    genshin_version = re.findall('\d+\.\d+', tree_main.xpath('//*[@id="__next"]/div[2]/div[1]/div/header/h3/text()')[0])[0]

    fp = os.path.join(os.path.dirname(__file__), f"data/enemys/enemy_info_{genshin_version}.json")
    with open(fp, 'w', encoding="utf-8") as f:
        f.write(json.dumps(enemy_info))

    enemy_teams[0].xpath('td')[1:][0].xpath('.//img/@src')

    enemy_img_path = os.path.join(os.path.dirname(__file__), "data/cache/enemy_imgs/")

    for enemy_team in enemy_teams:
        for half in enemy_team.xpath('td')[1:]:
            src_list = half.xpath('.//img/@src')
            for src in src_list:
                img_name = src.split('/')[-1]
                if img_name not in os.listdir(enemy_img_path):
                    print("更新完成 " + img_name)
                    download_pic(src, enemy_img_path + img_name)
    print("原魔头像更新完成。")

    # 更新角色使用率
    character_list = tree_main.xpath('//*[@id="__next"]/div[2]/div[1]/div/main/div/section/div[2]/div/img/@alt')
    usage_list = tree_main.xpath('//*[@id="__next"]/div[2]/div[1]/div/main/div/section/div[2]/div/div/text()')

    fp = os.path.join(os.path.dirname(__file__), f"data/usage_rate/{genshin_version}.json")
    with open(fp, 'w', encoding="utf-8") as f:
        f.write(json.dumps({k: v for k, v in zip(character_list, usage_list)}))
    print("角色使用率更新完成。")


if __name__ == '__main__':
    update_local_cache()

