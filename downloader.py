from selenium.common.exceptions import TimeoutException
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
# import requests
# from lxml import etree
# import pickle
# from urllib import parse
from .utils import *
from tqdm import tqdm

__all__ = ['down_load_teams']


def down_load_teams(headless=True):
    character_map = MultiKeyMap.load_from_json()
    url = "https://spiralabyss.org/zh/floor-12-usage-rate"
    # 无头浏览器
    if headless:
        opt = Options()
        opt.add_argument("--headless")
        opt.add_argument("--disable-gpu")
        web = Chrome(options=opt)
    else:
        web = Chrome()

    # 打开url
    print("正在打开网页...")
    try:
        web.get(url)
    except TimeoutException:
        raise TimeoutException("网页加载失败，请重试。")

    print("网页已打开，准备下载队伍信息")

    # 一共8个下拉框
    sel_list = [
        Select(
            web.find_element(
                By.XPATH,
                f'//*[@id="__next"]/div[2]/div[1]/div/main/div/section/div[5]/div[2]/table/thead/tr/td[1]/select[{i}]'
            )
        ) for i in range(1, 9)
    ]

    # 打开屏蔽缺少角色的选项
    sel_list[0].select_by_index(1)
    element = web.find_element(By.XPATH, '//input[@id="charFilter"]')
    web.execute_script('arguments[0].click();', element)
    sel_list[0].select_by_index(0)

    # 获取全部角色英文名，按option标签排序
    characters = [opt.text for opt in web.find_elements(
        By.XPATH,
        '//*[@id="__next"]/div[2]/div[1]/div/main/div/section/div[5]/div[2]/table/thead/tr/td[1]/select[1]/option'
    )]

    # 获取全部角色英文名，按使用率排序
    sorted_characters = [div.get_attribute('title') for div in web.find_elements(
        By.XPATH,
        '//*[@id="__next"]/div[2]/div[1]/div/main/div/section/div[2]//img'
    )]

    print("正在下载中... (部分平台进度条可能会卡住，为正常现象，可以设置参数:headless=False 打开浏览器运行)")

    character_name_2_option_pos = {c: i for i, c in enumerate(characters)}

    def get_cur_team_num():
        """
        if team_num >= 40, except there are no option box left, we will
        change the next option box until team_num <= 40
        """
        team_num = web.find_element(
            By.XPATH,
            '//*[@id="__next"]/div[2]/div[1]/div/main/div/section/div[5]/div[2]/table/thead/tr/td[2]'
        ).text.split('\n')[0]
        return int(team_num)

    team_num = get_cur_team_num()

    def get_cur_teams(teams_dic):
        team_num = get_cur_team_num()
        page_num = (team_num + 7) // 8
        WebDriverWait(web, 20).until(
            EC.visibility_of_element_located((By.XPATH, '//div[@class="col-12 col-md-6 mb-5"]')))
        for page in range(page_num):
            #         print(page, page_num)
            if page > 0:
                element = web.find_elements(
                    By.XPATH,
                    '//div[@class="col-12 col-md-6 mb-5"]'
                )[-1].find_elements(
                    By.XPATH,
                    './/td[@colspan="4"]/a'
                )[page]
                web.execute_script('arguments[0].click();', element)
            tr_list = web.find_elements(
                By.XPATH,
                '//*[@id="__next"]/div[2]/div[1]/div/main/div/section/div[5]/div[2]/table/tbody/tr'
            )

            for tr in tr_list[:-1]:  # 最后一栏是页码选择栏，所以去除
                td_list = tr.find_elements(By.XPATH, './td')
                team_list = [td_list[0], td_list[2]]  # 上半场和下半场队伍
                rate = float(td_list[3].text.split('%')[0])  # 使用率
                team_hash_index = []
                for team in team_list:
                    names = [img.get_attribute('title') for img in team.find_elements(By.XPATH, './img')]
                    index = [str(character_map[name]['id']) for name in names]
                    index.sort()
                    team_hash_index.append("_".join(index))
                team_hash_index = ";".join(team_hash_index)
                teams_dic[team_hash_index] = rate

    # path = [T, T, F]， 表示队伍必须有前两个角色，且必须排除第三个角色
    # count_true记录path中True的个数，必须全程保证count_true<=8

    teams_dic = {}

    def dfs(path=[], count_true=0):

        # 首先检查是否可以剪枝
        if get_cur_team_num() <= 40:
            try:
                lenth = len(teams_dic)
                get_cur_teams(teams_dic)
                cur_lenth = len(teams_dic)
                pbar.update(cur_lenth - lenth)
                return
            except IndexError:
                return

        # 否则需要进行分叉

        # 1.必须包含角色时
        path.append(True)
        count_true += 1
        sel_list[count_true - 1].select_by_index(
            character_name_2_option_pos[sorted_characters[len(path) - 1]]
        )

        dfs(path, count_true)

        # 回退
        sel_list[count_true - 1].select_by_index(0)
        path.pop()
        count_true -= 1

        # 2.必须排除角色时
        path.append(False)

        element = web.find_elements(
            By.XPATH,
            '//*[@id="__next"]/div[2]/div[1]/div/main/div/section/div[2]/div'
        )[len(path) - 1]

        element = element.find_element(By.XPATH, './img')
        web.execute_script('arguments[0].click();', element)
        # 如果是第一次排除角色，这时浏览器会有弹窗，需要处理一下
        if len(path) - 1 == count_true:
            #         print("关闭弹窗")
            time.sleep(1.5)
            alert_window = web.switch_to.alert
            alert_window.accept()

        dfs(path, count_true)

        # 回退
        element = web.find_elements(
            By.XPATH,
            '//*[@id="__next"]/div[2]/div[1]/div/main/div/section/div[2]/div'
        )[len(path) - 1]
        element = element.find_element(By.XPATH, './img')
        web.execute_script('arguments[0].click();', element)
        path.pop()



    with tqdm(total=team_num) as pbar:
        pbar.set_description('Processing:')
        dfs()

    # print("正在下载...")
    # dfs()
    # print("队伍信息下载完成！")

    # 获取当前版本号
    genshin_version = re.findall('\d+\.\d+', web.find_elements(
        By.XPATH,
        '//*[@id="__next"]/div[2]/div[1]/div/header/h3'
    )[0].text)[0]

    # 根据百分比近似估计实际数量。
    # 并保存

    fp = os.path.join(os.path.dirname(__file__), f"data/teams/{genshin_version}.txt")
    with open(fp, 'w', encoding="utf-8") as f:
        f.write("\n".join([k + ": " + str(int(100 * v) if v > 0 else 1) for k, v in teams_dic.items()]))

    print("队伍信息下载完成！已保存至 ", fp)


if __name__ == '__main__':
    down_load_teams(False)
