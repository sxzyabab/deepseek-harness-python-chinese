import os
from ..异常 import 页面失败文案
from .准备行 import 准备行,画出根
from .卡片模型 import 运行卡片
from .运行卡片索引 import 工具视图键
from .状态 import 可见状态

__all__=['运行行','读数标签','样式表','前导图标']#仅中文公开名

读数标签={
    'idle':'status.idle',
    'awaiting-approval':'status.awaitingApproval',
    'failed':'status.failed',
    'client-pending':'status.clientPending',
    'running':'status.running',
    'removed':'status.removed',
    'superseded':'status.superseded',
}

本目录=os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(本目录,'运行行.module.css'),'r',encoding='utf-8') as 样式文件:
    样式表=样式文件.read()

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

class 运行行:
    '组装运行卡读数与业务视图座的嵌套 JSX 树。属性为 dict'

    def __init__(自身,属性=None):
        '记下 props'
        自身.属性={} if 属性 is None else 属性
        if 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新 props'
        自身.属性={} if 属性 is None else 属性

    def 渲染(自身):
        '与上游 JSX 同构；参数未齐时只画准备前缀'
        p=自身.属性
        if p.get('phase')=='preparing':
            if 't' in p and p['t'] is not None:
                翻译=p['t']
            else:
                翻译=原样键
            return 准备行({
                'toolName':'cordis_run','t':翻译,
                'icon':{'type':'IconCodeOutline16','size':14},
                'title':翻译('row.runTitle'),
                'className':'card','rowClassName':'row','titleClassName':'title',
            }).渲染()
        块=p['block'] if 'block' in p else None
        卡=运行卡片(块)
        if 't' in p and p['t'] is not None:
            翻译=p['t']
        else:
            翻译=原样键
        调用标识=p['callId'] if 'callId' in p else None
        清单钩=p['useInventory'] if 'useInventory' in p else None
        加载钩=p['useLoaded'] if 'useLoaded' in p else None
        卡仓钩=p['useRunCards'] if 'useRunCards' in p else None
        活动钩=p['useActiveRuns'] if 'useActiveRuns' in p else None
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
        if callable(卡仓钩):
            最新=卡仓钩(恒等)
            if 最新 is None:
                最新={}
        elif 'runCards' in p and p['runCards'] is not None:
            最新=p['runCards']
        else:
            最新={}
        if callable(活动钩):
            活动图=活动钩(恒等)
            if 活动图 is None:
                活动图={}
        elif 'activeRuns' in p and p['activeRuns'] is not None:
            活动图=p['activeRuns']
        else:
            活动图={}
        卡插件=卡['pluginId'] if 'pluginId' in 卡 else None
        卡包=卡['packageId'] if 'packageId' in 卡 else None
        卡运行=卡['pluginRunId'] if 'pluginRunId' in 卡 else None
        卡序号=卡['seq'] if 'seq' in 卡 else None
        卡态=卡['state'] if 'state' in 卡 else None
        键=None
        if 卡态=='ok' and 卡插件 is not None and 卡包 is not None and 卡运行 is not None and 卡序号 is not None:
            键=工具视图键(卡插件,卡包)
            观察=p['onObserveRunCard'] if 'onObserveRunCard' in p else None
            if callable(观察):
                观察({'key':键,'callId':调用标识,'seq':卡序号,'pluginRunId':卡运行})
        行=None
        if 'rows' in 清单 and 清单['rows'] is not None:
            for 候 in 清单['rows']:
                if 'pluginId' in 候 and 候['pluginId']==卡插件:
                    行=候
                    break
        指针=None
        if 键 is not None and 键 in 最新:
            指针=最新[键]
        指针调用=指针['callId'] if 指针 is not None and 'callId' in 指针 else None
        指针序号=指针['seq'] if 指针 is not None and 'seq' in 指针 else -1#指针序号；缺席当 -1
        被替=指针 is not None and 指针调用!=调用标识 and 指针序号>=(卡序号 if 卡序号 is not None else -1)
        活动=活动图[卡插件] if 卡插件 is not None and 卡插件 in 活动图 else None
        最近=行['latestRun'] if 行 is not None and 'latestRun' in 行 else None
        尝试=None
        if 卡运行 is not None and 最近 is not None and 'pluginRunId' in 最近 and 最近['pluginRunId']==卡运行:
            尝试=最近
        活动阶段=活动['phase'] if 活动 is not None and 'phase' in 活动 else None
        活动包=活动['packageId'] if 活动 is not None and 'packageId' in 活动 else None
        活动模式=活动['mode'] if 活动 is not None and 'mode' in 活动 else None
        卡模式=卡['mode'] if 'mode' in 卡 else None
        尝试状态=尝试['status'] if 尝试 is not None and 'status' in 尝试 else None
        等批=(尝试状态=='awaiting-approval'
            or (卡包 is not None and 活动阶段=='awaiting-approval'
                and 活动包==卡包
                and (卡模式 is None or 活动模式==卡模式)))
        if 'removed' in 清单 and 清单['removed'] is not None:
            已移=清单['removed']
        else:
            已移=set()
        if 卡插件 is not None and 卡插件 in 已移:
            读数='removed'
        elif 被替:
            读数='superseded'
        elif 等批:
            读数='awaiting-approval'
        elif 尝试状态=='failed':
            读数='failed'
        elif 行 is not None and 卡包 is not None:
            读数=可见状态(行,卡包,已加载)
        else:
            读数='idle'
        错摘要=卡['errorSummary'] if 'errorSummary' in 卡 else None
        摘要=错摘要
        if 摘要 is None:
            if 卡插件 is None:
                摘要=调用标识
            elif 卡包 is not None:
                摘要=卡插件+' · '+卡包
            else:
                摘要=卡插件
        示业务=读数=='running' and 键 is not None
        标题键='row.updateTitle' if 卡模式=='update' else 'row.runTitle'
        读数键=读数标签[读数] if 读数 in 读数标签 else 读数
        巡检=p['inspect'] if 'inspect' in p else None
        行子=去掉空子节点([
            {'type':'span','class':'icon','children':[前导图标(卡态)]},
            {'type':'span','class':'title','children':[翻译(标题键)]},
            {'type':'span','class':'separator','aria-hidden':True},
            {'type':'span','class':'error' if 错摘要 is not None else 'summary','children':[摘要]},
            {'type':'span','class':'status','children':[翻译(读数键)]},
            {'type':'button','class':'inspect','aria-label':'Inspect','onClick':'inspect',
             'children':[{'type':'IconInspectOutline12'}]} if 巡检 is not None else None,
        ])
        卡子=[
            {'type':'div','class':'row','children':行子},
        ]
        if 读数=='removed':
            卡子.append({'type':'div','class':'message','children':[翻译('run.removed')]})
        if 读数=='superseded':
            卡子.append({'type':'div','class':'message','children':[翻译('run.superseded')]})
        尝试错=尝试['error'] if 尝试 is not None and 'error' in 尝试 else None
        错消息=尝试错['message'] if isinstance(尝试错,dict) and 'message' in 尝试错 else None
        if 读数=='failed' and 错消息 is not None:
            卡子.append({'type':'div','class':'message','children':[页面失败文案(错消息)]})
        输出=卡['output'] if 'output' in 卡 else None
        if 示业务 and 卡插件 is not None and 卡包 is not None and 卡运行 is not None:
            回退=None
            if 输出 is not None:
                回退={'type':'pre','class':'output','children':[输出]}
            卡子.append({'type':'div','class':'business','data-cordis-business-view':键,'children':[
                {'type':'renderSlot','name':'tool.view.cordis',
                 'props':{'pluginId':卡插件,'packageId':卡包,
                          'pluginRunId':卡运行},
                 'entryKey':键,'fallback':回退},
            ]})
        if (not 示业务 and 读数 not in ('removed','superseded') and 输出 is not None):
            卡子.append({'type':'pre','class':'output','children':[输出]})
        渲染槽=p['renderSlot'] if 'renderSlot' in p else None
        树={
            'type':'div','class':'card','data-tool':'cordis_run','data-state':卡态,
            'data-cordis-plugin-id':卡插件,'data-cordis-package-id':卡包,
            'data-cordis-run-id':卡运行,'data-cordis-status':读数,
            'children':卡子,'css':样式表,
            'handlers':{'inspect':巡检,'renderSlot':渲染槽},
            'note':'业务视图槽与图标需浏览器；Package React 半无法 Python·vm 执行',
        }
        return 画出根(树)

    def __call__(自身,属性=None):
        '结构树面'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
