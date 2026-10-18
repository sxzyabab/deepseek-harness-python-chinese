import json#美化
__all__=['json块','处理json块','最大字节','默认截断标签']#仅中文公开名

最大字节=20000#UTF-8 字节封顶

def 默认截断标签(总计):
    '超出封顶时的脚'
    return '… 已截断，共 '+str(总计)+' 字节'#文案

def 按字节截(串,上限):
    'UTF-8 字节截断，切点落在字符边界'
    编码=串.encode('utf-8')#字节
    if len(编码)<=上限:#未超；判 length
        return 串#全
    切=编码[:上限]#截
    while len(切)>0:#回退到字符边界；判 length
        try:#解码
            return 切.decode('utf-8')#成
        except UnicodeDecodeError:#半字符
            切=切[:-1]#退一字节
    return ''#空

def 处理json块(window,属性):
    '画出标签，打开时画出 JSON 正文。有 parent 就挂上去'
    文档=window.document
    组件=属性['组件']
    截断标=属性['truncatedLabel'] if 'truncatedLabel' in 属性 else 默认截断标签#脚格式
    标签=属性['label'] if 'label' in 属性 and 属性['label'] is not None else ''#标签
    根=文档.createElement('div')
    根.className='json块'
    def 清空(节点):
        while 节点.firstElementChild is not None:
            节点.firstElementChild.remove()
    def 重画():
        '按打开态重画'
        体=''#体
        if 组件.已打开 is True:#开
            载荷=属性['payload'] if 'payload' in 属性 else None#载荷
            try:#stringify
                串=json.dumps(载荷,ensure_ascii=False,separators=(',',':'),allow_nan=False,indent=2)#美化
            except (TypeError,ValueError):#不可序列
                串=str(载荷)#回退
            字节=串.encode('utf-8')#字节
            if len(字节)>最大字节:#超
                脚=截断标(len(字节)) if callable(截断标) else 截断标#脚
                体=按字节截(串,最大字节)+'\n'+脚#截
            else:#全
                体=串#全
        清空(根)
        前='▾ ' if 组件.已打开 else '▸ '#开合
        def 点切换(事件):
            '开合正文'
            组件.切换()
            重画()
        钮=文档.createElement('button')
        钮.type='button'
        钮.textContent=前+标签
        钮.addEventListener('click',点切换)
        根.appendChild(钮)
        if 组件.已打开 is True and 体!='':
            预=文档.createElement('pre')
            码=文档.createElement('code')
            码.textContent=体
            预.appendChild(码)
            根.appendChild(预)
    重画()#首画
    if 'parent' in 属性:
        属性['parent'].appendChild(根)
    return 根

class json块:#可折叠 JSON
    '打开时 stringify；超封顶截断'
    def __init__(自身,属性=None,**关键字参数):
        '合并 props。构造不画'
        自身.属性=dict(属性 if 属性 is not None else {})#基础
        自身.属性.update(关键字参数)#覆盖
        自身.已打开=自身.属性['defaultOpen'] is True if 'defaultOpen' in 自身.属性 else False#默认开
        自身.根=None

    def 更新(自身,属性):
        '刷新'
        自身.属性=dict(属性)#最新

    def 切换(自身):
        '开合'
        自身.已打开=not 自身.已打开#翻

    def 渲染(自身):
        '拆掉旧块，再画一次'
        if 自身.根 is not None:
            自身.根.remove()
        绘制=dict(自身.属性)
        绘制['组件']=自身
        自身.根=处理json块(自身.属性['window'],绘制)
        return 自身.根

    def __call__(自身,属性=None,**关键字参数):
        '对齐 React'
        if 属性 is not None or len(关键字参数)>0:#有；判 length
            合并=dict(属性 if 属性 is not None else {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()
