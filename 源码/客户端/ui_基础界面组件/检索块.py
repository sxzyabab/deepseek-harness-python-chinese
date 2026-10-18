from .头尾封顶 import 头尾封顶#高度封顶
from .复制反馈 import 复制反馈#复制反馈

样式表='''
.检索块{position:relative;margin:16px 0;color:var(--dsw-alias-label-primary);background:var(--dsw-alias-markdown-code-block);border-radius:var(--dsw-radius-lg);display:flex;flex-direction:column}
.检索块 .摘要{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font:var(--dsw-font-xs-13);color:var(--dsw-alias-label-secondary)}
'''

__all__=['检索块','处理检索块','默认检索最大行','复制文本','显示计数','摘要文案','展平行','样式表']#仅中文公开名

默认检索最大行=16#与终端同预算

def 复制文本(属性):
    '不受封顶/折叠影响。属性为 dict'
    if ('kind' in 属性) and 属性['kind']=='paths':#路径形
        路径=属性['paths'] if 'paths' in 属性 and 属性['paths'] is not None else []#路径
        return '\n'.join(路径)#路径
    块=[]#文件块
    文件列表=属性['files'] if 'files' in 属性 and 属性['files'] is not None else []#文件
    for 文件 in 文件列表:#逐文件
        行=[文件['path'] if 'path' in 文件 and 文件['path'] is not None else '']#路径头
        匹配列表=文件['matches'] if 'matches' in 文件 and 文件['matches'] is not None else []#匹配
        for 匹配 in 匹配列表:#匹配
            号=匹配['lineNumber'] if 'lineNumber' in 匹配 else None#号
            文=匹配['line'] if 'line' in 匹配 and 匹配['line'] is not None else ''#文
            行.append(str(号)+': '+str(文))#行
        块.append('\n'.join(行))#一块
    return '\n\n'.join(块)#拼

def 显示计数(属性):
    'matches=匹配行总和；paths=路径数'
    if ('kind' in 属性) and 属性['kind']=='paths':#路径
        路径=属性['paths'] if 'paths' in 属性 and 属性['paths'] is not None else []#路径
        return len(路径)#数
    总=0#累
    文件列表=属性['files'] if 'files' in 属性 and 属性['files'] is not None else []#文件
    for 文件 in 文件列表:#文件
        匹配列表=文件['matches'] if 'matches' in 文件 and 文件['matches'] is not None else []#匹配
        总+=len(匹配列表)#匹配
    return 总#数

def 摘要文案(属性,显示,截断,总计):
    '截断时 显示 X / 共 N'
    计数=('显示 '+str(显示)+' / 共 '+str(总计)) if 截断 is True else str(显示)#计数子句
    if ('kind' in 属性) and 属性['kind']=='paths':#路径
        return 计数+' 个路径'#路径单位
    文件列表=属性['files'] if 'files' in 属性 and 属性['files'] is not None else []#文件
    return 计数+' 处匹配 · '+str(len(文件列表))+' 个文件'#匹配单位

def 展平行(属性,已折叠):
    '折叠文件组丢掉其 match 行'
    if ('kind' in 属性) and 属性['kind']=='paths':#路径形
        路径=属性['paths'] if 'paths' in 属性 and 属性['paths'] is not None else []#路径
        出=[]#行
        for 径 in 路径:#路径
            出.append({'type':'path','path':径})#路径行
        return 出#路径行
    行列表=[]#累
    文件列表=属性['files'] if 'files' in 属性 and 属性['files'] is not None else []#文件
    for 索引,文件 in enumerate(文件列表):#分组
        折=索引 in 已折叠#折
        匹配列表=文件['matches'] if 'matches' in 文件 and 文件['matches'] is not None else []#匹配
        行列表.append({'type':'file','path':文件['path'] if 'path' in 文件 and 文件['path'] is not None else '','count':len(匹配列表),'index':索引,'collapsed':折})#头
        if 折 is True:#折起
            continue#跳匹配
        for 匹配 in 匹配列表:#匹配行
            行号=匹配['lineNumber'] if 'lineNumber' in 匹配 else None#号
            行列表.append({'type':'match','lineNumber':行号,'line':匹配['line'] if 'line' in 匹配 and 匹配['line'] is not None else '','key':str(索引)+':'+str(行号),'fileIndex':索引})#匹配
    return 行列表#扁

def 行键(行):
    '类型前缀防撞'
    种=行['type']#种
    if 种=='match':#匹配
        return 'match:'+行['key']#键
    if 种=='file':#文件
        return 'file:'+str(行['index'])#键
    return 'path:'+行['path']#路径

def 处理检索块(window,属性):
    '画出摘要、路径或匹配行。有 parent 就挂上去'
    文档=window.document
    if 文档.getElementById('检索块样式') is None:
        样式=文档.createElement('style')
        样式.id='检索块样式'
        样式.textContent=样式表
        文档.head.appendChild(样式)
    组件=属性['组件']
    截断=属性['truncated'] is True if 'truncated' in 属性 else False#截断
    总计=属性['total'] if 'total' in 属性 else 0#总计
    最大=属性['maxLines'] if 'maxLines' in 属性 else 默认检索最大行#封顶
    显示=显示计数(属性)#显示数
    组件.反馈.置文本(复制文本(属性))#可复制
    摘要=摘要文案(属性,显示,截断,总计)#摘要
    根=文档.createElement('div')
    根.className='检索块'
    类名=属性['className'] if 'className' in 属性 else None#类
    if isinstance(类名,str) and 类名!='':
        根.className=根.className+' '+类名
    def 清空(节点):
        while 节点.firstElementChild is not None:
            节点.firstElementChild.remove()
    def 画检索行(行):
        '路径、文件头或匹配行'
        种=行['type']#种
        if 种=='path':#路径
            标=文档.createElement('div')
            标.textContent=行['path']
            根.appendChild(标)
            return
        if 种=='file':#文件
            文=行['path']+' ('+str(行['count'])+')'#文案
            索引=行['index']#索引
            def 点文件(事件,索引=索引):
                '折叠或展开这一组'
                组件.切换文件(索引)
                重画()
            钮=文档.createElement('button')
            钮.type='button'
            钮.textContent=文
            钮.addEventListener('click',点文件)
            根.appendChild(钮)
            return
        号=行['lineNumber']#号
        号文='' if 号 is None else str(号)#号
        标=文档.createElement('div')
        标.style.cssText='white-space:pre'
        标.textContent=号文+': '+行['line']
        根.appendChild(标)
    def 重画():
        '按展开和文件折叠重画'
        行列表=展平行(属性,组件.已折叠)#扁
        度量=头尾封顶(len(行列表),最大,组件.已展开)#度量
        头=行列表[:度量['headLines']] if 度量['capped'] is True else 行列表#头
        自然尾=行列表[len(行列表)-度量['tailLines']:] if 度量['capped'] is True else []#自然尾
        尾首=自然尾[0] if len(自然尾)>0 else None#尾首
        尾头=None#恢复的文件头
        if 尾首 is not None and ('type' in 尾首) and 尾首['type']=='match':#尾从匹配起
            文件索引=尾首['fileIndex']#属主
            头已带=False#头未带
            for 行 in 头:#扫头
                if ('type' in 行) and 行['type']=='file' and ('index' in 行) and 行['index']==文件索引:#头已带
                    头已带=True
                    break
            if 头已带 is False:#头未带
                for 行 in 行列表:#找头
                    if ('type' in 行) and 行['type']=='file' and ('index' in 行) and 行['index']==文件索引:#命中
                        尾头=行#恢复
                        break
        尾=自然尾[1:] if 尾头 is not None else 自然尾#占尾槽
        可见=list(头)#可见
        if 尾头 is not None:#补头
            可见.append(尾头)#头
        可见.extend(尾)#尾
        清空(根)
        if 度量['hidden']>0:#可切换
            def 点切换(事件):
                '展开或收起'
                组件.切换展开()
                重画()
            钮=文档.createElement('button')
            钮.type='button'
            钮.className='摘要'
            钮.textContent=摘要
            钮.addEventListener('click',点切换)
            根.appendChild(钮)
        else:#未封顶
            标=文档.createElement('div')
            标.className='摘要'
            标.textContent=摘要
            根.appendChild(标)
        for 行 in 可见:#逐行
            画检索行(行)#画
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

class 检索块:#检索卡
    'kind=matches|paths；本地展开与文件折叠集'
    def __init__(自身,属性=None,**关键字参数):
        '合并 props。构造不画'
        自身.属性=dict(属性 if 属性 is not None else {})#基础
        自身.属性.update(关键字参数)#覆盖
        自身.已展开=False#展开
        自身.已折叠=set()#折叠文件索引
        自身.反馈=复制反馈()#复制
        自身.根=None

    def 更新(自身,属性):
        '刷新'
        自身.属性=dict(属性)#最新

    def 切换展开(自身):
        '翻转'
        自身.已展开=not 自身.已展开#翻

    def 切换文件(自身,索引):
        '翻转一组'
        if 索引 in 自身.已折叠:#已折
            自身.已折叠.discard(索引)#开
        else:#未折
            自身.已折叠.add(索引)#折

    def 渲染(自身):
        '拆掉旧卡，再画一次'
        if 自身.根 is not None:
            自身.根.remove()
        绘制=dict(自身.属性)
        绘制['组件']=自身
        自身.根=处理检索块(自身.属性['window'],绘制)
        return 自身.根

    def __call__(自身,属性=None,**关键字参数):
        '对齐 React'
        if 属性 is not None or len(关键字参数)>0:#有；判 length
            合并=dict(属性 if 属性 is not None else {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()