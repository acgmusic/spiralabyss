import os
from .utils import *
from matplotlib import pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

__all__ = ['team_builder']


def team_builder(version, must_in=[], must_not_in=[], must_include=[], tor=0.1,
                 show_pic=True, show_usage_above_imag=False):
    assert type(tor) in [float, int], "tor参数必须为数字。"
    assert type(show_pic) == bool
    assert type(show_usage_above_imag) == bool
    character_map = MultiKeyMap.load_from_json()

    fp = os.path.join(os.path.dirname(__file__), f"data/teams/{version}.txt")

    try:
        with open(fp, 'r', encoding="utf-8") as f:
            data = f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"版本号'{version}'不存在，请检查版本号是否正确。如果为当期版本，请先缓存到本地。")

    data.split('\n')[3].split(': ')[0].split(';')[0].split('_')

    teams_dic = {}

    for team in data.split('\n'):
        [team_info, team_user_count] = team.split(': ')
        [fst_half_team_info, snd_half_team_info] = team_info.split(';')
        key = tuple([int(x) for x in fst_half_team_info.split('_')]), tuple(
            [int(x) for x in snd_half_team_info.split('_')])
        value = int(team_user_count)
        teams_dic[key] = value

    def draw_team(id_list, team_score, show_pic=True, show_usage_above_imag=True):
        fig, axes = plt.subplots(1, 4)
        print("-" * 80)
        print(f"成员：{' '.join([character_map[str(id_list[i])]['zh_name'] for i in range(len(id_list))])}")
        print(f"使用率：{team_score}")
        if not show_pic:
            return
        img_root_path = os.path.join(os.path.dirname(__file__), f"data/cache/pics/")
        for i, ax in enumerate(axes[:len(id_list)]):
            name = character_map[str(id_list[i])]['en_name']
            name2img_fmt = {f.split('.')[0]: f.split('.')[1] for f in os.listdir(img_root_path) if
                            len(f.split('.')) > 1}
            assert name in name2img_fmt
            path = img_root_path + name + '.' + name2img_fmt[name]
            img = plt.imread(path)
            ax.imshow(img, interpolation="bicubic")
            ax.axes.get_xaxis().set_visible(False)
            ax.axes.get_yaxis().set_visible(False)
            ax.axes.set_title(character_map[str(id_list[i])]['zh_name'])
        for i in range(4 - len(id_list)):
            ax = axes[3 - i]
            path = img_root_path + 'nothing.jpg'
            img = plt.imread(path)
            ax.imshow(img, interpolation="bicubic")
            ax.axes.get_xaxis().set_visible(False)
            ax.axes.get_yaxis().set_visible(False)
        if show_usage_above_imag:
            fig.suptitle(f"使用率：{team_score}")
        plt.show()

    def search_team(must_in: list, must_not_in: list, must_include: list):
        if len(must_in) > 0 and not isinstance(must_in[0], int):
            must_in = [
                character_map[str(c)]['id']
                for c in must_in
            ]

        if len(must_not_in) > 0 and not isinstance(must_not_in[0], int):
            must_not_in = [
                character_map[str(c)]['id']
                for c in must_not_in
            ]

        if len(must_include) > 0 and not isinstance(must_include[0], int):
            must_include = [
                character_map[str(c)]['id']
                for c in must_include
            ]

        team_dict_list = [{}, {}]
        for i, team_dict in enumerate(team_dict_list):
            for key, value in teams_dic.items():
                if all([(True if c in key[i] else False) for c in must_in]) and \
                        all([(False if c in key[i] else True) for c in must_not_in]) and \
                        (any([(True if c in key[i] else False) for c in must_include]) or must_include == []):
                    key_tmp = tuple(must_in + [x for x in key[i] if x not in must_in])
                    team_dict[key_tmp] = team_dict.get(key_tmp, 0) + value
        return team_dict_list

    def print_teams(team_dict_list, tor=0, show_pic=show_pic, show_usage_above_imag=show_usage_above_imag):
        info_show = ["上半", "下半"]
        for i, team_dict in enumerate(team_dict_list):
            print("=" * 80)
            print(info_show[i])
            teams_dic_list = list(team_dict.items())
            teams_dic_list.sort(key=lambda x: x[1], reverse=True)
            teams_dic_list = list(filter(lambda x: x[1] / len(teams_dic) * 100 > tor, teams_dic_list))
            for team in teams_dic_list:
                draw_team(team[0], str(round(team[1] / len(teams_dic) * 100, 2)) + "%", show_pic=show_pic,
                          show_usage_above_imag=show_usage_above_imag)
                # if show_pic:
                #     draw_team(team[0], str(round(team[1] / len(teams_dic) * 100, 2)) + "%")
                # else:
                #     print([character_map[str(c)] for c in team[0]], team[1])
            print("\n" * 5 * (show_pic + 1))

    # must_include = list(set.union(set(must_include), set(must_in)))

    print_teams(
        search_team(must_in=must_in, must_not_in=must_not_in, must_include=must_include),
        tor=tor,
        show_pic=show_pic,
        show_usage_above_imag=show_usage_above_imag
    )


def get_character_list(mod=None, exclude=None):
    character_map = MultiKeyMap.load_from_json()
    character_list = []
    if exclude is None:
        exclude = []
    if mod is None:
        character_list = [dic['zh_name'] for dic in character_map.meta_data]
    elif str(mod) in '45':
        for dic in character_map.meta_data:
            if (dic['rarity'] == int(mod)) and (dic['zh_name'] not in exclude):
                character_list.append(dic['zh_name'])
    elif mod in '火水冰岩风雷草':
        for dic in character_map.meta_data:
            if (dic['element'] == mod) and (dic['zh_name'] not in exclude):
                character_list.append(dic['zh_name'])
    elif all([(m in '45火水冰岩风雷草') for m in mod]):
        return list(set.intersection(*[set(get_character_list(mod=m, exclude=exclude)) for m in mod]))

    else:
        assert False, "mod参数只能为4、5、火、水、冰、岩、风、雷、草、None"
    return character_list


if __name__ == '__main__':
    team_builder(version="2.6",
                 must_in=["雷电将军", "神里绫华"],
                 must_not_in=[],
                 tor=0.11,
                 show_pic=True,
                 show_usage_above_imag=True
                 )
