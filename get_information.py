import requests
from lxml import etree
import os
from dataclasses import dataclass
from re_expression import re_expression
from rich.table import Table
from rich.live import Live
import time
from rich.live import Live
from rich.text import Text
from console_manager import console

@dataclass
class activate_info:
    index: int
    name: str
    location: str
    remaining_spots: str
    hash: str
    url: str
    registration_time: str  # 新增报名时间字段

class Information:
    def __init__(self,headers):
        self.activate_info_urls = []
        self.activates_name = []
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
    def get_activate_urls(self,start_page=1,end_page=5):
        
        for activate_param in self.activate_params.values():  # 遍历所有分类
            for pages in range(start_page, end_page+1):  # 获取当前分类前5页的活动信息url
                url = f'https://pocketuni.net/index.php?app=event&mod=School&act=board&cat=all&cid={activate_param}&p={pages}'
                resp = requests.get(url, headers=self.headers)
                resp_tree = etree.HTML(resp.text)
                self.activate_info_urls.extend(resp_tree.xpath("/html/body/div[2]/div/div[3]/div[2]/div[1]/ul/li/div[2]/div[1]/a/@href"))  # 通过xpath获取活动信息url
                resp.close()
        return self.activate_info_urls
    
    
    def get_info_inside(self,index):
        self.active_info_list = []
        for url in self.activate_info_urls:
            status = self.is_active_status(url)
            if status == "报名已结束":
                continue
            remaining_spots = self.get_remaining_spots_inside(url)
            if remaining_spots == "0":
                continue
            console.print(f"正在获取第{index}个活动信息")
            active = activate_info(
                index,
                self.get_activate_name_inside(url),
                self.get_activity_location_inside(url),
                remaining_spots,
                "",  # hash
                url,
                self.get_registration_time(url)  # 添加报名时间
            )
            self.active_info_list.append(active)
            index += 1
        return self.active_info_list
        
        
    def get_activate_name_inside(self,activate_info_url):
        activate_name = "空"
        resp = requests.get(activate_info_url, headers=self.headers)
        resp_tree = etree.HTML(resp.text)
        for name in self.re_expression.activity_name.findall(resp.text):
            activate_name = name
        resp.close()
        return activate_name
    
    def get_search_activate_urls(self,start_page=1,end_page=5,keyword="三江讲堂"):
        for pages in range(start_page, end_page+1):  # 获取当前分类前5页的活动信息url
            
            url = f'https://pocketuni.net/index.php?app=event&mod=School&act=board&titkey={keyword}&cid=2134&p={pages}'
            resp = requests.get(url, headers=self.headers)
            resp_tree = etree.HTML(resp.text)
            self.activate_info_urls.extend(resp_tree.xpath("/html/body/div[2]/div/div[3]/div[2]/div[1]/ul/li/div[2]/div[1]/a/@href"))  # 通过xpath获取活动信息url
            resp.close()

        return self.activate_info_urls
    def get_remaining_spots_inside(self,activate_info_url):
        remaining_spots = None
        resp = requests.get(activate_info_url, headers=self.headers)
        for spots in self.re_expression.remaining_spots.findall(resp.text):
            if ("br" in spots):
                spots = "0"
            remaining_spots = spots
        resp.close()
        return remaining_spots
    
    
    def get_activity_location_inside(self,activate_info_url):
        activity_location = "空"
        resp = requests.get(activate_info_url, headers=self.headers)
        resp_tree = etree.HTML(resp.text)
        for location in self.re_expression.activity_location.findall(resp.text):
            activity_location = location
        resp.close()
        return activity_location
    
    
    def is_active_status(self,activate_info_url):
        resp = requests.get(activate_info_url.replace("act=index","act=join"), headers=self.headers)
        resp.close()
        if "报名已结束" in resp.text:
            return "报名已结束"
        
        
    def get_sanjiang_lecture(self):
        self.get_activate_by_keyword("三江讲堂")

        
        
    def get_activate_by_keyword(self, keyword):
        index = 1
        pages = 1
        while True:
            self.get_search_activate_urls(pages, pages+5, keyword)
            if not self.activate_info_urls:
                console.print("没有更多活动信息", style="yellow")
                break

            for url in self.activate_info_urls:
                console.print(f"正在获取第{index}个活动信息")
                remaining_spots = self.get_remaining_spots_inside(url)
                
                active = activate_info(
                    index,
                    self.get_activate_name_inside(url),
                    self.get_activity_location_inside(url),
                    remaining_spots,
                    "",  # hash
                    url,
                    self.get_registration_time(url)
                )
                
                self.active_info_list.append(active)
                
                index += 1
            self.display_static(self.active_info_list)
            if not self.active_info_list:
                console.print("此页活动报名已满或没有符合条件的活动", style="yellow")
            
            choice = console.input("\n是否显示下一页? (y/n): ").lower()
            if choice != 'y':
                break
            while True:
                choice = console.input("\n输入活动序号添加到抢课列表，输入'n'显示下一页，输入'q'退出: ").lower()
                if choice == 'n':
                    break
                elif choice == 'q':
                    return 
                elif choice.isdigit():
                    choice = int(choice)
                    if 1<=choice<=len(self.active_info_list):
                        self.apply_list.append(self.active_info_list[choice-1])
                    
            pages += 5


    
    def get_registration_time(self,activate_info_url):
        resp = requests.get(activate_info_url.replace("act=index","act=join"), headers=self.headers)
        resp.close()
        registration_time = "可报名"
        for time in re_expression.registration_time.findall(resp.text):
            registration_time = time
        return registration_time
    
    
    
    def display_static(self, active_info_list):
        table = Table(title="最近五页活动信息")
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
        
        
def display_dynamic(imf):
    table = Table(title="活动信息")
    table.add_column("活动序号", style="cyan", no_wrap=True)
    table.add_column("活动名称", style="cyan", no_wrap=True)
    table.add_column("活动地点", style="magenta")
    table.add_column("剩余名额", justify="right", style="green")
    table.add_column("报名时间", style="yellow")  # 新增报名时间列
    index = 1
    with Live(table, refresh_per_second=10) as live:
        for url in imf.activate_info_urls:
            if imf.is_active_status(url) == "报名已结束":
                continue
            activity = activate_info(
                index,
                imf.get_activate_name(url),
                imf.get_activity_location(url),
                imf.get_remaining_spots(url),
                "",
                url,
                imf.get_registration_time(url)  # 添加报名时间
            )
            imf.active_info_list.append(activity)
            index += 1
            table.add_row(
                str(activity.index),
                activity.name,
                activity.location,
                activity.remaining_spots,
                activity.registration_time,  # 添加报名时间
            )
            
            live.update(table)

if __name__ == "__main__":
    headers={
    "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "cookie":"PHPSESSID=2c9050bb6506fbc2d17f7;TS_LOGGED_USER=r0TD2VED6QKnwVYLxOqz4WEza;TS_oauth_token=5f43072744bd6cd0f5c36a09bda612f9;TS_oauth_token_secret=cd434990c3f91733d787b5fda58bcdc6;TS_think_language=zh-CN;"
}


    with open(f"{os.getcwd()}/cookie.txt", "r") as f:
        headers["cookie"] = f.read()
    imf = Information(headers)
    urls = imf.get_activate_urls(1,1)
    imf.get_info_inside()
    imf.display_static(imf.active_info_list)