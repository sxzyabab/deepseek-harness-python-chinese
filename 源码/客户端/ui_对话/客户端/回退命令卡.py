
__all__=['回退命令卡','行状态','前导图标']#仅中文公开名

from nicegui import ui as 界面
from .文案 import 中文 as 对话文案
from ..异常 import 页面失败文案,贴出失败

def 恒等翻译(键,参数=None):
    '无文案表时返回键本身'
    return 键#键即文案

def 行状态(结果):
    '未结算 running；error/ok'
    if 结果 is None:#未结
        return 'running'#跑
    种类=结果['kind'] if 'kind' in 结果 else None#种类
    return 'error' if 种类=='error' else 'ok'#结

def 前导图标(状态):
    'error 用 StateDot；否则 api 图标'
    return 'error-dot' if 状态=='error' else 'api-icon'#图标

class 回退命令卡:
    'name · outcome；多行正文可展'

    def __init__(自身,属性=None):
        '记下 props 与展开'
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.展开=False#展
        自身.画面=None#可反复清空的画面

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性 if 属性 is not None else {}#新

    def 切换(自身):
        '翻转'
        自身.展开=not 自身.展开#翻

    def 渲染(自身):
        '画出命令名、状态和可展开正文。'
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
        节点=属性['node'] if 'node' in 属性 else None#命令节点
        跑摘要=属性['runningSummary'] if 'runningSummary' in 属性 else None#专属跑文
        结果=节点['outcome'] if 节点 is not None and 'outcome' in 节点 else None#结果
        正文=结果['text'] if 结果 is not None and 'text' in 结果 else None#文
        if 结果 is None:#跑
            摘要=跑摘要 if 跑摘要 is not None else 翻译('command.running')#摘要
        elif 正文 is not None:#有文
            摘要=正文#用文
        else:#无文
            种类=结果['kind'] if 'kind' in 结果 else None#种类
            摘要=翻译('command.failed') if 种类=='error' else 翻译('command.done')#结
        标题=节点['name'] if 节点 is not None and 'name' in 节点 else None#名
        if 标题 is None:#无
            标题=翻译('command.title')#默认
        状态=行状态(结果)#态
        体=正文 if 正文 is not None and '\n' in 正文 else None#多行体
        自身.画面失败=None
        if 自身.画面 is not None:
            try:
                自身.画面.clear()
            except Exception as 错误:
                自身.画面=None
                自身.画面失败=页面失败文案(错误)
        if 自身.画面 is None:#新建
            自身.画面=界面.column().classes('root')#卡
        def 重画():
            '按展开态重画。'
            自身.画面.clear()#清空
            开=自身.展开 is True and 体 is not None#开
            with 自身.画面:#卡
                贴出失败(自身)
                if 状态=='running':#跑
                    界面.label(翻译('row.running'))#无障碍
                elif 状态=='error':#败
                    界面.label(翻译('row.failed'))#无障碍
                def 点切换():
                    '多行正文才翻转。'
                    if 体 is None:#不可
                        return#停
                    自身.切换()#翻
                    重画()#重画
                if 体 is not None:#可展
                    界面.button(标题,on_click=点切换)#标题
                else:#标题
                    界面.label(标题)#标题
                界面.label(摘要)#摘要
                if 开 is True:#正文
                    界面.label(体).classes('正文')#体
        重画()#画

    def __call__(自身,属性=None):
        '对齐 React'
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
