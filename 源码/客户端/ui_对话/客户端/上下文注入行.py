from .上下文体 import 上下文体,通知摘要#按 form 选体；通知折叠摘要

__all__=['上下文注入行']#仅中文公开名

from nicegui import ui as 界面
from .文案 import 中文 as 对话文案
from ..异常 import 页面失败文案,贴出失败

def 恒等翻译(键,参数=None):
    '无文案表时返回键本身'
    return 键#键即文案

class 上下文注入行:
    '折叠披露；体按已解析 form，缺席走不透明'

    def __init__(自身,属性=None):
        '记下 props、开态与体'
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.打开=False#开
        自身.体=上下文体()#展开体
        自身.画面=None#可反复清空的画面

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性 if 属性 is not None else {}#新

    def 切换(自身):
        '翻转'
        自身.打开=not 自身.打开#翻

    def 渲染(自身):
        '画出折叠标题；展开后由上下文体自己画。'
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
        出处=属性['provenance'] if 'provenance' in 属性 and 属性['provenance'] is not None else {}#出处
        形态=属性['form'] if 'form' in 属性 else None#form 声明
        内容=属性['content'] if 'content' in 属性 else None#内容
        源=属性['source'] if 'source' in 属性 else None#源
        角色=出处['role'] if 'role' in 出处 else None#角色
        题键='message.contextRecall' if 角色=='recall' else 'message.contextInjection'#题
        标签=出处['label'] if 'label' in 出处 else None#生产者
        摘要=通知摘要(源) if 形态=='notice' else None#折叠摘要
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
            '按开合重画。'
            自身.画面.clear()#清空
            with 自身.画面:#行
                贴出失败(自身)
                def 点切换():
                    '翻转开合。'
                    自身.切换()#翻
                    重画()#重画
                界面.button(翻译(题键),on_click=点切换)#标题
                if 标签 is not None:#生产者
                    界面.label(str(标签))#源
                if 摘要 is not None:#折叠摘要
                    界面.label(摘要)#摘要
                if 自身.打开 is True:#展开
                    自身.体.更新({'content':内容,'source':源,'form':形态,'t':翻译})#灌入
                    自身.体.渲染()#自己画
        重画()#画

    def __call__(自身,属性=None):
        '对齐 React'
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
