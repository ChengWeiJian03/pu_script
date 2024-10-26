import requests
from lxml import etree
import os
from dataclasses import dataclass
from rich.table import Table
from rich.live import Live
import time
from rich.text import Text
from urllib.parse import urlparse, parse_qs
from console_manager import console
from re_expression import re_expression

@dataclass
class ActivateInfo:
    index: int
    name: str
    location: str
    remaining_spots: str
    hash_value: str
    url: str
    id: str
    registration_time: str  # 新增报名时间字段

class Information:
    def __init__(self, headers):
        self.activate_info_urls = []
        self.active_info_list = []
        self.headers = headers
        self.apply_list = []
        # 分类号
        self.activate_params = {
            "校园文化活动": 2134,
            "经典阅读": 3589,
            "劳动实践-志愿服务": 3587,
            "劳动实践-日常劳动": 3755,
            "劳动实践-专业劳动": 3576,
            "劳动实践-理论学习": 3757,
            "劳动实践-特色劳动": 3580
        }
        self.re_expression = re_expression

    def get_activate_urls(self, start_page=1, end_page=5):
        for activate_param in self.activate_params.values():  # 遍历所有分类
            for pages in range(start_page, end_page + 1):  # 获取当前分类前5页的活动信息url
                url = f'https://pocketuni.net/index.php?app=event&mod=School&act=board&cat=all&cid={activate_param}&p={pages}'
                resp = requests.get(url, headers=self.headers)
                resp_tree = etree.HTML(resp.text)
                self.activate_info_urls.extend(
                    resp_tree.xpath("/html/body/div[2]/div/div[3]/div[2]/div[1]/ul/li/div[2]/div[1]/a/@href"))
                resp.close()
        return self.activate_info_urls

    def get_hash_by_id(self, id):
        with requests.get(f'https://pocketuni.net/index.php?app=event&mod=Front&act=join&id={id}', headers=self.headers) as resp:
            matches = self.re_expression.hash_param.findall(resp.text)
            hash_value = matches[0] if matches else ''
        return hash_value

    def submit_button(self):
        for active in self.apply_list:
            params = {'app': 'event', 'mod': 'Front', 'act': 'doAddUser', 'id': f'{active.id}'}
            data = {'__hash__': active.hash_value}
            resp = requests.post('https://pocketuni.net/index.php', params=params, headers=self.headers, data=data)
            if "人数已满" in resp.text:
                console.print(f"活动 {active.name} 人数已满，报名失败,报名下一个", style="red")
                continue
            elif "操作太频繁" in resp.text:
                console.print(f"活动 {active.name} 操作太频繁，报名失败,报名下一个", style="red")
                continue
            elif "报名成功" in resp.text:
                console.print(f"成功提交报名：{active.name}", style="green")
            else:
                console.print(f"未知错误{active.name}", style="red")
            resp.close()

    def submit_activate_by_url(self):
        
        for active in self.apply_list:
            if not active.id:
                active.id = self.get_id_by_url(active.url)
            active.hash_value = self.get_hash_by_id(active.id)
        start_time = time.time()
        self.submit_button()
        print(f"submit{time.time() - start_time:.2f}秒")

    def get_id_by_url(self, url):
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        return query_params.get('id', [None])[0]

    def get_activate_name_inside(self, activate_info_url):
        activate_name = "空"
        with requests.get(activate_info_url, headers=self.headers) as resp:
            matches = self.re_expression.activity_name.findall(resp.text)
            activate_name = matches[0] if matches else activate_name
        return activate_name

    def get_search_activate_urls(self, start_page=1, end_page=5, keyword="三江讲堂"):
        self.activate_info_urls = []
        for pages in range(start_page, end_page + 1):
            url = f'https://pocketuni.net/index.php?app=event&mod=School&act=board&titkey={keyword}&cid=2134&p={pages}'
            resp = requests.get(url, headers=self.headers)
            resp_tree = etree.HTML(resp.text)
            self.activate_info_urls.extend(
                resp_tree.xpath("/html/body/div[2]/div/div[3]/div[2]/div[1]/ul/li/div[2]/div[1]/a/@href"))
            resp.close()
        return self.activate_info_urls

    def get_remaining_spots_inside(self, activate_info_url):
        with requests.get(activate_info_url, headers=self.headers) as resp:
            matches = self.re_expression.remaining_spots.findall(resp.text)
        if matches:
            remaining_spots = matches[0].strip()
            if "br" in remaining_spots:
                remaining_spots = "0"
        else:
            remaining_spots = "0"
        return remaining_spots

    def get_activity_location_inside(self, activate_info_url):
        activity_location = "空"
        with requests.get(activate_info_url, headers=self.headers) as resp:
            matches = self.re_expression.activity_location.findall(resp.text)
            activity_location = matches[0] if matches else activity_location
        return activity_location

    def is_active_status(self, activate_info_url):
        with requests.get(activate_info_url.replace("act=index", "act=join"), headers=self.headers) as resp:
            content = resp.text
        if "报名已结束" in content:
            return "报名已结束"

    def get_registration_time(self, activate_info_url):
        with requests.get(activate_info_url.replace("act=index", "act=join"), headers=self.headers) as resp:
            matches = self.re_expression.registration_time.findall(resp.text)
        registration_time = matches[0] if matches else "可报名"
        return registration_time

    def get_activate_by_keyword(self, keyword):
        pages = 1
        while True:
            # 清空列表
            self.activate_info_urls = []
            self.active_info_list = []

            # 获取当前页的活动信息
            self.get_search_activate_urls(pages, pages, keyword)
            if not self.activate_info_urls:
                console.print("没有更多活动信息", style="yellow")
                break

            for idx, url in enumerate(self.activate_info_urls, start=1):
                console.print(f"正在获取第{idx}个活动信息")
                remaining_spots = self.get_remaining_spots_inside(url)
                if remaining_spots == "0" and False:
                    continue  # 跳过已满的活动

                active = ActivateInfo(
                    index=idx,
                    name=self.get_activate_name_inside(url),
                    location=self.get_activity_location_inside(url),
                    remaining_spots=remaining_spots,
                    hash_value="",  # will be filled later
                    url=url,
                    id=self.get_id_by_url(url),
                    registration_time=self.get_registration_time(url)
                )

                self.active_info_list.append(active)

            if not self.active_info_list:
                console.print("此页活动报名已满或没有符合条件的活动", style="yellow")
            else:
                self.display_static(self.active_info_list)

                while True:
                    choice = console.input("\n输入活动序号添加到抢课列表，输入'n'显示下一页，输入'q'退出: ").lower()
                    if choice == 'n':
                        break
                    elif choice == 'q':
                        return
                    elif choice.isdigit():
                        choice = int(choice)
                        if 1 <= choice <= len(self.active_info_list):
                            selected_activity = self.active_info_list[choice - 1]
                            selected_activity.remaining_spots = selected_activity.remaining_spots.replace(" ", "")
                            if selected_activity.remaining_spots == "0" and False:
                                console.print(f"活动 {selected_activity.name} 已无剩余名额，添加失败。", style="red")
                            else:
                                self.apply_list.append(selected_activity)
                                console.print(f"已将活动 {selected_activity.name} 添加到抢课列表。", style="green")
                            self.display_apply_list()
                        else:
                            console.print("无效的活动序号，请重新输入。", style="red")
                    else:
                        console.print("输入无效，请重新输入。", style="red")

            # 询问是否显示下一页
            choice = console.input("\n是否显示下一页? (y/n): ").lower()
            if choice != 'y':
                break

            pages += 1  # 每次只增加一页

    def display_apply_list(self):
        if not self.apply_list:
            console.print("抢课列表为空", style="yellow")
            return

        table = Table(title="抢课列表")
        table.add_column("序号", style="cyan", no_wrap=True)
        table.add_column("活动名称", style="cyan", no_wrap=True)
        table.add_column("活动地点", style="magenta")
        table.add_column("剩余名额", style="green")
        table.add_column("报名时间", style="yellow")

        for idx, activity in enumerate(self.apply_list, start=1):
            table.add_row(
                str(idx),
                activity.name,
                activity.location,
                activity.remaining_spots,
                activity.registration_time,
            )

        console.print(table)

    def display_static(self, active_info_list):
        table = Table(title="活动信息")
        table.add_column("活动序号", style="cyan", no_wrap=True)
        table.add_column("活动名称", style="cyan", no_wrap=True)
        table.add_column("活动地点", style="magenta")
        table.add_column("剩余名额", style="green")
        table.add_column("报名时间", style="yellow")  # 新增报名时间列

        for activity in active_info_list:
            table.add_row(
                str(activity.index),
                activity.name,
                activity.location,
                activity.remaining_spots,
                activity.registration_time,  # 添加报名时间
            )
        console.print(table)

if __name__ == "__main__":
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    }

    try:
        with open(f"{os.getcwd()}/cookie.txt", "r") as f:
            headers["cookie"] = f.read()
    except FileNotFoundError:
        console.print("cookie.txt 文件未找到，请确保存在并填入正确的cookie。", style="red")
        exit(1)

    imf = Information(headers)
    keyword = console.input("请输入搜索关键词：")
    imf.get_activate_by_keyword(keyword)

    if imf.apply_list:
        choice = console.input("是否立即提交抢课申请? (y/n): ").lower()
        if choice == 'y':
            imf.submit_activate_by_url()
        else:
            console.print("已取消提交。", style="yellow")
    else:
        console.print("未选择任何活动。", style="yellow")
        
    while True:
        imf.submit_activate_by_url()