'回合尾悬停预览和侧栏审阅共用的文件对比'
import os
import pywebbridge
from ...ui_对话.异常 import 注入模块样式文件,标样式模块
from ...ui_基础界面组件.按钮 import 按钮
from ...ui_基础界面组件.代码高亮语法 import 使用代码高亮器,路径语言
from .文案 import 中文,填入

__all__=['最大绘制行数','块行','分栏行','绘制块','产出文件']

样式模块='FileDiff'
样式路径=os.path.join(os.path.dirname(__file__),'产出文件.module.css')
最大绘制行数=5000


def 确保样式(文档):
    '对比样式只插一次'
    注入模块样式文件(文档,'dsh-file-diff',样式路径,样式模块)


def 元素(文档,标签,类名=None):
    '带官方类名和样式模块'
    节点=文档.createElement(标签)
    if isinstance(类名,str) and 类名!='':
        节点.className=类名
    return 标样式模块(节点,样式模块)


def 块行(块):
    '上下文两边计数，删除只计旧侧，新增只计新侧'
    旧号=块['oldStart']
    新号=块['newStart']
    行表=[]
    for 行 in 块['lines']:
        文本=行[1:]
        记号=行[0] if len(行)>0 else ''
        if 记号=='+':
            行表.append({'kind':'add','old':None,'new':新号,'text':文本})
            新号+=1
        elif 记号=='-':
            行表.append({'kind':'del','old':旧号,'new':None,'text':文本})
            旧号+=1
        else:
            行表.append({'kind':'context','old':旧号,'new':新号,'text':文本})
            旧号+=1
            新号+=1
    return 行表


def 分栏行(块):
    '一段删除和紧跟的新增按行对齐，上下文两边都有'
    行表=[]
    删除=[]
    新增=[]

    def 冲掉():
        '把攒下的删除和新增按行配对'
        长度=len(删除) if len(删除)>len(新增) else len(新增)
        下标=0
        while 下标<长度:
            左=删除[下标] if 下标<len(删除) else None
            右=新增[下标] if 下标<len(新增) else None
            一项={}
            if 左 is not None:
                一项['left']=左
            if 右 is not None:
                一项['right']=右
            行表.append(一项)
            下标+=1
        删除.clear()
        新增.clear()

    for 行 in 块行(块):
        if 行['kind']=='del':
            删除.append({'no':行['old'],'text':行['text'],'kind':'del'})
        elif 行['kind']=='add':
            新增.append({'no':行['new'],'text':行['text'],'kind':'add'})
        else:
            冲掉()
            行表.append({
                'left':{'no':行['old'],'text':行['text'],'kind':'context'},
                'right':{'no':行['new'],'text':行['text'],'kind':'context'},
            })
    冲掉()
    return 行表


def 绘制块(块表):
    '合计超过上限时截断最后一块'
    预算=最大绘制行数
    留下=[]
    for 块 in 块表:
        if 预算==0:
            return {'hunks':留下,'truncated':True}
        if len(块['lines'])<=预算:
            留下.append(块)
        else:
            截=dict(块)
            截['lines']=块['lines'][:预算]
            留下.append(截)
        本次=预算 if 预算<len(块['lines']) else len(块['lines'])
        预算-=本次
    截断=False
    下标=0
    while 下标<len(块表):
        现=留下[下标] if 下标<len(留下) else None
        if 现 is not 块表[下标]:
            截断=True
        下标+=1
    return {'hunks':留下,'truncated':截断}


def 高亮一侧(行表,侧,高亮器):
    '这一侧有行号的文本交给高亮器。没就绪就返回 None'
    源=[]
    for 行 in 行表:
        号=行[侧]
        if 号 is not None:
            源.append({'no':号,'text':行['text']})
    if len(源)==0:
        return {}
    高亮=高亮器('\n'.join(项['text'] for 项 in 源))
    if 高亮 is None:
        return None
    结果={}
    下标=0
    while 下标<len(源):
        片段=[]
        if isinstance(高亮,list) and 下标<len(高亮) and 高亮[下标] is not None:
            片段=高亮[下标]
        结果[源[下标]['no']]=片段
        下标+=1
    return 结果


def 分栏行种类(行):
    '任一侧是删除或新增就用那个种类，否则是上下文'
    左=行.get('left')
    右=行.get('right')
    if isinstance(左,dict) and 左.get('kind')=='del':
        return 'del'
    if isinstance(右,dict) and 右.get('kind')=='add':
        return 'add'
    return 'context'


def 块头(块):
    '统一差异的块头'
    return '@@ -'+str(块['oldStart'])+','+str(块['oldLines'])+' +'+str(块['newStart'])+','+str(块['newLines'])+' @@'


class 差异文本:
    '一行里的纯文本或高亮片段'
    def __init__(自身,属性):
        '记下文本和片段'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None

    def 渲染(自身):
        '没有片段就整段文本'
        文档=自身.属性['window'].document
        片段=自身.属性.get('spans')
        节点=元素(文档,'span','text')
        if 片段 is None:
            节点.textContent=自身.属性.get('text') or ''
        else:
            节点.setAttribute('data-diff-code','')
            for 段 in 片段:
                字=文档.createElement('span')
                if isinstance(段,dict):
                    字.textContent=段.get('text') or ''
                    样式=段.get('style')
                    if isinstance(样式,dict):
                        for 键,值 in 样式.items():
                            字.style.setProperty(str(键),str(值))
                    elif isinstance(样式,str) and 样式!='':
                        字.style.cssText=样式
                else:
                    字.textContent=str(段)
                节点.appendChild(字)
        自身.根=节点
        return 节点


class 分栏列:
    '不换行的左右两列，滚动锁在一起'
    def __init__(自身,属性):
        '记下块和高亮'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None

    def 渲染(自身):
        '两列各画块头和行'
        属性=自身.属性
        文档=属性['window'].document
        窗口=属性['window']
        块表=属性.get('hunks') or []
        高亮表=属性.get('highlights') or []
        配对=[]
        for 块 in 块表:
            配对.append({'header':块头(块),'rows':分栏行(块)})
        列={}
        偏移={'left':{'scrollLeft':0,'scrollTop':0},'right':{'scrollLeft':0,'scrollTop':0}}

        def 跟随(侧):
            '一侧滚动时把另一侧拨到同一位置'

            def 滚动(事件,侧=侧):
                '记下浏览器夹过的偏移，避免滚回来'
                对侧='right' if 侧=='left' else 'left'
                另一=列.get(对侧)
                if 另一 is None:
                    return
                源=事件.currentTarget
                for 轴 in ('scrollLeft','scrollTop'):
                    值=getattr(源,轴)
                    if 偏移[侧][轴]==值:
                        continue
                    偏移[侧][轴]=值
                    setattr(另一,轴,值)
                    偏移[对侧][轴]=getattr(另一,轴)

            return 滚动

        根=元素(文档,'div','columns')
        for 侧 in ('left','right'):
            列盒=元素(文档,'div','column')
            列盒.setAttribute('data-diff-side',侧)
            列[侧]=列盒
            列盒.addEventListener('scroll',跟随(侧))
            位置=0
            for 块 in 配对:
                节=元素(文档,'section','hunk')
                头=元素(文档,'div','hunkHeader')
                头.setAttribute('data-diff-hunk-header','')
                头.textContent=块['header']
                节.appendChild(头)
                行号=0
                for 行 in 块['rows']:
                    格=行.get(侧)
                    种类=分栏行种类(行)
                    类名='sideLine '
                    if 格 is None:
                        类名=类名+'empty'
                    else:
                        类名=类名+格['kind']
                    行盒=元素(文档,'div',类名)
                    行盒.setAttribute('data-diff-line',种类)
                    号=元素(文档,'span','number')
                    号.textContent='' if 格 is None else str(格['no'])
                    行盒.appendChild(号)
                    片段=None
                    if 格 is not None and 位置<len(高亮表):
                        侧名='old' if 侧=='left' else 'new'
                        侧表=高亮表[位置].get(侧名) if isinstance(高亮表[位置],dict) else None
                        if isinstance(侧表,dict):
                            片段=侧表.get(格['no'])
                    行盒.appendChild(差异文本({
                        'window':窗口,
                        'text':'' if 格 is None else 格['text'],
                        'spans':片段,
                    }).渲染())
                    节.appendChild(行盒)
                    行号+=1
                列盒.appendChild(节)
                位置+=1
            根.appendChild(列盒)
        自身.根=根
        return 根


class 文本对比:
    '文本对比的块，单栏或左右'
    def __init__(自身,属性):
        '记下对比和布局'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None

    def 渲染(自身):
        '说明、截断提示和块'
        属性=自身.属性
        文档=属性['window'].document
        窗口=属性['window']
        对比=属性['diff']
        左右=属性.get('split') is True
        换行=属性.get('wrap') is True
        if not 对比.get('before'):
            说明键='diff.created'
        elif not 对比.get('after'):
            说明键='diff.deleted'
        elif len(对比.get('hunks') or [])==0:
            说明键='diff.unchanged'
        else:
            说明键=None
        绘制=绘制块(对比.get('hunks') or [])
        块表=绘制['hunks']
        截断=绘制['truncated']
        高亮器=使用代码高亮器(路径语言(对比.get('path') or ''))
        高亮表=[]
        for 块 in 块表:
            行表=块行(块)
            高亮表.append({
                'old':高亮一侧(行表,'old',高亮器),
                'new':高亮一侧(行表,'new',高亮器),
            })
        根=元素(文档,'div','body')
        根.setAttribute('data-review-view','split' if 左右 else 'unified')
        if 换行:
            根.setAttribute('data-review-wrap','')
        if 说明键 is not None:
            说明=元素(文档,'p','note')
            说明.setAttribute('data-diff-note','empty' if len(块表)==0 else 'metadata')
            说明.textContent=中文[说明键]
            根.appendChild(说明)
        if 对比.get('coarse') is True:
            粗=元素(文档,'p','note')
            粗.setAttribute('data-diff-coarse','')
            粗.textContent=中文['diff.coarse']
            根.appendChild(粗)
        if 截断:
            截=元素(文档,'p','note')
            截.setAttribute('data-diff-truncated','')
            截.textContent=填入(中文['diff.truncated'],{'count':str(最大绘制行数)})
            根.appendChild(截)
        if 左右 and not 换行:
            根.appendChild(分栏列({
                'window':窗口,
                'hunks':块表,
                'highlights':高亮表,
            }).渲染())
        else:
            位置=0
            for 块 in 块表:
                高亮=高亮表[位置]
                节=元素(文档,'section','hunk')
                头=元素(文档,'div','hunkHeader')
                头.setAttribute('data-diff-hunk-header','')
                头.textContent=块头(块)
                节.appendChild(头)
                if 左右:
                    for 行 in 分栏行(块):
                        行盒=元素(文档,'div','splitLine')
                        行盒.setAttribute('data-diff-line',分栏行种类(行))
                        for 侧,侧名 in (('left','old'),('right','new')):
                            格=行.get(侧)
                            类名='cell '
                            if 格 is None:
                                类名=类名+'empty'
                            else:
                                类名=类名+格['kind']
                            格盒=元素(文档,'span',类名)
                            号=元素(文档,'span','number')
                            号.textContent='' if 格 is None else str(格['no'])
                            格盒.appendChild(号)
                            片段=None
                            if 格 is not None and isinstance(高亮.get(侧名),dict):
                                片段=高亮[侧名].get(格['no'])
                            格盒.appendChild(差异文本({
                                'window':窗口,
                                'text':'' if 格 is None else 格['text'],
                                'spans':片段,
                            }).渲染())
                            行盒.appendChild(格盒)
                        节.appendChild(行盒)
                else:
                    for 行 in 块行(块):
                        行盒=元素(文档,'div','line '+行['kind'])
                        行盒.setAttribute('data-diff-line',行['kind'])
                        旧号=元素(文档,'span','number')
                        旧号.textContent='' if 行['old'] is None else str(行['old'])
                        新号=元素(文档,'span','number')
                        新号.textContent='' if 行['new'] is None else str(行['new'])
                        记号=元素(文档,'span','sign')
                        if 行['kind']=='add':
                            记号.textContent='+'
                        elif 行['kind']=='del':
                            记号.textContent='-'
                        else:
                            记号.textContent=' '
                        行盒.appendChild(旧号)
                        行盒.appendChild(新号)
                        行盒.appendChild(记号)
                        if 行['kind']=='add':
                            片段=高亮.get('new').get(行['new']) if isinstance(高亮.get('new'),dict) else None
                        else:
                            片段=高亮.get('old').get(行['old']) if isinstance(高亮.get('old'),dict) else None
                        行盒.appendChild(差异文本({
                            'window':窗口,
                            'text':行['text'],
                            'spans':片段,
                        }).渲染())
                        节.appendChild(行盒)
                根.appendChild(节)
                位置+=1
        自身.根=根
        return 根


class 产出文件:
    '对比，或加载、缺失、失败、二进制、过大'
    def __init__(自身,属性):
        '记下对比状态'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None

    def 更新(自身,属性):
        '换上新的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 换成(自身,节点):
        '换根时留在原来的父节点里'
        旧=自身.根
        父=None if 旧 is None else 旧.parentNode
        if 旧 is not None and 旧 is not 节点:
            if 父 is not None:
                父.replaceChild(节点,旧)
            else:
                旧.remove()
        自身.根=节点
        return 节点

    def 渲染(自身):
        '按状态画说明或文本对比'
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        确保样式(文档)
        状态=属性.get('state')
        if 状态 is None or 状态=='loading':
            节点=元素(文档,'p','status')
            节点.setAttribute('role','status')
            节点.textContent=中文['diff.loading']
            return 自身.换成(节点)
        if 状态=='missing':
            节点=元素(文档,'p','status')
            节点.textContent=中文['diff.missing']
            return 自身.换成(节点)
        if 状态=='error':
            节点=元素(文档,'div','status')
            字=文档.createElement('span')
            字.textContent=中文['diff.error']
            节点.appendChild(字)
            重试=属性.get('retry')

            def 点重试():
                '再读一次对比'
                if callable(重试):
                    重试()

            节点.appendChild(按钮({
                'window':窗口,
                'size':'sm',
                'onClick':点重试,
                'children':中文['presented.retry'],
            }).渲染())
            return 自身.换成(节点)
        if not isinstance(状态,dict):
            节点=元素(文档,'p','status')
            节点.textContent=中文['diff.error']
            return 自身.换成(节点)
        if 状态.get('kind')=='binary':
            节点=元素(文档,'p','status')
            节点.textContent=中文['diff.binary']
            return 自身.换成(节点)
        if 状态.get('kind')=='oversized':
            节点=元素(文档,'p','status')
            节点.textContent=中文['diff.oversized']
            return 自身.换成(节点)
        有增=False
        有删=False
        for 块 in 状态.get('hunks') or []:
            for 行 in 块.get('lines') or []:
                if isinstance(行,str) and 行.startswith('+'):
                    有增=True
                elif isinstance(行,str) and 行.startswith('-'):
                    有删=True
        单侧=有增!=有删
        左右=属性.get('split') is True and not 单侧
        体=文本对比({
            'window':窗口,
            'diff':状态,
            'split':左右,
            'wrap':属性.get('wrap') is True,
        }).渲染()
        return 自身.换成(体)
