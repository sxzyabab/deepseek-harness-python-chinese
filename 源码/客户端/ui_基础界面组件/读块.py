from .头尾封顶 import 头尾封顶#高度封顶
from .复制反馈 import 复制反馈#复制反馈

__all__=['读块','处理读块','默认读最大行']#仅中文公开名

默认读最大行=16#与终端同预算

样式表='''
.读块{margin:16px 0;color:var(--dsw-alias-label-primary);background:var(--dsw-alias-markdown-code-block);border-radius:var(--dsw-radius-lg);font:var(--dsw-font-markdown-code-block);overflow:auto;display:flex;flex-direction:column}
.读块 .行{display:flex;min-height:1lh;white-space:pre}
.读块 .槽{flex:none;margin-right:12px;text-align:right;color:var(--dsw-alias-label-tertiary);user-select:none}
.读块 .正文{white-space:pre}
'''

def 处理读块(window,属性):
    '画出标签、行号和正文。有 parent 就挂上去'
    文档=window.document
    if 文档.getElementById('读块样式') is None:
        样式=文档.createElement('style')
        样式.id='读块样式'
        样式.textContent=样式表
        文档.head.appendChild(样式)
    组件=属性['组件']
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
    组件.反馈.置文本(原文)#可复制
    窗口化=len(规范)<总行#窗口读；判 length
    根=文档.createElement('div')
    根.className='读块'
    类名=属性['className'] if 'className' in 属性 else None#类
    if isinstance(类名,str) and 类名!='':
        根.className=根.className+' '+类名
    块标签=属性['label'] if 'label' in 属性 else None#标签
    def 清空(节点):
        while 节点.firstElementChild is not None:
            节点.firstElementChild.remove()
    def 画行(行组):
        '行号加正文'
        for 行 in 行组:#逐行
            号=行['number']#号
            行盒=文档.createElement('div')
            行盒.className='行'
            槽=文档.createElement('span')
            槽.className='槽'
            槽.textContent='' if 号 is None else str(号)
            正文=文档.createElement('span')
            正文.className='正文'
            正文.textContent=行['text']
            行盒.appendChild(槽)
            行盒.appendChild(正文)
            根.appendChild(行盒)
    def 加重(文):
        标=文档.createElement('div')
        标.textContent=文
        根.appendChild(标)
    def 重画():
        '按当前展开态重画'
        度量=头尾封顶(len(规范),最大,组件.已展开)#度量
        头=规范[:度量['headLines']] if 度量['capped'] is True else 规范#头
        尾=规范[len(规范)-度量['tailLines']:] if 度量['capped'] is True else []#尾
        清空(根)
        if isinstance(块标签,str) and 块标签!='':#标签
            加重(块标签)
        if 语言 is not None:#语言
            加重(str(语言))
        if 窗口化 is True:#窗口
            加重('显示 '+str(len(规范))+' / '+str(总行)+' 行')
        画行(头)#头
        if 度量['hidden']>0:#可切换
            def 点切换(事件):
                '展开或收起'
                组件.切换展开()
                重画()
            钮=文档.createElement('button')
            钮.type='button'
            钮.textContent='… '+str(度量['hidden'])
            钮.addEventListener('click',点切换)
            根.appendChild(钮)
        if 度量['capped'] is True:#封顶
            画行(尾)#尾
        if len(规范)>0:#可复制
            def 点复制(事件):
                '写入剪贴板'
                组件.反馈.复制()
                重画()
            复制钮=文档.createElement('button')
            复制钮.type='button'
            复制钮.setAttribute('aria-label','content_copy')
            图=文档.createElement('span')
            图.className='材料图标'
            图.textContent='content_copy'
            复制钮.appendChild(图)
            复制钮.addEventListener('click',点复制)
            根.appendChild(复制钮)
    重画()#首画
    if 'parent' in 属性:
        属性['parent'].appendChild(根)
    return 根

class 读块:#读卡
    'banner+行号 gutter；复制写窗口原文'
    def __init__(自身,属性=None,**关键字参数):
        '合并 props。构造不画'
        自身.属性=dict(属性 if 属性 is not None else {})#基础
        自身.属性.update(关键字参数)#覆盖
        自身.已展开=False#展开
        自身.反馈=复制反馈()#复制
        自身.根=None

    def 更新(自身,属性):
        '刷新'
        自身.属性=dict(属性)#最新

    def 切换展开(自身):
        '封顶切换'
        自身.已展开=not 自身.已展开#翻

    def 渲染(自身):
        '拆掉旧卡，再画一次'
        if 自身.根 is not None:
            自身.根.remove()
        绘制=dict(自身.属性)
        绘制['组件']=自身
        自身.根=处理读块(自身.属性['window'],绘制)
        return 自身.根

    def __call__(自身,属性=None,**关键字参数):
        '对齐 React'
        if 属性 is not None or len(关键字参数)>0:#有；判 length
            合并=dict(属性 if 属性 is not None else {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()
