import re
from dataclasses import dataclass

@dataclass
class re_expression:
    # 匹配活动地点的正则表达式
    activity_location = re.compile(".*? <span class=\"b1\">活动地点：</span><a title=\"(?P<area>.*?)\">")
    
    # 匹配活动名称的正则表达式
    activity_name = re.compile(".*?<title>(?P<name>.*?)</title>")
    
    # 匹配剩余名额的正则表达式
    remaining_spots = re.compile(".*?<span class=\"b1\">剩余名额：</span>\n(?P<number>.*?)<br />")
    
    # 匹配隐藏参数哈希值的正则表达式
    hash_param = re.compile(r'<input type="hidden" name="__hash__" value="(?P<hash>.*?)"')

    # 匹配活动报名时间的正则表达式
    registration_time = re.compile(r'.*?报名时间：(?P<time>.*?)<div class="b">')