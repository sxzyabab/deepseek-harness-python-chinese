from .节流视觉更新 import 节流视觉更新#摘要跟尾节流

__all__=['推理行','首行','末行']#仅中文公开名

from nicegui import ui as 界面
from .文案 import 中文 as 对话文案
from ..异常 import 页面失败文案,贴出失败

def 恒等翻译(键,参数=None):
    '无文案表时返回键本身'
    return 键#键即文案

def 首行(文本):
    '取第一行'
    换行=文本.find('\n')#换行
    return 文本 if 换行==-1 else 文本[:换行]#首行

def 末行(文本):
    '取末可见行'
    可见=文本.rstrip()#去尾空白
    换行=可见.rfind('\n')#末换行
    return 可见 if 换行==-1 else 可见[换行+1:]#末行

class 推理行:
    '流式跟末行；定稿取首行'

    def __init__(自身,属性=None):
        '记下 props、展开与摘要滚调度'
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.展开=False#展开
        自身.摘要滚=节流视觉更新(None)#宿主绑对齐后再调度
        自身.画面=None#可反复清空的画面

    def 更新(自身,属性):
        '刷新并请求摘要滚'
        自身.属性=属性 if 属性 is not None else {}#新
        自身.摘要滚.调度()#跟尾/回零

    def 设摘要滚(自身,对齐):
        '每次渲染写最新对齐回调'
        自身.摘要滚.设更新(对齐)#绑
        自身.摘要滚.调度()#排

    def 切换(自身):
        '翻转'
        自身.展开=not 自身.展开#翻

    def 渲染(自身):
        '画出 Think 摘要；展开后显示全文。'
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
            文本词=对话文案[键]#词条
            if 参数 is None:#无参数
                return 文本词#原文
            for 名 in 参数:#替换占位
                文本词=文本词.replace('{'+名+'}',str(参数[名]))#替换
            return 文本词#译完
        文本=属性['text'] if 'text' in 属性 and 属性['text'] is not None else ''#文
        运行中=属性['running'] is True if 'running' in 属性 else False#流式
        摘要=末行(文本) if 运行中 is True else 首行(文本)#摘要
        自身.摘要滚.调度()#跟 running/summary
        自身.画面失败=None
        if 自身.画面 is not None:
            try:
                自身.画面.clear()
            except Exception as 错误:
                自身.画面=None
                自身.画面失败=页面失败文案(错误)
        if 自身.画面 is None:#新建
            自身.画面=界面.column().classes('root')#行
        def 重画():
            '按展开态重画。'
            自身.画面.clear()#清空
            with 自身.画面:#行
                贴出失败(自身)
                if 运行中 is True:#跑
                    界面.label(翻译('row.running'))#无障碍
                def 点切换():
                    '翻转全文。'
                    自身.切换()#翻
                    重画()#重画
                界面.button('Think',on_click=点切换)#标题
                if 摘要=='':#没有可见摘要
                    pass#折叠行保持标题
                else:#摘要
                    界面.label(摘要)#摘要
                if 自身.展开 is True and 文本=='':#展开但没有正文
                    pass#不另造空句
                elif 自身.展开 is True:#全文
                    界面.label(文本).classes('正文')#体
        重画()#画

    def __call__(自身,属性=None):
        '对齐 React'
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
