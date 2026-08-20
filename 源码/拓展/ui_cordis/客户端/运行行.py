"""cordis_run 卡与包业务视图座：嵌套 JSX 结构树 + 样式串。

对齐上游 `ui-cordis/src/client/CordisRunRow.tsx`。公开面仅中文名。
业务视图槽 renderSlot 与图标半需浏览器；读数逻辑与 DOM 嵌套来自上游。
无法 JS·vm 执行：Package 拥有的 React 业务视图。
"""
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

_本目录=os.path.dirname(os.path.abspath(__file__))#本目录
with open(os.path.join(_本目录,'运行行.module.css'),'r',encoding='utf-8') as _样式文件:#原文
    样式表=_样式文件.read()#全文

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 前导图标(态):#icon 槽
    """error→StateDot.error；stopped→warning；其余 IconCodeOutline16。"""
    if 态=='error':#失败
        return {'type':'StateDot','state':'error'}#红点
    if 态=='stopped':#中断
        return {'type':'StateDot','state':'warning'}#琥珀
    return {'type':'IconCodeOutline16','size':14}#代码图标

def 滤子(子们):#去掉 None
    """保留真值子节点。"""
    return [子 for 子 in 子们 if 子 is not None]#过滤

class 运行行:#cordis_run 结构树
    """组装运行卡读数与业务视图座的嵌套 JSX 树。"""

    def __init__(自身,属性=None):#记下
        """记下 props。"""
        自身.属性=属性 or {}#合成

    def 更新(自身,属性):#刷新
        """刷新 props。"""
        自身.属性=属性 or {}#新

    def 渲染(自身):#结构树
        """与上游 JSX 同构。"""
        p=自身.属性#props
        卡=运行卡片(取字段(p,'block'))#卡
        翻译=取字段(p,'t') or (lambda 键,*_a,**_k:键)#文案
        调用标识=取字段(p,'callId')#callId
        清单钩=取字段(p,'useInventory')#清单
        加载钩=取字段(p,'useLoaded')#已加载
        卡仓钩=取字段(p,'useRunCards')#卡仓
        活动钩=取字段(p,'useActiveRuns')#活动
        if callable(清单钩):#有
            清单=清单钩(lambda s:s)#快照
        else:#直读
            清单=取字段(p,'inventory') or {'rows':[],'removed':set()}#缺省
        if callable(加载钩):#有
            已加载=加载钩(lambda s:s) or []#表
        else:#直读
            已加载=取字段(p,'loaded') or []#表
        if callable(卡仓钩):#有
            最新=卡仓钩(lambda s:s) or {}#图
        else:#直读
            最新=取字段(p,'runCards') or {}#图
        if callable(活动钩):#有
            活动图=活动钩(lambda s:s) or {}#图
        else:#直读
            活动图=取字段(p,'activeRuns') or {}#图
        键=None#业务键
        if (卡.get('state')=='ok' and 卡.get('pluginId') and 卡.get('packageId')
            and 卡.get('pluginRunId') and 卡.get('seq') is not None):#成功激活
            键=工具视图键(卡.get('pluginId'),卡.get('packageId'))#键
            观察=取字段(p,'onObserveRunCard')#观察
            if callable(观察):#有
                观察({'key':键,'callId':调用标识,'seq':卡.get('seq'),'pluginRunId':卡.get('pluginRunId')})#登记
        行=None#清单行
        for 候 in 取字段(清单,'rows') or []:#找
            if 取字段(候,'pluginId')==卡.get('pluginId'):#命中
                行=候#行
                break#停
        指针=最新.get(键) if 键 and isinstance(最新,dict) else None#指针
        被替=指针 is not None and 取字段(指针,'callId')!=调用标识 and 取字段(指针,'seq',-1)>=(卡.get('seq') or -1)#被替
        活动=活动图.get(卡.get('pluginId')) if isinstance(活动图,dict) and 卡.get('pluginId') else None#活动
        最近=取字段(行,'latestRun') if 行 else None#最近
        尝试=最近 if 卡.get('pluginRunId') and 取字段(最近,'pluginRunId')==卡.get('pluginRunId') else None#尝试
        等批=(取字段(尝试,'status')=='awaiting-approval'
            or (卡.get('packageId') and 取字段(活动,'phase')=='awaiting-approval'
                and 取字段(活动,'packageId')==卡.get('packageId')
                and (卡.get('mode') is None or 取字段(活动,'mode')==卡.get('mode'))))#审批
        已移=取字段(清单,'removed') or set()#已移
        if 卡.get('pluginId') and 卡.get('pluginId') in 已移:#移除
            读数='removed'#已移
        elif 被替:#被替
            读数='superseded'#被替
        elif 等批:#审批
            读数='awaiting-approval'#审批
        elif 取字段(尝试,'status')=='failed':#失败
            读数='failed'#失败
        elif 行 is not None and 卡.get('packageId'):#有行
            读数=可见状态(行,卡.get('packageId'),已加载)#三态
        else:#缺省
            读数='idle'#空闲
        摘要=卡.get('errorSummary')
        if 摘要 is None:#无错
            if 卡.get('pluginId') is None:#无插件
                摘要=调用标识#callId
            else:#有
                摘要=卡.get('pluginId')+(f" · {卡.get('packageId')}" if 卡.get('packageId') else '')#拼
        示业务=读数=='running' and 键 is not None#业务座
        标题键='row.updateTitle' if 卡.get('mode')=='update' else 'row.runTitle'#标题
        行子=滤子([#css.row 子
            {'type':'span','class':'icon','children':[前导图标(卡.get('state'))]},#图标
            {'type':'span','class':'title','children':[翻译(标题键)]},#标题
            {'type':'span','class':'separator','aria-hidden':True},#分隔
            {'type':'span','class':'error' if 卡.get('errorSummary') else 'summary','children':[摘要]},#摘要
            {'type':'span','class':'status','children':[翻译(读数标签.get(读数,读数))]},#状态
            {'type':'button','class':'inspect','aria-label':'Inspect','onClick':'inspect',
             'children':[{'type':'IconInspectOutline12'}]} if 取字段(p,'inspect') is not None else None,#巡检
        ])#行子结束
        卡子=[#card 子
            {'type':'div','class':'row','children':行子},#顶行
        ]#基
        if 读数=='removed':#已移消息
            卡子.append({'type':'div','class':'message','children':[翻译('run.removed')]})#消息
        if 读数=='superseded':#被替消息
            卡子.append({'type':'div','class':'message','children':[翻译('run.superseded')]})#消息
        if 读数=='failed' and 取字段(取字段(尝试,'error'),'message') is not None:#失败消息
            卡子.append({'type':'div','class':'message','children':[取字段(取字段(尝试,'error'),'message')]})#消息
        if 示业务 and 卡.get('pluginId') and 卡.get('packageId') and 卡.get('pluginRunId'):#业务座
            回退=None#fallback
            if 卡.get('output') is not None:#有输出作回退
                回退={'type':'pre','class':'output','children':[卡.get('output')]}#pre
            卡子.append({'type':'div','class':'business','data-cordis-business-view':键,'children':[#业务
                {'type':'renderSlot','name':'tool.view.cordis',#槽
                 'props':{'pluginId':卡.get('pluginId'),'packageId':卡.get('packageId'),
                          'pluginRunId':卡.get('pluginRunId')},#槽参
                 'entryKey':键,'fallback':回退},#选项
            ]})#业务结束
        if (not 示业务 and 读数 not in ('removed','superseded') and 卡.get('output') is not None):#非业务输出
            卡子.append({'type':'pre','class':'output','children':[卡.get('output')]})#输出
        return {#根
            'type':'div','class':'card','data-tool':'cordis_run','data-state':卡.get('state'),
            'data-cordis-plugin-id':卡.get('pluginId'),'data-cordis-package-id':卡.get('packageId'),
            'data-cordis-run-id':卡.get('pluginRunId'),'data-cordis-status':读数,
            'children':卡子,'css':样式表,
            'handlers':{'inspect':取字段(p,'inspect'),'renderSlot':取字段(p,'renderSlot')},#动作
            'note':'业务视图槽与图标需浏览器；Package React 半无法 Python·vm 执行',#缺口
        }#结束

    def __call__(自身,属性=None):#调用形
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
