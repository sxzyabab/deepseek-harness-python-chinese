from .头尾封顶 import 头尾封顶#高度封顶
from .复制反馈 import 复制反馈#复制反馈

样式表='''
.差异块{overflow:hidden;font:var(--dsw-font-markdown-code-block);display:flex;flex-direction:column}
.差异行{box-sizing:border-box;min-height:1lh;padding:0 22px;white-space:pre}
.差异删{color:var(--dsw-alias-state-error-primary);background:var(--dsw-alias-code-diff-deleted);box-shadow:inset 3px 0 0 var(--dsw-alias-state-error-primary)}
.差异增{color:var(--dsw-alias-state-success-primary);background:var(--dsw-alias-code-diff-added);box-shadow:inset 3px 0 0 var(--dsw-alias-state-success-primary)}
.差异径{color:var(--dsw-alias-label-secondary);font-weight:500}
.差异隙{color:var(--dsw-alias-label-tertiary)}
'''

__all__=['差异块','处理差异块','默认差异最大行','内容行','建行','复制文本','样式表']#仅中文公开名

默认差异最大行=16#与终端块同预算

def 内容行(文本):
    '空=零行；尾换行是终止符不是空行'
    if 文本=='':#空
        return []#零
    体=文本[:-1] if 文本.endswith('\n') else 文本#剥终止符
    return 体.split('\n')#切

def 建行(差异列表):
    '路径头开新文件；同文件第二 hunk 用 ⋯ 缝。差异为 dict'
    行列表=[]#扁平行
    路径集=set()#去重路径
    增=0#加行
    删=0#删行
    前路径=None#上一路径
    for 项 in 差异列表:#逐 hunk
        路径=项['path'] if 'path' in 项 and 项['path'] is not None else ''#路径
        路径集.add(路径)#记
        if 路径!=前路径:#新文件
            行列表.append({'kind':'path','text':路径})#路径头
        else:#同文件缝
            行列表.append({'kind':'gap','text':'⋯'})#缝
        前路径=路径#更新
        旧=项['oldText'] if 'oldText' in 项 else None#旧侧
        if 旧 is not None:
            for 线 in 内容行(旧):#逐行
                行列表.append({'kind':'del','text':线})#删
                删+=1#计
        新=项['newText'] if 'newText' in 项 and 项['newText'] is not None else ''#新侧
        for 线 in 内容行(新):#逐行
            行列表.append({'kind':'add','text':线})#增
            增+=1#计
    return {'rows':行列表,'added':增,'removed':删,'files':len(路径集)}#结果

def 复制文本(行列表):
    '带 -/+ /路径/缝 前缀'
    出=[]#行
    for 行 in 行列表:#逐行
        种=行['kind']#种
        if 种=='del':#删
            出.append('- '+行['text'])#前缀
        elif 种=='add':#增
            出.append('+ '+行['text'])#前缀
        else:#路径或缝
            出.append(行['text'])#原文
    return '\n'.join(出)#拼接

def 处理差异块(window,属性):
    '建行并画出增删和页脚。空 diffs 返回 None。有 parent 就挂上去'
    文档=window.document
    if 文档.getElementById('差异块样式') is None:
        样式=文档.createElement('style')
        样式.id='差异块样式'
        样式.textContent=样式表
        文档.head.appendChild(样式)
    组件=属性['组件']
    差异列=属性['diffs'] if 'diffs' in 属性 else None#hunks
    差异列表=差异列 if 差异列 is not None else []#空则空表
    建成=建行(差异列表)#扁
    行列表=建成['rows']#行
    if len(行列表)==0:#空；判 length
        return None#不画
    最大=属性['maxLines'] if 'maxLines' in 属性 else 默认差异最大行#封顶
    组件.反馈.置文本(复制文本(行列表))#整卡可复制
    文件数=建成['files']#文件数
    脚='└ +'+str(建成['added'])+' -'+str(建成['removed'])+' · '+str(文件数)+' file'+('' if 文件数==1 else 's')#脚
    根=文档.createElement('div')
    根.className='差异块'
    类名=属性['className'] if 'className' in 属性 else None#类
    if isinstance(类名,str) and 类名!='':
        根.className=根.className+' '+类名
    类={'del':'差异行 差异删','add':'差异行 差异增','path':'差异行 差异径','gap':'差异行 差异隙'}#行类
    前缀={'del':'- ','add':'+ ','path':'','gap':''}#前缀
    def 清空(节点):
        while 节点.firstElementChild is not None:
            节点.firstElementChild.remove()
    def 画行(行组):
        '按种类画出一行'
        for 行 in 行组:#逐行
            种=行['kind']#种
            标=文档.createElement('div')
            标.className=类[种]
            标.textContent=前缀[种]+行['text']
            根.appendChild(标)
    def 重画():
        '按当前展开态重画'
        度量=头尾封顶(len(行列表),最大,组件.已展开)#度量
        头=行列表[:度量['headLines']] if 度量['capped'] is True else 行列表#头
        尾=行列表[len(行列表)-度量['tailLines']:] if 度量['capped'] is True else []#尾
        清空(根)
        画行(头)#头
        if 度量['hidden']>0:#可切换
            def 点切换(事件):
                '展开或收起'
                组件.切换展开()
                重画()
            钮=文档.createElement('button')
            钮.type='button'
            钮.textContent=脚
            钮.addEventListener('click',点切换)
            根.appendChild(钮)
        else:#未封顶
            脚标=文档.createElement('div')
            脚标.textContent=脚
            根.appendChild(脚标)
        if 度量['capped'] is True:#封顶
            画行(尾)#尾
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

class 差异块:#内联 diff 面
    '空 diffs 返回 None；展开态本地持有'
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
        '头尾封顶切换'
        自身.已展开=not 自身.已展开#翻

    def 渲染(自身):
        '拆掉旧卡，再画一次'
        if 自身.根 is not None:
            自身.根.remove()
        绘制=dict(自身.属性)
        绘制['组件']=自身
        自身.根=处理差异块(自身.属性['window'],绘制)
        return 自身.根

    def __call__(自身,属性=None,**关键字参数):
        '对齐 React'
        if 属性 is not None or len(关键字参数)>0:#有；判 length
            合并=dict(属性 if 属性 is not None else {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()