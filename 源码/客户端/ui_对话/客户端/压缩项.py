__all__=['压缩项']#仅中文公开名

from nicegui import ui as 界面
from .文案 import 中文 as 对话文案
from ..异常 import 页面失败文案,贴出失败

def 恒等翻译(键,参数=None):
    '无文案表时返回键本身'
    return 键#键即文案

class 压缩项:
    '默认可折叠；无 summary 不可展开'

    def __init__(自身,属性=None):
        '记下 props 与展开'
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.已展开=False#展开
        自身.画面=None#可反复清空的画面

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性 if 属性 is not None else {}#新

    def 切换(自身):
        '可展开才翻'
        节点=自身.属性['node'] if 'node' in 自身.属性 and 自身.属性['node'] is not None else {}#节点
        if 'summary' not in 节点 or 节点['summary'] is None:#不可
            return#停
        自身.已展开=not 自身.已展开#翻

    def 渲染(自身):
        '画出压缩标记；没有摘要时用不可用句。'
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
        节点=属性['node'] if 'node' in 属性 and 属性['node'] is not None else {}#节点
        标题=属性['title'] if 'title' in 属性 else None#命令题
        回退摘要=属性['fallbackSummary'] if 'fallbackSummary' in 属性 else None#回退
        可展='summary' in 节点 and 节点['summary'] is not None#可展
        项数=节点['shadowedItemCount'] if 'shadowedItemCount' in 节点 else None#项
        令牌=节点['shadowedTokenCount'] if 'shadowedTokenCount' in 节点 else None#令牌
        if 项数 is not None and 令牌 is not None:#有计数
            摘要=翻译('message.compaction.completed',{'items':项数,'tokens':令牌})#完成
        elif 回退摘要 is not None:#回退
            摘要=回退摘要#回退
        elif 可展 is True:#可展
            摘要=翻译('message.compaction.expand')#展开提示
        else:#不可用
            摘要=翻译('message.compaction.unavailable')#不可用
        题出=标题 if 标题 is not None else 翻译('message.compaction')#题
        自身.画面失败=None
        if 自身.画面 is not None:
            try:
                自身.画面.clear()
            except Exception as 错误:
                自身.画面=None
                自身.画面失败=页面失败文案(错误)
        if 自身.画面 is None:#新建
            自身.画面=界面.column().classes('压缩项')#项
        def 重画():
            '按展开态重画。'
            自身.画面.clear()#清空
            打开=可展 is True and 自身.已展开 is True#开
            with 自身.画面:#项
                贴出失败(自身)
                def 点切换():
                    '可展开才翻转。'
                    自身.切换()#翻
                    重画()#重画
                if 可展 is True:#可点
                    界面.button(题出,on_click=点切换)#题
                else:#不可点
                    界面.label(题出)#题
                界面.label(摘要)#摘要
                if 打开 is True and 'summary' in 节点 and 节点['summary'] is not None:#体
                    界面.label(str(节点['summary'])).classes('正文')#体
        重画()#画

    def __call__(自身,属性=None):
        '对齐 React'
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
