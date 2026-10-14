from .消息铬 import 格式化延迟秒,格式化消息时钟,格式化运行时长,格式化每秒令牌,本地日起点#时钟辅助
import time as 时间模块#墙钟
from ....基础设施.通用工具 import 启动守护线程

__all__=['消息图标动作','日历日']#仅中文公开名

from nicegui import ui as 界面
from .文案 import 中文 as 对话文案
from ..异常 import 页面失败文案,贴出失败

def 恒等翻译(键,参数=None):
    '无文案表时返回键本身'
    return 键#键即文案

def 日历日(现在=None):
    '对齐 useCalendarDay 的当前值面（无定时器）'
    if 现在 is None:#缺省
        现在=int(时间模块.time()*1000)#毫秒
    return 本地日起点(现在)#午夜

class 消息图标动作:
    '共享用户与助手铬'

    def __init__(自身,属性=None):
        '记下 props 与复制态'
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.已复制=False#成功铬
        自身.复制中=False#防重入
        自身.画面=None#可反复清空的画面
        自身.刷新画面=None#复制成功后重画

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性 if 属性 is not None else {}#新

    def 复制(自身):
        '成功则短时勾'
        if 自身.已复制 is True or 自身.复制中 is True:#忙
            return#停
        文本=自身.属性['text'] if 'text' in 自身.属性 and 自身.属性['text'] is not None else ''#文本
        写=自身.属性['writeClipboard'] if 'writeClipboard' in 自身.属性 else None#宿主写
        自身.复制中=True#闩
        def 完成(成功):
            '成功亮勾'
            自身.复制中=False#清
            if 成功 is True:#成
                自身.已复制=True#勾
            if 自身.刷新画面 is not None:#勾要立刻重画
                自身.刷新画面()#重画
        if 写 is None:#无宿主则视为成功（视图层自接）
            完成(True)#成
            return#停
        结果=写(文本)#写
        def 观察():
            '等待剪贴板任务'
            成功=False#默认失败
            try:#等待
                成功=结果.等待() is True#结算
            finally:#无论成败
                完成(成功)#收尾
        启动守护线程(观察)#挂观察

    def 清除复制铬(自身):
        '1s 窗后调用'
        自身.已复制=False#清

    def 渲染(自身):
        '画出时钟、复制、额外动作和分支。'
        属性=自身.属性#props
        原译=属性['t'] if 't' in 属性 and 属性['t'] is not None else None#宿主文案
        def 翻译(键,参数=None):
            '属性上的 t 优先，否则用本包中文词典。'
            if 原译 is not None:#宿主
                if 参数 is None:#无参数
                    return 原译(键)#译
                return 原译(键,参数)#带参数
            if 键 not in 对话文案:#词典没有
                return 键#键
            文本=对话文案[键]#词条
            if 参数 is None:#无参数
                return 文本#原文
            for 名 in 参数:#替换占位
                文本=文本.replace('{'+名+'}',str(参数[名]))#替换
            return 文本#译完
        时间=属性['time'] if 'time' in 属性 else None#时刻
        日=属性['calendarDay'] if 'calendarDay' in 属性 else None#日席
        if 日 is None:#缺省
            日=日历日()#本日
        段=[]#时钟段
        if 时间 is not None:#有时
            段.append(格式化消息时钟(时间,翻译,日))#时钟
            运行=属性['runMs'] if 'runMs' in 属性 else None#运行
            if 运行 is not None:#有
                段.append(翻译('message.ranFor',{'duration':格式化运行时长(运行,翻译)}))#时长
            首=属性['ttftMs'] if 'ttftMs' in 属性 else None#TTFT
            if 首 is not None:#有
                段.append(翻译('message.ttft',{'seconds':格式化延迟秒(首)}))#TTFT
            吞吐=属性['tokensPerSecond'] if 'tokensPerSecond' in 属性 else None#吞吐
            if 吞吐 is not None:#有
                段.append(翻译('message.tokensPerSecond',{'tps':格式化每秒令牌(吞吐)}))#吞吐
        不可分支=属性['branchUnavailable'] is True if 'branchUnavailable' in 属性 else False#不可
        分支回调=属性['onBranch'] if 'onBranch' in 属性 else None#分支
        额外=属性['extraActions'] if 'extraActions' in 属性 else None#额外
        布局类=属性['className'] if 'className' in 属性 and 属性['className'] not in (None,'') else '消息图标动作'#布局类
        自身.画面失败=None
        if 自身.画面 is not None:
            try:
                自身.画面.clear()
            except Exception as 错误:
                自身.画面=None
                自身.画面失败=页面失败文案(错误)
        if 自身.画面 is None:#新建
            自身.画面=界面.row().classes(布局类)#行
        def 重画():
            '按当前复制态重画这一行。'
            自身.画面.clear()#清空
            with 自身.画面:#行内
                贴出失败(自身)
                if len(段)>0:#有时钟
                    界面.label(' · '.join(段)).classes('时钟')#时钟
                复制文=翻译('copied') if 自身.已复制 is True else 翻译('copy')#复制标
                def 点复制():
                    '写入剪贴板。'
                    自身.复制()#复制
                复制钮=界面.button(on_click=点复制).props('flat round aria-label="'+复制文+'"').classes('消息钮')#复制
                with 复制钮:
                    界面.html('<svg width="15" height="15" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M5.5 2.5H12.5C13.0523 2.5 13.5 2.94772 13.5 3.5V10.5C13.5 11.0523 13.0523 11.5 12.5 11.5H5.5C4.94772 11.5 4.5 11.0523 4.5 10.5V3.5C4.5 2.94772 4.94772 2.5 5.5 2.5Z" stroke="currentColor" stroke-width="1"/><path d="M2.5 5.5V12.5C2.5 13.0523 2.94772 13.5 3.5 13.5H10.5" stroke="currentColor" stroke-width="1"/></svg>',sanitize=False)
                if isinstance(额外,list):#额外按钮
                    for 项 in 额外:#逐个
                        标=项['label'] if isinstance(项,dict) and 'label' in 项 else None#标
                        回调=项['onClick'] if isinstance(项,dict) and 'onClick' in 项 else None#回调
                        if 标 is None:#无标
                            continue#跳
                        def 点额外(钉回调=回调):
                            '点额外动作。'
                            if 钉回调 is not None:#有
                                钉回调()#点
                        界面.button(标,on_click=点额外).props('flat no-caps aria-label="'+标+'"').classes('消息钮')#按钮
                if 分支回调 is not None:#有分支
                    分支文=翻译('message.branchUnavailable') if 不可分支 is True else 翻译('message.branch')#标
                    def 点分支():
                        '可分支时交给宿主。'
                        if 不可分支 is True:#不可
                            return#停
                        分支回调()#叉
                    界面.button(分支文,on_click=点分支).props('flat no-caps aria-label="'+分支文+'"').classes('消息钮')#分支
        自身.刷新画面=重画#复制完成后重画
        重画()#画

    def __call__(自身,属性=None):
        '对齐 React'
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
