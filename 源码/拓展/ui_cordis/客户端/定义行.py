"""只读 cordis_define 卡：嵌套 JSX 结构树 + 样式串。

对齐上游 `ui-cordis/src/client/CordisDefineRow.tsx`。公开面仅中文名。
结构树字段/嵌套与上游 JSX 同构；DisclosureRow/CodeBlock/图标半需浏览器。
无法 JS·vm 执行：源码高亮与真实 DOM 展开动画。
"""
import os#读样式
from .卡片模型 import 定义卡片#卡模型
from .状态 import 可见状态#可见态

__all__=['定义行','读数标签','样式表','前导图标']#仅中文公开名

读数标签={#CardReading → 文案键
    'idle':'status.idle',
    'client-pending':'status.clientPending',
    'running':'status.running',
    'removed':'status.removed',
}#结束

_本目录=os.path.dirname(os.path.abspath(__file__))#本目录
with open(os.path.join(_本目录,'定义行.module.css'),'r',encoding='utf-8') as _样式文件:#原文
    样式表=_样式文件.read()#全文

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 状态文案键(态):#无障碍
    """running/error/stopped → 文案键。"""
    if 态=='running':#定义中
        return 'a11y.defining'#定义中
    if 态=='error':#失败
        return 'a11y.failed'#失败
    if 态=='stopped':#中断
        return 'a11y.stopped'#中断
    return None#ok

def 前导图标(态):#leadingFor
    """error→StateDot.error；stopped→warning；其余 IconCodeOutline16。"""
    if 态=='error':#失败
        return {'type':'StateDot','state':'error'}#红点
    if 态=='stopped':#中断
        return {'type':'StateDot','state':'warning'}#琥珀
    return {'type':'IconCodeOutline16','size':14}#代码图标

def 滤子(子们):#去掉 None
    """保留真值子节点。"""
    return [子 for 子 in 子们 if 子 is not None]#过滤

class 定义行:#cordis_define 结构树
    """组装定义卡嵌套 JSX 树；源码 Tab 本地。"""

    def __init__(自身,属性=None):#记下
        """记下 props。"""
        自身.属性=属性 or {}#合成
        自身.已展开=False#展开
        自身.选中源='client'#源 Tab
        自身.源面板标识='cordis-define-source'#对齐 useId 座

    def 更新(自身,属性):#刷新
        """刷新 props。"""
        自身.属性=属性 or {}#新

    def 切换展开(自身):#翻转
        """可展开才翻。"""
        自身.已展开=not 自身.已展开#翻

    def 选源(自身,源):#切 Tab
        """client | host。"""
        自身.选中源=源#写

    def 渲染(自身):#结构树
        """与上游 JSX 同构的嵌套树。"""
        p=自身.属性#props
        卡=定义卡片(取字段(p,'block'))#卡
        翻译=取字段(p,'t') or (lambda 键,*_a,**_k:键)#文案
        清单钩=取字段(p,'useInventory')#清单
        加载钩=取字段(p,'useLoaded')#已加载
        if callable(清单钩):#有
            清单=清单钩(lambda s:s)#快照
        else:#直读
            清单=取字段(p,'inventory') or {'rows':[],'removed':set()}#缺省
        if callable(加载钩):#有
            已加载=加载钩(lambda s:s) or []#表
        else:#直读
            已加载=取字段(p,'loaded') or []#表
        行=None#清单行
        for 候 in 取字段(清单,'rows') or []:#找
            if 取字段(候,'pluginId')==卡.get('pluginId'):#命中
                行=候#行
                break#停
        已移=取字段(清单,'removed') or set()#已移
        if 卡.get('pluginId') is not None and 卡.get('pluginId') in 已移:#移除
            读数='removed'#已移
        elif 行 is not None and 卡.get('packageId') is not None:#有行
            读数=可见状态(行,卡.get('packageId'),已加载)#三态
        else:#缺省
            读数='idle'#空闲
        名=卡.get('name') or 取字段(p,'callId')#名
        可展=卡.get('hostCode') is not None or 卡.get('clientCode') is not None or 卡.get('output') is not None#可展
        开=自身.已展开 and 可展#开
        有源=卡.get('clientCode') is not None or 卡.get('hostCode') is not None#有源
        活源=自身.选中源#选
        if 活源=='client' and 卡.get('clientCode') is None:#无客户
            活源='host' if 卡.get('hostCode') is not None else 'client'#回退
        if 活源=='host' and 卡.get('hostCode') is None:#无宿主
            活源='client' if 卡.get('clientCode') is not None else 'host'#回退
        活码=卡.get('clientCode') if 活源=='client' else 卡.get('hostCode')#码
        无障碍=状态文案键(卡.get('state'))#a11y
        面板标识=自身.源面板标识#id
        # —— collapsedContent：分隔点 + 名/错 + 用途 + 读数 ——
        折叠子=[#collapsedContent
            {'type':'span','class':'separator','aria-hidden':True},#分隔点
            {'type':'span','class':'errorSummary' if 卡.get('errorSummary') else 'name',
             'children':[卡.get('errorSummary') or 名]},#名或错
        ]#基
        if 卡.get('errorSummary') is None:#无错才示用途
            折叠子.append({'type':'span','class':'purpose','children':[卡.get('purpose') or 翻译('purpose.missing')]})#用途
        if 卡.get('pluginId') is not None:#有插件示读数
            折叠子.append({'type':'span','class':'readout','children':[#读数
                {'type':'span','class':'statusLabel','children':[翻译(读数标签.get(读数,读数))]},#标签
            ]})#结束
        # —— 展开体：源码 Tab + 输出 + 面板提示 + Inspect ——
        体子=[]#bodyWrap 子
        if 有源 and 活码 is not None:#源码区
            页签=[]#tab 们
            for 源 in ('client','host'):#两源
                可用=卡.get('clientCode') is not None if 源=='client' else 卡.get('hostCode') is not None#可用
                活=活源==源#选中
                页签.append({#button role=tab
                    'type':'button','key':源,'id':f'{面板标识}-{源}','role':'tab',
                    'aria-controls':面板标识,'aria-selected':活,
                    'class':'sourceTab sourceTabActive' if 活 else 'sourceTab',
                    'disabled':not 可用,'onClick':('selectSource',源),
                    'children':[翻译('body.clientCode' if 源=='client' else 'body.hostCode')],
                })#页签
            体子.append({'type':'section','class':'sourceCard','children':[#源卡
                {'type':'div','class':'sourceTabs','role':'tablist','aria-label':翻译('body.source'),'children':页签},#页签栏
                {'type':'div','id':面板标识,'class':'sourcePanel','role':'tabpanel',
                 'aria-labelledby':f'{面板标识}-{活源}','children':[#面板
                    {'type':'CodeBlock','code':活码,'lang':'javascript',
                     'copyLabel':翻译('body.copy'),'copiedLabel':翻译('body.copied'),'class':'sourceCode'},#码块
                ]},#面板结束
            ]})#源卡结束
        if 卡.get('output') is not None:#输出段
            体子.append({'type':'section','class':'codeSection','children':[#输出
                {'type':'div','class':'sectionLabel','children':[翻译('body.output')]},#标签
                {'type':'pre','class':'output','data-error':卡.get('state')=='error' or None,
                 'children':[卡.get('output')]},#预格式
            ]})#段结束
        if 卡.get('pluginId') is not None:#面板提示
            体子.append({'type':'div','class':'panelHint','children':[翻译('panel.hint')]})#提示
        if 取字段(p,'inspect') is not None:#巡检钮
            体子.append({'type':'button','class':'inspectButton','onClick':'inspect','children':[#Inspect
                {'type':'IconInspectOutline12'},#图标
                'Inspect',#文案（上游字面）
            ]})#钮结束
        卡子=滤子([#card 子
            {'type':'span','class':'visuallyHidden','children':[翻译(无障碍)]} if 无障碍 else None,#a11y
            {'type':'DisclosureRow',#展开行原语
             'rowClassName':'row','titleClassName':'title','chevronClassName':'chevron',
             'icon':前导图标(卡.get('state')),'title':翻译('row.defineTitle'),
             'open':开,'expandable':可展,'expandOnRowClick':True,'keepContentWhenOpen':True,
             'onToggle':'toggle','collapsedContent':{'type':'fragment','children':折叠子},
             'children':[{'type':'div','class':'bodyWrap','children':体子}] if 开 or 可展 else [],
            },#DisclosureRow
        ])#滤
        return {#根
            'type':'div','class':'card','data-tool':'cordis_define','data-state':卡.get('state'),
            'data-terminal':读数=='removed' or None,
            'data-cordis-plugin-id':卡.get('pluginId'),'data-cordis-package-id':卡.get('packageId'),
            'data-cordis-status':读数,'children':卡子,
            'css':样式表,#样式原文
            'handlers':{'toggle':自身.切换展开,'selectSource':自身.选源,'inspect':取字段(p,'inspect')},#动作
            'note':'DisclosureRow/CodeBlock/图标需浏览器；源码高亮无法 Python·vm 执行',#缺口
        }#结束

    def __call__(自身,属性=None):#调用形
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
