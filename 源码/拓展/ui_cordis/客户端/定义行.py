import os
from .准备行 import 准备行,画出根
from .卡片模型 import 定义卡片
from .状态 import 可见状态

__all__=['定义行','读数标签','样式表','前导图标']#仅中文公开名

读数标签={#CardReading → 文案键
    'idle':'status.idle',
    'client-pending':'status.clientPending',
    'running':'status.running',
    'removed':'status.removed',
}

本目录=os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(本目录,'定义行.module.css'),'r',encoding='utf-8') as 样式文件:
    样式表=样式文件.read()

def 状态文案键(态):
    'running/error/stopped → 文案键'
    if 态=='running':
        return 'a11y.defining'
    if 态=='error':
        return 'a11y.failed'
    if 态=='stopped':
        return 'a11y.stopped'
    return None

def 前导图标(态):
    'error→StateDot.error；stopped→warning；其余 IconCodeOutline16'
    if 态=='error':
        return {'type':'StateDot','state':'error'}
    if 态=='stopped':
        return {'type':'StateDot','state':'warning'}
    return {'type':'IconCodeOutline16','size':14}

def 去掉空子节点(子节点列表):
    '去掉 None 子节点'
    return [子 for 子 in 子节点列表 if 子 is not None]

def 原样键(键):
    '无翻译函数时返回键本身'
    return 键

def 恒等(值):
    '钩子选择器：整份快照'
    return 值

class 定义行:
    '组装定义卡嵌套 JSX 树；源码 Tab 本地。属性为 dict'

    def __init__(自身,属性=None):
        '记下 props'
        自身.属性={} if 属性 is None else 属性
        自身.已展开=False
        自身.选中源='client'
        自身.源面板标识='cordis-define-source'
        if 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新 props'
        自身.属性={} if 属性 is None else 属性

    def 切换展开(自身):
        '可展开才翻'
        自身.已展开=not 自身.已展开

    def 选源(自身,源):
        'client | host'
        自身.选中源=源

    def 渲染(自身):
        '与上游 JSX 同构的嵌套树；参数未齐时只画准备前缀'
        p=自身.属性
        if p.get('phase')=='preparing':
            if 't' in p and p['t'] is not None:
                翻译=p['t']
            else:
                翻译=原样键
            return 准备行({
                'toolName':'cordis_define','t':翻译,
                'icon':{'type':'IconCodeOutline16','size':14},
                'title':翻译('row.defineTitle'),
                'className':'card','rowClassName':'row','titleClassName':'title',
            }).渲染()
        块=p['block'] if 'block' in p else None
        卡=定义卡片(块)
        if 't' in p and p['t'] is not None:
            翻译=p['t']
        else:
            翻译=原样键
        清单钩=p['useInventory'] if 'useInventory' in p else None
        加载钩=p['useLoaded'] if 'useLoaded' in p else None
        if callable(清单钩):
            清单=清单钩(恒等)
        elif 'inventory' in p and p['inventory'] is not None:
            清单=p['inventory']
        else:
            清单={'rows':[],'removed':set()}
        if callable(加载钩):
            已加载=加载钩(恒等)
            if 已加载 is None:
                已加载=[]
        elif 'loaded' in p and p['loaded'] is not None:
            已加载=p['loaded']
        else:
            已加载=[]
        行=None
        卡插件=卡['pluginId'] if 'pluginId' in 卡 else None
        if 'rows' in 清单 and 清单['rows'] is not None:
            for 候 in 清单['rows']:
                if 'pluginId' in 候 and 候['pluginId']==卡插件:
                    行=候
                    break
        if 'removed' in 清单 and 清单['removed'] is not None:
            已移=清单['removed']
        else:
            已移=set()
        卡包=卡['packageId'] if 'packageId' in 卡 else None
        if 卡插件 is not None and 卡插件 in 已移:
            读数='removed'
        elif 行 is not None and 卡包 is not None:
            读数=可见状态(行,卡包,已加载)
        else:
            读数='idle'
        if 'name' in 卡 and 卡['name'] is not None:
            名=卡['name']
        elif 'callId' in p:
            名=p['callId']
        else:
            名=None
        宿主码=卡['hostCode'] if 'hostCode' in 卡 else None
        客户码=卡['clientCode'] if 'clientCode' in 卡 else None
        输出=卡['output'] if 'output' in 卡 else None
        可展=宿主码 is not None or 客户码 is not None or 输出 is not None
        开=自身.已展开 and 可展
        有源=客户码 is not None or 宿主码 is not None
        活源=自身.选中源
        if 活源=='client' and 客户码 is None:
            活源='host' if 宿主码 is not None else 'client'
        if 活源=='host' and 宿主码 is None:
            活源='client' if 客户码 is not None else 'host'
        活码=客户码 if 活源=='client' else 宿主码
        态=卡['state'] if 'state' in 卡 else None
        无障碍=状态文案键(态)
        面板标识=自身.源面板标识
        错摘要=卡['errorSummary'] if 'errorSummary' in 卡 else None
        折叠子=[
            {'type':'span','class':'separator','aria-hidden':True},
            {'type':'span','class':'errorSummary' if 错摘要 is not None else 'name',
             'children':[错摘要 if 错摘要 is not None else 名]},
        ]
        if 错摘要 is None:
            用途=卡['purpose'] if 'purpose' in 卡 and 卡['purpose'] is not None else 翻译('purpose.missing')
            折叠子.append({'type':'span','class':'purpose','children':[用途]})
        if 卡插件 is not None:
            读数键=读数标签[读数] if 读数 in 读数标签 else 读数
            折叠子.append({'type':'span','class':'readout','children':[
                {'type':'span','class':'statusLabel','children':[翻译(读数键)]},
            ]})
        体子=[]
        if 有源 and 活码 is not None:
            页签=[]
            for 源 in ('client','host'):
                可用=客户码 is not None if 源=='client' else 宿主码 is not None
                活=活源==源
                页签.append({
                    'type':'button','key':源,'id':面板标识+'-'+源,'role':'tab',
                    'aria-controls':面板标识,'aria-selected':活,
                    'class':'sourceTab sourceTabActive' if 活 else 'sourceTab',
                    'disabled':not 可用,'onClick':('selectSource',源),
                    'children':[翻译('body.clientCode' if 源=='client' else 'body.hostCode')],
                })
            体子.append({'type':'section','class':'sourceCard','children':[
                {'type':'div','class':'sourceTabs','role':'tablist','aria-label':翻译('body.source'),'children':页签},
                {'type':'div','id':面板标识,'class':'sourcePanel','role':'tabpanel',
                 'aria-labelledby':面板标识+'-'+活源,'children':[
                    {'type':'CodeBlock','code':活码,'lang':'javascript',
                     'copyLabel':翻译('body.copy'),'copiedLabel':翻译('body.copied'),'class':'sourceCode'},
                ]},
            ]})
        if 输出 is not None:
            体子.append({'type':'section','class':'codeSection','children':[
                {'type':'div','class':'sectionLabel','children':[翻译('body.output')]},
                {'type':'pre','class':'output','data-error':True if 态=='error' else None,
                 'children':[输出]},
            ]})
        if 卡插件 is not None:
            体子.append({'type':'div','class':'panelHint','children':[翻译('panel.hint')]})
        巡检=p['inspect'] if 'inspect' in p else None
        if 巡检 is not None:
            体子.append({'type':'button','class':'inspectButton','onClick':'inspect','children':[
                {'type':'IconInspectOutline12'},
                'Inspect',#文案（上游字面）
            ]})
        卡子=去掉空子节点([
            {'type':'span','class':'visuallyHidden','children':[翻译(无障碍)]} if 无障碍 is not None else None,
            {'type':'DisclosureRow',#展开行原语
             'rowClassName':'row','titleClassName':'title','chevronClassName':'chevron',
             'icon':前导图标(态),'title':翻译('row.defineTitle'),
             'open':开,'expandable':可展,'expandOnRowClick':True,'keepContentWhenOpen':True,
             'onToggle':'toggle','collapsedContent':{'type':'fragment','children':折叠子},
             'children':[{'type':'div','class':'bodyWrap','children':体子}] if 开 or 可展 else [],
            },
        ])
        树={
            'type':'div','class':'card','data-tool':'cordis_define','data-state':态,
            'data-terminal':True if 读数=='removed' else None,
            'data-cordis-plugin-id':卡插件,'data-cordis-package-id':卡包,
            'data-cordis-status':读数,'children':卡子,
            'css':样式表,
            'handlers':{'toggle':自身.切换展开,'selectSource':自身.选源,'inspect':巡检},
            'note':'DisclosureRow/CodeBlock/图标需浏览器；源码高亮无法 Python·vm 执行',
        }
        return 画出根(树)

    def __call__(自身,属性=None):
        '结构树面'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
