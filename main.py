import os
from rich.console import Console, Group
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from get_information import Information
from console_manager import console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

url_headers={
    "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "cookie":""
}


def get_activities():
    page = 1
    index = 1
    while True:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
        ) as progress:
            task1 = progress.add_task("[green]获取活动URL...", total=100)
            task2 = progress.add_task("[cyan]获取活动信息...", total=100)
            imf = Information(url_headers)
            progress.update(task1, advance=50)
            imf.get_activate_urls(page, page + 1)
            progress.update(task1, completed=100)
            progress.update(task2, advance=50)
            imf.get_info_inside(index)
            progress.update(task2, completed=100)
        imf.display_static(imf.active_info_list)
        if len(imf.active_info_list) == 0:
            console.print("没有活动信息或此页活动报名已满", style="yellow")
        else:
            index = imf.active_info_list[-1].index + 1
        choice = console.input("\n是否显示下一页? (y/n): ").lower()
        if choice != 'y':
            break
        page += 5

    

def get_cookie_manually():
    console.print("手动获取cookie功能尚未实现", style="yellow")

def get_sanjiang_lecture():
    imf = Information(url_headers)
    imf.get_sanjiang_lecture()
    imf.display_static(imf.active_info_list)

def configure_notifications():
    console.print("消息提示配置功能尚未实现", style="yellow")

def show_error_docs():
    console.print("异常文档功能尚未实现", style="yellow")

def main_menu():
    while True:
        title = Text("活动报名辅助工具v0.1", style="bold magenta")
        menu_items = Table.grid(padding=1)
        menu_items.add_column(style="cyan", justify="right")
        menu_items.add_column(style="green")
        
        menu_items.add_row("1.", "获取活动列表")
        menu_items.add_row("2.", "手动获取cookie")
        menu_items.add_row("3.", "获取所有三江讲堂活动")
        menu_items.add_row("4.", "等待报名的活动")
        menu_items.add_row("4.", "异常文档")
        menu_items.add_row("5.", "退出(直接关是一样的效果)")

        note = Text("\n提示: 如果一直获取不到活动，请删除cookie.txt文件，然后重新输入学号和密码获取cookie。", style="yellow italic")
        
        footer = Text("\n--by 小程", style="dim")

        content = Group(
            title,
            Text("\n"),
            menu_items,
            note,
            footer
        )

        panel = Panel(
            content,
            border_style="bright_blue",
            expand=False
        )
        
        console.print(panel)

        choice = console.input("请输入您的选择 (1-6): ")

        if choice == "1":
            get_activities()
        elif choice == "2":
            get_cookie_manually()
        elif choice == "3":
            get_sanjiang_lecture()
        elif choice == "4":
            configure_notifications()
        elif choice == "5":
            show_error_docs()
        elif choice == "6":
            console.print("感谢使用，再见！", style="bold green")
            break
        else:
            console.print("无效的选择，请重新输入。", style="bold red")

        console.input("\n按Enter键继续...")
        console.clear()

if __name__ == "__main__":
    
    try:
        with open(rf"{os.getcwd()}/cookie.txt", "r") as f:
            url_headers["cookie"] = f.read()
    except:
        error_message = Panel(
        Text(rf"cookie文件不存在,请回到主页手动获取cookie,当前目录{os.getcwd()}\cookie.txt", style="bold red"),border_style="red")
        console.print(error_message)
    
    main_menu()
    
    