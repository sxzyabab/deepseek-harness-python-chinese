from nicegui import ui as 界面
from .头尾封顶 import 头尾封顶#高度封顶
from .复制反馈 import 复制反馈#复制反馈

__all__=['读块','默认读最大行']#仅中文公开名

默认读最大行=16#与终端同预算

样式已登记=False

def 登记样式():
    '同一段样式整个进程只登记一次'
    global 样式已登记
    if 样式已登记 is True:
        return
    界面.add_css('''
.读块{margin:16px 0;color:var(--dsw-alias-label-primary);background:var(--dsw-alias-markdown-code-block);border-radius:var(--dsw-radius-lg);font:var(--dsw-font-markdown-code-block);overflow:auto}
.读块 .行{display:flex;min-height:1lh;white-space:pre}
.读块 .槽{flex:none;margin-right:12px;text-align:right;color:var(--dsw-alias-label-tertiary);user-select:none}
''')
    样式已登记=True

class 读块:#读卡
    'banner+行号 gutter；复制写窗口原文'
    def __init__(自身,属性=None,**关键字参数):
        '合并 props'
        自身.属性=dict(属性 if 属性 is not None else {})#基础
        自身.属性.update(关键字参数)#覆盖
        自身.已展开=False#展开
        自身.反馈=复制反馈()#复制

    def 更新(自身,属性):
        '刷新'
        自身.属性=dict(属性)#最新

    def 切换展开(自身):
        '封顶切换'
        自身.已展开=not 自身.已展开#翻

    def 渲染(自身):
        '画出标签、行号和正文'
        登记样式()
        属性=自身.属性#props
        行列=属性['lines'] if 'lines' in 属性 else None#窗口行
        行列表=list(行列) if 行列 is not None else []#空则空表
        总行=属性['totalLines'] if 'totalLines' in 属性 else 0#文件总行
        最大=属性['maxLines'] if 'maxLines' in 属性 else 默认读最大行#封顶
        语言=属性['lang'] if 'lang' in 属性 else None#语法提示
        原文行=[]#原文
        规范=[]#规范行
        for 行 in 行列表:#逐行
            文=行['text'] if 'text' in 行 and 行['text'] is not None else ''#文
            原文行.append(文)#原文
            规范.append({'number':行['number'] if 'number' in 行 else None,'text':文})#规范行
        原文='\n'.join(原文行)#原文
        自身.反馈.置文本(原文)#可复制
        窗口化=len(规范)<总行#窗口读；判 length
        根=界面.column().classes('读块')#卡
        类名=属性['className'] if 'className' in 属性 else None#类
        if isinstance(类名,str) and 类名!='':
            根.classes(类名)#附
        块标签=属性['label'] if 'label' in 属性 else None#标签
        def 画行(行组):
            '行号加正文'
            for 行 in 行组:#逐行
                号=行['number']#号
                with 界面.row().classes('行'):
                    界面.label('' if 号 is None else str(号)).classes('槽')
                    界面.label(行['text']).classes('正文')
        def 重画():
            '按当前展开态重画'
            度量=头尾封顶(len(规范),最大,自身.已展开)#度量
            头=规范[:度量['headLines']] if 度量['capped'] is True else 规范#头
            尾=规范[len(规范)-度量['tailLines']:] if 度量['capped'] is True else []#尾
            根.clear()
            with 根:#内容
                if isinstance(块标签,str) and 块标签!='':#标签
                    界面.label(块标签)#标签
                if 语言 is not None:#语言
                    界面.label(str(语言))#语言
                if 窗口化 is True:#窗口
                    界面.label('显示 '+str(len(规范))+' / '+str(总行)+' 行')#计数
                画行(头)#头
                if 度量['hidden']>0:#可切换
                    def 点切换():
                        '展开或收起'
                        自身.切换展开()#翻
                        重画()#重画
                    界面.button('… '+str(度量['hidden']),on_click=点切换)#其余
                if 度量['capped'] is True:#封顶
                    画行(尾)#尾
                if len(规范)>0:#可复制
                    def 点复制():
                        '写入剪贴板'
                        自身.反馈.复制()#复制
                        重画()#重画
                    界面.button(icon='content_copy',on_click=点复制)#复制
        重画()#首画

    def __call__(自身,属性=None,**关键字参数):
        '对齐 React'
        if 属性 is not None or len(关键字参数)>0:#有；判 length
            合并=dict(属性 if 属性 is not None else {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()
