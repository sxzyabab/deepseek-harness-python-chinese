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

本目录=os.path.dirname(os.path.abspath(__file__))#本目录
with open(os.path.join(本目录,'定义行.module.css'),'r',encoding='utf-8') as 样式文件:#原文
    样式表=样式文件.read()#全文

def 状态文案键(态):
    """running/error/stopped → 文案键。"""
    if 态=='running':#定义中
        return 'a11y.defining'#定义中
    if 态=='error':#失败
        return 'a11y.failed'#失败
    if 态=='stopped':#中断
        return 'a11y.stopped'#中断
    return None#ok

def 前导图标(态):
    """error→StateDot.error；stopped→warning；其余 IconCodeOutline16。"""
    if 态=='error':#失败
        return {'type':'StateDot','state':'error'}#红点
    if 态=='stopped':#中断
        return {'type':'StateDot','state':'warning'}#琥珀
    return {'type':'IconCodeOutline16','size':14}#代码图标

def 去掉空子节点(子节点列表):
    """去掉 None 子节点。"""
    return [子 for 子 in 子节点列表 if 子 is not None]#过滤

def 原样键(键):
    """无翻译函数时返回键本身。"""
    return 键#原样

def 恒等(值):
    """钩子选择器：整份快照。"""
    return 值#原样

class 定义行:
    """组装定义卡嵌套 JSX 树；源码 Tab 本地。属性为 dict。"""

    def __init__(自身,属性=None):
        """记下 props。"""
        自身.属性={} if 属性 is None else 属性#合成
        自身.已展开=False#展开
        自身.选中源='client'#源 Tab
        自身.源面板标识='cordis-define-source'#对齐 useId 座

    def 更新(自身,属性):
        """刷新 props。"""
        自身.属性={} if 属性 is None else 属性#新

    def 切换展开(自身):
        """可展开才翻。"""
        自身.已展开=not 自身.已展开#翻

    def 选源(自身,源):
        """client | host。"""
        自身.选中源=源#写

    def 渲染(自身):
        """与上游 JSX 同构的嵌套树。"""
        p=自身.属性#props dict
        块=p['block'] if 'block' in p else None#调用块
        卡=定义卡片(块)#卡
        if 't' in p and p['t'] is not None:#有翻译
            翻译=p['t']#文案
        else:#缺席
            翻译=原样键#原样键
        清单钩=p['useInventory'] if 'useInventory' in p else None#清单
        加载钩=p['useLoaded'] if 'useLoaded' in p else None#已加载
        if callable(清单钩):#有钩
            清单=清单钩(恒等)#快照
        elif 'inventory' in p and p['inventory'] is not None:#直读
            清单=p['inventory']#清单
        else:#缺省
            清单={'rows':[],'removed':set()}#缺省
        if callable(加载钩):#有钩
            已加载=加载钩(恒等)#表
            if 已加载 is None:#钩子给了空
                已加载=[]#空表
        elif 'loaded' in p and p['loaded'] is not None:#直读
            已加载=p['loaded']#表
        else:#缺省
            已加载=[]#空表
        行=None#清单行
        卡插件=卡['pluginId'] if 'pluginId' in 卡 else None#卡上的插件
        if 'rows' in 清单 and 清单['rows'] is not None:#有行表
            for 候 in 清单['rows']:#找
                if 'pluginId' in 候 and 候['pluginId']==卡插件:#命中
                    行=候#行
                    break#停
        if 'removed' in 清单 and 清单['removed'] is not None:#有已移集合
            已移=清单['removed']#已移
        else:#缺席
            已移=set()#空
        卡包=卡['packageId'] if 'packageId' in 卡 else None#卡上的包
        if 卡插件 is not None and 卡插件 in 已移:#移除
            读数='removed'#已移
        elif 行 is not None and 卡包 is not None:#有行
            读数=可见状态(行,卡包,已加载)#三态
        else:#缺省
            读数='idle'#空闲
        if 'name' in 卡 and 卡['name'] is not None:#有名
            名=卡['name']#名
        elif 'callId' in p:#回落调用 id
            名=p['callId']#名
        else:#都没有
            名=None#空
        宿主码=卡['hostCode'] if 'hostCode' in 卡 else None#宿主码
        客户码=卡['clientCode'] if 'clientCode' in 卡 else None#客户码
        输出=卡['output'] if 'output' in 卡 else None#输出
        可展=宿主码 is not None or 客户码 is not None or 输出 is not None#可展
        开=自身.已展开 and 可展#开
        有源=客户码 is not None or 宿主码 is not None#有源
        活源=自身.选中源#选
        if 活源=='client' and 客户码 is None:#无客户
            活源='host' if 宿主码 is not None else 'client'#回退
        if 活源=='host' and 宿主码 is None:#无宿主
            活源='client' if 客户码 is not None else 'host'#回退
        活码=客户码 if 活源=='client' else 宿主码#码
        态=卡['state'] if 'state' in 卡 else None#状态
        无障碍=状态文案键(态)#a11y
        面板标识=自身.源面板标识#id
        错摘要=卡['errorSummary'] if 'errorSummary' in 卡 else None#错摘要
        折叠子=[#collapsedContent
            {'type':'span','class':'separator','aria-hidden':True},#分隔点
            {'type':'span','class':'errorSummary' if 错摘要 is not None else 'name',
             'children':[错摘要 if 错摘要 is not None else 名]},#名或错
        ]#基
        if 错摘要 is None:#无错才示用途
            用途=卡['purpose'] if 'purpose' in 卡 and 卡['purpose'] is not None else 翻译('purpose.missing')#用途
            折叠子.append({'type':'span','class':'purpose','children':[用途]})#用途
        if 卡插件 is not None:#有插件示读数
            读数键=读数标签[读数] if 读数 in 读数标签 else 读数#标签
            折叠子.append({'type':'span','class':'readout','children':[#读数
                {'type':'span','class':'statusLabel','children':[翻译(读数键)]},#标签
            ]})#结束
        体子=[]#bodyWrap 子
        if 有源 and 活码 is not None:#源码区
            页签=[]#页签列表
            for 源 in ('client','host'):#两源
                可用=客户码 is not None if 源=='client' else 宿主码 is not None#可用
                活=活源==源#选中
                页签.append({#button role=tab
                    'type':'button','key':源,'id':面板标识+'-'+源,'role':'tab',
                    'aria-controls':面板标识,'aria-selected':活,
                    'class':'sourceTab sourceTabActive' if 活 else 'sourceTab',
                    'disabled':not 可用,'onClick':('selectSource',源),
                    'children':[翻译('body.clientCode' if 源=='client' else 'body.hostCode')],
                })#页签
            体子.append({'type':'section','class':'sourceCard','children':[#源卡
                {'type':'div','class':'sourceTabs','role':'tablist','aria-label':翻译('body.source'),'children':页签},#页签栏
                {'type':'div','id':面板标识,'class':'sourcePanel','role':'tabpanel',
                 'aria-labelledby':面板标识+'-'+活源,'children':[#面板
                    {'type':'CodeBlock','code':活码,'lang':'javascript',
                     'copyLabel':翻译('body.copy'),'copiedLabel':翻译('body.copied'),'class':'sourceCode'},#码块
                ]},#面板结束
            ]})#源卡结束
        if 输出 is not None:#输出段
            体子.append({'type':'section','class':'codeSection','children':[#输出
                {'type':'div','class':'sectionLabel','children':[翻译('body.output')]},#标签
                {'type':'pre','class':'output','data-error':True if 态=='error' else None,
                 'children':[输出]},#预格式
            ]})#段结束
        if 卡插件 is not None:#面板提示
            体子.append({'type':'div','class':'panelHint','children':[翻译('panel.hint')]})#提示
        巡检=p['inspect'] if 'inspect' in p else None#巡检
        if 巡检 is not None:#巡检钮
            体子.append({'type':'button','class':'inspectButton','onClick':'inspect','children':[#Inspect
                {'type':'IconInspectOutline12'},#图标
                'Inspect',#文案（上游字面）
            ]})#钮结束
        卡子=去掉空子节点([#card 子
            {'type':'span','class':'visuallyHidden','children':[翻译(无障碍)]} if 无障碍 is not None else None,#a11y
            {'type':'DisclosureRow',#展开行原语
             'rowClassName':'row','titleClassName':'title','chevronClassName':'chevron',
             'icon':前导图标(态),'title':翻译('row.defineTitle'),
             'open':开,'expandable':可展,'expandOnRowClick':True,'keepContentWhenOpen':True,
             'onToggle':'toggle','collapsedContent':{'type':'fragment','children':折叠子},
             'children':[{'type':'div','class':'bodyWrap','children':体子}] if 开 or 可展 else [],
            },#DisclosureRow
        ])#滤
        return {#根
            'type':'div','class':'card','data-tool':'cordis_define','data-state':态,
            'data-terminal':True if 读数=='removed' else None,
            'data-cordis-plugin-id':卡插件,'data-cordis-package-id':卡包,
            'data-cordis-status':读数,'children':卡子,
            'css':样式表,#样式原文
            'handlers':{'toggle':自身.切换展开,'selectSource':自身.选源,'inspect':巡检},#动作
            'note':'DisclosureRow/CodeBlock/图标需浏览器；源码高亮无法 Python·vm 执行',#缺口
        }#结束

    def __call__(自身,属性=None):
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
