import os#读样式
from .卡片模型 import 运行卡片#卡模型
from .运行卡片索引 import 工具视图键#视图键
from .状态 import 可见状态#可见态

__all__=['运行行','读数标签','样式表','前导图标']#仅中文公开名

读数标签={#RunReading → 文案键
    'idle':'status.idle',
    'awaiting-approval':'status.awaitingApproval',
    'failed':'status.failed',
    'client-pending':'status.clientPending',
    'running':'status.running',
    'removed':'status.removed',
    'superseded':'status.superseded',
}#结束

本目录=os.path.dirname(os.path.abspath(__file__))#本目录
with open(os.path.join(本目录,'运行行.module.css'),'r',encoding='utf-8') as 样式文件:#原文
    样式表=样式文件.read()#全文

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

class 运行行:
    """组装运行卡读数与业务视图座的嵌套 JSX 树。属性为 dict。"""

    def __init__(自身,属性=None):
        """记下 props。"""
        自身.属性={} if 属性 is None else 属性#合成

    def 更新(自身,属性):
        """刷新 props。"""
        自身.属性={} if 属性 is None else 属性#新

    def 渲染(自身):
        """与上游 JSX 同构。"""
        p=自身.属性#props dict
        块=p['block'] if 'block' in p else None#调用块
        卡=运行卡片(块)#卡
        if 't' in p and p['t'] is not None:#有翻译
            翻译=p['t']#文案
        else:#缺席
            翻译=原样键#原样键
        调用标识=p['callId'] if 'callId' in p else None#callId
        清单钩=p['useInventory'] if 'useInventory' in p else None#清单
        加载钩=p['useLoaded'] if 'useLoaded' in p else None#已加载
        卡仓钩=p['useRunCards'] if 'useRunCards' in p else None#卡仓
        活动钩=p['useActiveRuns'] if 'useActiveRuns' in p else None#活动
        if callable(清单钩):#有钩
            清单=清单钩(恒等)#快照
        elif 'inventory' in p and p['inventory'] is not None:#直读
            清单=p['inventory']#清单
        else:#缺省
            清单={'rows':[],'removed':set()}#缺省
        if callable(加载钩):#有钩
            已加载=加载钩(恒等)#表
            if 已加载 is None:#空
                已加载=[]#空表
        elif 'loaded' in p and p['loaded'] is not None:#直读
            已加载=p['loaded']#表
        else:#缺省
            已加载=[]#空表
        if callable(卡仓钩):#有钩
            最新=卡仓钩(恒等)#图
            if 最新 is None:#空
                最新={}#空图
        elif 'runCards' in p and p['runCards'] is not None:#直读
            最新=p['runCards']#图
        else:#缺省
            最新={}#空图
        if callable(活动钩):#有钩
            活动图=活动钩(恒等)#图
            if 活动图 is None:#空
                活动图={}#空图
        elif 'activeRuns' in p and p['activeRuns'] is not None:#直读
            活动图=p['activeRuns']#图
        else:#缺省
            活动图={}#空图
        卡插件=卡['pluginId'] if 'pluginId' in 卡 else None#插件
        卡包=卡['packageId'] if 'packageId' in 卡 else None#包
        卡运行=卡['pluginRunId'] if 'pluginRunId' in 卡 else None#运行
        卡序号=卡['seq'] if 'seq' in 卡 else None#序号
        卡态=卡['state'] if 'state' in 卡 else None#状态
        键=None#业务键
        if 卡态=='ok' and 卡插件 is not None and 卡包 is not None and 卡运行 is not None and 卡序号 is not None:#成功激活
            键=工具视图键(卡插件,卡包)#键
            观察=p['onObserveRunCard'] if 'onObserveRunCard' in p else None#观察
            if callable(观察):#有
                观察({'key':键,'callId':调用标识,'seq':卡序号,'pluginRunId':卡运行})#登记
        行=None#清单行
        if 'rows' in 清单 and 清单['rows'] is not None:#有行表
            for 候 in 清单['rows']:#找
                if 'pluginId' in 候 and 候['pluginId']==卡插件:#命中
                    行=候#行
                    break#停
        指针=None#指针
        if 键 is not None and 键 in 最新:#有指针
            指针=最新[键]#指针
        指针调用=指针['callId'] if 指针 is not None and 'callId' in 指针 else None#指针调用
        指针序号=指针['seq'] if 指针 is not None and 'seq' in 指针 else -1#指针序号；缺席当 -1
        被替=指针 is not None and 指针调用!=调用标识 and 指针序号>=(卡序号 if 卡序号 is not None else -1)#被替
        活动=活动图[卡插件] if 卡插件 is not None and 卡插件 in 活动图 else None#活动
        最近=行['latestRun'] if 行 is not None and 'latestRun' in 行 else None#最近
        尝试=None#尝试
        if 卡运行 is not None and 最近 is not None and 'pluginRunId' in 最近 and 最近['pluginRunId']==卡运行:#同一次运行
            尝试=最近#尝试
        活动阶段=活动['phase'] if 活动 is not None and 'phase' in 活动 else None#阶段
        活动包=活动['packageId'] if 活动 is not None and 'packageId' in 活动 else None#活动包
        活动模式=活动['mode'] if 活动 is not None and 'mode' in 活动 else None#活动模式
        卡模式=卡['mode'] if 'mode' in 卡 else None#卡模式
        尝试状态=尝试['status'] if 尝试 is not None and 'status' in 尝试 else None#尝试状态
        等批=(尝试状态=='awaiting-approval'
            or (卡包 is not None and 活动阶段=='awaiting-approval'
                and 活动包==卡包
                and (卡模式 is None or 活动模式==卡模式)))#审批
        if 'removed' in 清单 and 清单['removed'] is not None:#有已移
            已移=清单['removed']#已移
        else:#缺席
            已移=set()#空
        if 卡插件 is not None and 卡插件 in 已移:#移除
            读数='removed'#已移
        elif 被替:#被替
            读数='superseded'#被替
        elif 等批:#审批
            读数='awaiting-approval'#审批
        elif 尝试状态=='failed':#失败
            读数='failed'#失败
        elif 行 is not None and 卡包 is not None:#有行
            读数=可见状态(行,卡包,已加载)#三态
        else:#缺省
            读数='idle'#空闲
        错摘要=卡['errorSummary'] if 'errorSummary' in 卡 else None#错摘要
        摘要=错摘要#摘要
        if 摘要 is None:#无错
            if 卡插件 is None:#无插件
                摘要=调用标识#callId
            elif 卡包 is not None:#有包
                摘要=卡插件+' · '+卡包#拼
            else:#只有插件
                摘要=卡插件#插件
        示业务=读数=='running' and 键 is not None#业务座
        标题键='row.updateTitle' if 卡模式=='update' else 'row.runTitle'#标题
        读数键=读数标签[读数] if 读数 in 读数标签 else 读数#状态文案
        巡检=p['inspect'] if 'inspect' in p else None#巡检
        行子=去掉空子节点([#css.row 子
            {'type':'span','class':'icon','children':[前导图标(卡态)]},#图标
            {'type':'span','class':'title','children':[翻译(标题键)]},#标题
            {'type':'span','class':'separator','aria-hidden':True},#分隔
            {'type':'span','class':'error' if 错摘要 is not None else 'summary','children':[摘要]},#摘要
            {'type':'span','class':'status','children':[翻译(读数键)]},#状态
            {'type':'button','class':'inspect','aria-label':'Inspect','onClick':'inspect',
             'children':[{'type':'IconInspectOutline12'}]} if 巡检 is not None else None,#巡检
        ])#行子结束
        卡子=[#card 子
            {'type':'div','class':'row','children':行子},#顶行
        ]#基
        if 读数=='removed':#已移消息
            卡子.append({'type':'div','class':'message','children':[翻译('run.removed')]})#消息
        if 读数=='superseded':#被替消息
            卡子.append({'type':'div','class':'message','children':[翻译('run.superseded')]})#消息
        尝试错=尝试['error'] if 尝试 is not None and 'error' in 尝试 else None#失败对象
        错消息=尝试错['message'] if isinstance(尝试错,dict) and 'message' in 尝试错 else None#失败消息
        if 读数=='failed' and 错消息 is not None:#失败消息
            卡子.append({'type':'div','class':'message','children':[错消息]})#消息
        输出=卡['output'] if 'output' in 卡 else None#输出
        if 示业务 and 卡插件 is not None and 卡包 is not None and 卡运行 is not None:#业务座
            回退=None#fallback
            if 输出 is not None:#有输出作回退
                回退={'type':'pre','class':'output','children':[输出]}#pre
            卡子.append({'type':'div','class':'business','data-cordis-business-view':键,'children':[#业务
                {'type':'renderSlot','name':'tool.view.cordis',#槽
                 'props':{'pluginId':卡插件,'packageId':卡包,
                          'pluginRunId':卡运行},#槽参
                 'entryKey':键,'fallback':回退},#选项
            ]})#业务结束
        if (not 示业务 and 读数 not in ('removed','superseded') and 输出 is not None):#非业务输出
            卡子.append({'type':'pre','class':'output','children':[输出]})#输出
        渲染槽=p['renderSlot'] if 'renderSlot' in p else None#渲染槽
        return {#根
            'type':'div','class':'card','data-tool':'cordis_run','data-state':卡态,
            'data-cordis-plugin-id':卡插件,'data-cordis-package-id':卡包,
            'data-cordis-run-id':卡运行,'data-cordis-status':读数,
            'children':卡子,'css':样式表,
            'handlers':{'inspect':巡检,'renderSlot':渲染槽},#动作
            'note':'业务视图槽与图标需浏览器；Package React 半无法 Python·vm 执行',#缺口
        }#结束

    def __call__(自身,属性=None):
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
