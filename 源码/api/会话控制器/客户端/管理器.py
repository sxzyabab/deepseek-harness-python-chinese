"""会话管理器：实例簇、帧分发与列表状态。

公开面仅中文名。无选择轴、无队列缓存、无完成提醒。
"""
import threading#防抖
import time#活动时间
from .有序基线 import 合并有序基线#有序合并
from .谱系 import 展平谱系#谱系
from .通知器 import 通知器#通知
from .投影存储 import 投影值存储#投影
from .会话 import 会话#会话类

__all__=['会话管理器']#仅中文公开名

def _规范游标(值):
    """规范投影游标。"""
    return -1 if 值==-1 else 值#游标

def _目录可用性(父可用):
    """可选父可用性字段。"""
    return {} if 父可用 is None else {'parentAvailable':父可用}#字段

def _工作区附着会话标识(错误):
    """从附着失败细节取已发布会话 id。"""
    细节=错误.details if hasattr(错误,'details') else (错误['details'] if isinstance(错误,dict) and 'details' in 错误 else None)#细节
    if not isinstance(细节,dict):#无
        return None#无
    return 细节['sessionId'] if 'sessionId' in 细节 else None#id

def _应用变更(摘要列表,变更):
    """应用一条列表变更。"""
    种类=变更['kind']#种类
    if 种类=='upsert':#插入或更新
        摘要=变更['summary']#摘要
        标识=摘要['sessionId']#id
        for 下标,项 in enumerate(摘要列表):#找已有
            if 项['sessionId']!=标识:#其它
                continue#下一项
            合并=dict(项)#拷
            合并['blank']=项.get('blank',True) and 摘要.get('blank',True)#blank 仅降
            if 项.get('cwd') is None and 摘要.get('cwd') is not None:#填 cwd
                合并['cwd']=摘要['cwd']#写入
            if 项.get('parentSessionId') is None and 摘要.get('parentSessionId') is not None:#填父
                合并['parentSessionId']=摘要['parentSessionId']#写入
            if 项.get('origin') is None and 摘要.get('origin') is not None:#填来源
                合并['origin']=摘要['origin']#写入
            if (合并.get('cwd')==项.get('cwd') and 合并.get('parentSessionId')==项.get('parentSessionId')
                and 合并.get('origin')==项.get('origin') and 合并.get('blank')==项.get('blank')):#无变
                return list(摘要列表)#原样
            结果=list(摘要列表)#拷
            结果[下标]=合并#替换
            return 结果#结果
        return [摘要]+list(摘要列表)#前置新项
    if 种类=='remove':#移除
        return [项 for 项 in 摘要列表 if 项['sessionId']!=变更['sessionId']]#过滤
    if 种类=='status':#运行态
        结果=[]#行
        for 项 in 摘要列表:#逐项
            if 项['sessionId']!=变更['sessionId']:#其它
                结果.append(项)#原样
            elif 项.get('running')!=变更['running'] or (变更['running'] and 项.get('blank')):#需改
                行=dict(项)#拷
                行['running']=变更['running']#写入
                行['blank']=项.get('blank',True) and not 变更['running']#blank 翻
                结果.append(行)#收下
            else:#无变
                结果.append(项)#原样
        return 结果#结果
    if 种类=='activity':#活动
        结果=[]#行
        for 项 in 摘要列表:#逐项
            if 项['sessionId']!=变更['sessionId'] or 变更['updatedAt']<=项.get('updatedAt',0):#其它
                结果.append(项)#原样
            else:#命中
                行=dict(项)#拷
                行['updatedAt']=变更['updatedAt']#写入
                结果.append(行)#收下
        return 结果#结果
    if 种类=='engaged':#接入
        结果=[]#行
        for 项 in 摘要列表:#逐项
            if 项['sessionId']!=变更['sessionId'] or not 项.get('blank'):#其它
                结果.append(项)#原样
            else:#命中
                行=dict(项)#拷
                行['blank']=False#非空白
                结果.append(行)#收下
        return 结果#结果
    return list(摘要列表)#未知

def _调用远程(方法,*参数,信号=None):
    """归一远程结果。"""
    try:
        if 信号 is not None:#有信号
            原始=方法(*参数,信号)#调用
        else:#无
            原始=方法(*参数)#调用
        if isinstance(原始,dict) and 'ok' in 原始:#信封
            return 原始#原样
        return {'ok':True,'value':原始}#包装
    except BaseException as 错误:
        return {'ok':False,'error':错误}#失败

class 会话管理器:
    """实例簇 + 帧入口 + session 列表。"""

    def __init__(自身,远程):
        """构造。"""
        自身._远程=远程#远程
        自身._会话表={}#实例簇
        自身._处置中=set()#处置
        自身._投影存储表={}#投影
        自身._摘要列表=[]#摘要
        自身._列表状态='idle'#活动态
        自身._列表相位='pending'#到达相位
        自身._列表错误=None#错误
        自身._列表飞行=None#飞行
        自身._列表变更=None#待重放
        自身._地址表={}#子地址
        自身._目录表={}#目录
        自身._目录飞行={}#飞行目录
        自身._目录陈旧=set()#陈旧
        自身._打开目录=set()#打开目录
        自身._目录防抖={}#防抖
        自身._任务表={}#作业
        自身._条目缓存={}#条目身份
        自身._项缓存=()#items
        自身._通知器=通知器(自身._重建列表快照)#通知
        自身._列表快照=自身._构建列表快照()#首快照

    def resolveTarget(自身,目标):
        """解析获取目标而不物化 Session。"""
        if isinstance(目标,str):#身份
            标识=目标#id
            地址=自身.navigationAddress(标识)#导航
        else:#子地址
            标识=目标['childSessionId']#子 id
            地址=目标#地址
        if (isinstance(目标,str) and 标识 not in 自身._会话表
            and not any(摘要['sessionId']==标识 for 摘要 in 自身._摘要列表)
            and 地址 is None):#未知
            raise RuntimeError('sessions.retain: unknown session '+str(标识))#拒绝
        if 地址 is not None:#保留
            自身._地址表[标识]=地址#写入
        实例=自身._会话表[标识] if 标识 in 自身._会话表 else None#实例
        if 实例 is not None:#配置
            父可用=None if 地址 is None else (自身._目录表[地址['parentSessionId']].get('parentAvailable') if 地址['parentSessionId'] in 自身._目录表 else None)#父
            实例.configureSubagent(地址,父可用)#配置
        return 标识#id

    def subagentAddress(自身,会话标识):
        """返回保留的子地址。"""
        return 自身.navigationAddress(会话标识)#委托

    def navigationAddress(自身,会话标识):
        """解析面包屑导航地址。"""
        if 会话标识 in 自身._地址表:#保留
            return 自身._地址表[会话标识]#命中
        for 父标识,目录 in 自身._目录表.items():#扫目录
            for 条目 in 目录['entries']:#找子
                if 条目.get('kind')=='child' and 条目.get('id')==会话标识:#命中
                    return {'parentSessionId':父标识,'childSessionId':会话标识,'mode':条目['mode']}#派生
        return None#无

    def drop(自身,会话标识,期望=None):
        """丢弃精确实例。"""
        实例=自身._会话表[会话标识] if 会话标识 in 自身._会话表 else None#实例
        if 期望 is not None and 实例 is not 期望:#替换
            return#空
        if 实例 is None:#无
            return#空
        自身._会话表.pop(会话标识,None)#移出
        自身._地址表.pop(会话标识,None)#地址
        自身._启动处置(实例)#处置

    def dispose(自身):
        """停止计时器与全部实例。"""
        for 定时器 in list(自身._目录防抖.values()):#清防抖
            定时器.cancel()#取消
        自身._目录防抖.clear()#清空
        自身._目录陈旧.clear()#清空
        自身._打开目录.clear()#清空
        实例列表=list(自身._会话表.values())#快照
        自身._会话表.clear()#清空
        自身._地址表.clear()#清空
        for 实例 in 实例列表:#处置
            自身._启动处置(实例)#启动
        while len(自身._处置中)>0:#排空
            time.sleep(0.01)#短等

    def get(自身,会话标识):
        """惰性构建：返回已有或新建实例。"""
        if 会话标识 in 自身._会话表:#已有
            return 自身._会话表[会话标识]#实例
        实例=自身._创建会话(会话标识)#新建
        自身._会话表[会话标识]=实例#入簇
        摘要=None#摘要
        for 项 in 自身._摘要列表:#找
            if 项['sessionId']==会话标识:#命中
                摘要=项#记下
                break#停
        if 摘要 is not None:#有摘要
            实例.handleBlank(摘要.get('blank',True))#空白
            实例.handleRunning(摘要.get('running',False))#运行
        else:#目录子项
            地址=自身._地址表[会话标识] if 会话标识 in 自身._地址表 else None#地址
            if 地址 is not None and 地址['parentSessionId'] in 自身._目录表:#有目录
                for 条目 in 自身._目录表[地址['parentSessionId']]['entries']:#找子
                    if 条目.get('kind')=='child' and 条目.get('id')==会话标识:#命中
                        实例.handleBlank(False)#非空白
                        实例.handleRunning(条目.get('activity')=='running')#活动
                        break#停
        return 实例#实例

    def refreshSubagents(自身,父会话标识):
        """刷新直接子目录（single-flight）。"""
        if 父会话标识 in 自身._目录飞行:#复用
            return#空
        先前=自身._目录表[父会话标识] if 父会话标识 in 自身._目录表 else None#先前
        可展开=set()#可展开
        活动行={}#活动
        自身._目录表[父会话标识]={
            'entries':list(先前['entries']) if 先前 is not None else [],
            **(_目录可用性(先前.get('parentAvailable') if 先前 else None)),
            'state':'loading',
            'error':None,
        }#占位
        自身._通知器.标脏()#脏
        飞行={'expandableRows':可展开,'activityRows':活动行,'parentAvailableOverride':None}#飞行态
        自身._目录飞行[父会话标识]=飞行#登记
        def 后台刷新目录():
            """拉目录。"""
            try:
                子面=自身._远程.subagents if hasattr(自身._远程,'subagents') else 自身._远程['subagents']#subagents
                结果=_调用远程(子面.list,父会话标识)#列表
                if 结果.get('ok'):#成功
                    值=结果['value']#目录
                    条目=自身._带目录变更(值.get('entries',[]),可展开,活动行)#折叠变更
                    父可用=飞行['parentAvailableOverride'] if 飞行['parentAvailableOverride'] is not None else 值.get('parentAvailable')#父
                    自身._目录表[父会话标识]={
                        'entries':条目,
                        **(_目录可用性(父可用)),
                        'state':'ready',
                        'error':None,
                    }#写入
                    for 子标识,地址 in list(自身._地址表.items()):#子地址
                        if 地址['parentSessionId']!=父会话标识:#其它
                            continue#跳过
                        if 子标识 in 自身._会话表:#已实例
                            自身._会话表[子标识].handleSubagentParentAvailable(bool(父可用))#父可用
                else:#失败
                    自身._目录表[父会话标识]={
                        'entries':自身._带目录变更(list(先前['entries']) if 先前 is not None else [],可展开,活动行),
                        **(_目录可用性(飞行['parentAvailableOverride'] if 飞行['parentAvailableOverride'] is not None else (先前.get('parentAvailable') if 先前 else None))),
                        'state':'error',
                        'error':结果['error'],
                    }#错误
            finally:
                自身._目录飞行.pop(父会话标识,None)#移除飞行
                if 父会话标识 in 自身._目录陈旧:#trailing
                    自身._目录陈旧.discard(父会话标识)#清
                    自身.refreshSubagents(父会话标识)#再刷
                自身._通知器.标脏()#脏
        线=threading.Thread(target=后台刷新目录)#后台
        线.daemon=True#守护
        线.start()#启

    def setSubagentCatalogOpen(自身,父会话标识,打开):
        """目录打开态。"""
        if 打开:#打开
            自身._打开目录.add(父会话标识)#登记
            自身.refreshSubagents(父会话标识)#刷新
        else:#关闭
            自身._打开目录.discard(父会话标识)#移除
            定时器=自身._目录防抖.pop(父会话标识,None)#防抖
            if 定时器 is not None:#有
                定时器.cancel()#取消

    def refreshList(自身):
        """全量刷新列表。"""
        if 自身._列表飞行 is not None:#复用
            return#空
        自身._列表状态='loading'#加载
        自身._列表错误=None#清错
        已建=list(自身._摘要列表)#基线
        变更=[]#变更日志
        自身._列表变更=变更#登记
        自身._通知器.标脏()#脏
        自身._列表飞行=True#飞行
        def 后台刷新列表():
            """拉列表。"""
            try:
                会话面=自身._远程.session if hasattr(自身._远程,'session') else 自身._远程['session']#session
                结果=_调用远程(会话面.list,{})#列表
                if 自身._列表变更 is not 变更:#代际
                    return#丢
                if 结果.get('ok'):#成功
                    项=结果['value'].get('items',[])#项
                    基线=list(项) if 自身._列表相位=='pending' else 合并有序基线(已建,项,lambda 摘要:摘要['sessionId'])#合并
                    摘要=基线#起点
                    for 一条 in 变更:#重放
                        摘要=_应用变更(摘要,一条)#应用
                    自身._摘要列表=摘要#写入
                    自身._列表状态='idle'#空闲
                    自身._列表相位='ready'#就绪
                    for 行 in 自身._摘要列表:#推位
                        if 行['sessionId'] not in 自身._会话表:#未实例
                            continue#跳过
                        实例=自身._会话表[行['sessionId']]#实例
                        实例.handleBlank(行.get('blank',True))#空白
                        实例.handleRunning(行.get('running',False))#运行
                    for 行 in 项:#投影播种
                        块=行.get('projections')#块
                        if 块 is None:#无
                            continue#跳过
                        存储=自身._投影存储(行['sessionId'])#存储
                        值表=块.get('values',{})#值
                        切点=_规范游标(块.get('asOfSeq',-1))#切点
                        for 键 in 值表:#按键
                            存储.应用(键,值表[键],切点)#应用
                else:#失败
                    自身._列表状态='error'#错误
                    自身._列表错误=结果['error']#记下
            finally:
                if 自身._列表变更 is 变更:#本代
                    自身._列表变更=None#清
                    自身._列表飞行=None#清
                    自身._通知器.标脏()#脏
        线=threading.Thread(target=后台刷新列表)#后台
        线.daemon=True#守护
        线.start()#启

    def search(自身,查询,信号=None):
        """搜索。"""
        会话面=自身._远程.session if hasattr(自身._远程,'session') else 自身._远程['session']#session
        结果=_调用远程(会话面.search,{'query':查询},信号=信号)#搜索
        if not 结果.get('ok'):#失败
            return 结果#原样
        值=结果['value']#值
        return {'ok':True,'value':{'items':list(值.get('items',[])),'hasMore':值.get('hasMore',False)}}#结果

    def create(自身,选项=None):
        """创建会话。"""
        if 选项 is None:#缺省
            选项={}#空
        共享={} if 选项.get('sessionId') is None else {'sessionId':选项['sessionId']}#共享
        if 选项.get('workspaceId') is not None:#工作区
            载荷={'workspaceId':选项['workspaceId'],**共享}#载荷
        else:#目录
            载荷={**( {} if 选项.get('cwd') is None else {'cwd':选项['cwd']} ),**共享}#载荷
        会话面=自身._远程.session if hasattr(自身._远程,'session') else 自身._远程['session']#session
        结果=_调用远程(会话面.create,载荷)#创建
        if 结果.get('ok'):#成功
            自身._记录变更({'kind':'upsert','summary':{
                'sessionId':结果['value']['sessionId'],'updatedAt':int(time.time()*1000),
                'running':False,'blank':True,
                **({} if 选项.get('cwd') is None else {'cwd':选项['cwd']}),
            }})#合并
        else:#失败
            已发布=_工作区附着会话标识(结果['error'])#已发布
            if 已发布 is not None:#有
                自身._记录变更({'kind':'upsert','summary':{
                    'sessionId':已发布,'updatedAt':int(time.time()*1000),'running':False,'blank':True,
                }})#暴露
        return 结果#结果

    def fork(自身,选项):
        """分叉会话。"""
        源=None#源
        for 项 in 自身._摘要列表:#找
            if 项['sessionId']==选项['sessionId']:#命中
                源=项#记下
                break#停
        载荷={'sessionId':选项['sessionId']}#载荷
        if 选项.get('atSeq') is not None:#锚定
            载荷['atSeq']=选项['atSeq']#序号
        会话面=自身._远程.session if hasattr(自身._远程,'session') else 自身._远程['session']#session
        结果=_调用远程(会话面.fork,载荷)#分叉
        子标识=结果['value']['sessionId'] if 结果.get('ok') else _工作区附着会话标识(结果.get('error'))#子
        if 子标识 is not None:#有
            自身._记录变更({'kind':'upsert','summary':{
                'sessionId':子标识,'updatedAt':int(time.time()*1000),'running':False,'blank':False,
                'parentSessionId':选项['sessionId'],
                **({} if 源 is None or 源.get('cwd') is None else {'cwd':源['cwd']}),
            }})#合并
        return 结果#结果

    def 订阅(自身,监听者):
        """订阅列表。"""
        return 自身._通知器.订阅(监听者)#取消

    def getListSnapshot(自身):
        """取列表快照。"""
        自身._通知器.确保新鲜()#新鲜
        return 自身._列表快照#快照

    def projectionValues(自身,会话标识):
        """读投影值。"""
        存储=自身._投影存储表[会话标识] if 会话标识 in 自身._投影存储表 else None#存储
        return None if 存储 is None else 存储.诸值()#值

    def handleControlFrame(自身,帧):
        """控制帧。"""
        类型=帧.get('type') if isinstance(帧,dict) else getattr(帧,'type',None)#类型
        if 类型=='baseline':#基线
            自身._替换控制基线(帧['value'] if isinstance(帧,dict) else 帧.value)#替换
            return#结束
        if 类型=='projection':#投影
            会话标识=帧['sessionId'] if isinstance(帧,dict) else 帧.sessionId#id
            键=帧['key'] if isinstance(帧,dict) else 帧.key#键
            值=帧['value'] if isinstance(帧,dict) else 帧.value#值
            序号=帧['seq'] if isinstance(帧,dict) else 帧.seq#序号
            自身._投影存储(会话标识).应用(键,值,_规范游标(序号))#应用
            自身._通知器.标脏()#脏
            return#结束
        作业=帧['jobs'] if isinstance(帧,dict) else 帧.jobs#作业
        会话标识=帧['sessionId'] if isinstance(帧,dict) else 帧.sessionId#id
        if len(作业)==0:#空
            自身._任务表.pop(会话标识,None)#删
        else:#有
            自身._任务表[会话标识]=作业#写
        自身._通知器.标脏()#脏

    def handleSessionAdded(自身,摘要):
        """列表新增。"""
        自身._记录变更({'kind':'upsert','summary':摘要})#合并
        if 摘要['sessionId'] in 自身._会话表:#已实例
            自身._会话表[摘要['sessionId']].handleBlank(摘要.get('blank',True))#空白
        投影=摘要.get('projections')#投影
        if 投影 is not None:#有
            存储=自身._投影存储(摘要['sessionId'])#存储
            for 键,值 in 投影.get('values',{}).items():#按键
                存储.应用(键,值,_规范游标(投影.get('asOfSeq',-1)))#应用
        if 摘要.get('origin')=='subagent' and 摘要.get('parentSessionId') is not None:#子
            自身._标记目录父可展开(摘要['parentSessionId'])#可展开
        if 摘要.get('parentSessionId') is not None and 摘要['parentSessionId'] in 自身._打开目录:#打开目录
            自身._调度目录刷新(摘要['parentSessionId'])#防抖

    def handleSessionRemoved(自身,会话标识):
        """列表移除。"""
        摘要=None#摘要
        for 项 in 自身._摘要列表:#找
            if 项['sessionId']==会话标识:#命中
                摘要=项#记下
                break#停
        持久子=摘要 is not None and 摘要.get('origin')=='subagent' or 会话标识 in 自身._地址表#持久子
        自身._记录变更({'kind':'status','sessionId':会话标识,'running':False} if 持久子 else {'kind':'remove','sessionId':会话标识})#变更
        自身._更新目录活动(会话标识,False)#活动
        if 会话标识 in 自身._会话表:#已实例
            if 持久子:#持久
                自身._会话表[会话标识].handleRunning(False)#停
            else:#普通
                自身._会话表[会话标识].handleRemoved()#移除
        自身._任务表.pop(会话标识,None)#作业
        if not 持久子:#非持久
            自身._投影存储表.pop(会话标识,None)#投影
        if 会话标识 in 自身._目录飞行:#飞行
            自身._目录飞行[会话标识]['parentAvailableOverride']=False#覆盖
            自身._目录陈旧.add(会话标识)#陈旧
        if 会话标识 in 自身._目录表 and 自身._目录表[会话标识].get('parentAvailable'):#自有目录
            目录=dict(自身._目录表[会话标识])#拷
            目录['parentAvailable']=False#不可用
            自身._目录表[会话标识]=目录#写
        for 子标识,地址 in list(自身._地址表.items()):#子
            if 地址['parentSessionId']==会话标识 and 子标识 in 自身._会话表:#父被移
                自身._会话表[子标识].handleSubagentParentAvailable(False)#父不可用

    def handleSessionStatus(自身,会话标识,运行中):
        """状态。"""
        自身._记录变更({'kind':'status','sessionId':会话标识,'running':运行中})#变更
        if 会话标识 in 自身._会话表:#已实例
            自身._会话表[会话标识].handleRunning(运行中)#转发
        自身._更新目录活动(会话标识,运行中)#目录

    def handleSessionActivity(自身,会话标识,更新于):
        """活动。"""
        自身._记录变更({'kind':'activity','sessionId':会话标识,'updatedAt':更新于})#变更

    def handleSessionError(自身,会话标识,消息):
        """错误。"""
        if 会话标识 in 自身._会话表:#已实例
            自身._会话表[会话标识].handleAgentError(消息)#转发

    def handleConnected(自身):
        """重连。"""
        for 存储 in 自身._投影存储表.values():#清空投影
            存储.清空()#清
        自身._列表变更=None#清
        自身._列表飞行=None#清
        自身.refreshList()#刷新列表
        父集=set(自身._打开目录)#打开目录
        for 标识 in 自身._会话表:#已实例
            地址=自身._地址表[标识] if 标识 in 自身._地址表 else None#地址
            if 地址 is not None:#有
                父集.add(地址['parentSessionId'])#父
        for 父 in 父集:#刷新
            自身.refreshSubagents(父)#刷

    def _创建会话(自身,会话标识):
        """新建会话。"""
        地址=自身._地址表[会话标识] if 会话标识 in 自身._地址表 else None#地址
        父可用=None if 地址 is None else (自身._目录表[地址['parentSessionId']].get('parentAvailable') if 地址['parentSessionId'] in 自身._目录表 else None)#父
        选项={}#选项
        if 地址 is not None:#有地址
            选项['address']=地址#地址
            选项.update(_目录可用性(父可用))#父
        def 已接入(接入会话):
            """首次接入。"""
            自身._记录变更({'kind':'engaged','sessionId':接入会话.sessionId})#变更
        选项['onEngaged']=已接入#回调
        选项['projections']=自身._投影存储(会话标识)#投影
        return 会话(会话标识,自身._远程,选项)#实例

    def _投影存储(自身,会话标识):
        """按需投影存储。"""
        if 会话标识 in 自身._投影存储表:#已有
            return 自身._投影存储表[会话标识]#存储
        存储=投影值存储()#新建
        存储.订阅任意(lambda:自身._通知器.标脏())#任意键
        自身._投影存储表[会话标识]=存储#入表
        return 存储#存储

    def _启动处置(自身,实例):
        """启动处置。"""
        自身._处置中.add(实例)#登记
        def 后台():
            """处置。"""
            try:
                实例.dispose()#拆
            finally:
                自身._处置中.discard(实例)#移除
        线=threading.Thread(target=后台)#后台
        线.daemon=True#守护
        线.start()#启

    def _记录变更(自身,变更):
        """记录并应用变更。"""
        if 自身._列表变更 is not None:#飞行
            自身._列表变更.append(变更)#日志
        自身._摘要列表=_应用变更(自身._摘要列表,变更)#应用
        自身._通知器.标脏()#脏

    def _替换控制基线(自身,基线):
        """替换控制基线。"""
        自身._任务表.clear()#清作业
        for 会话标识,作业 in (基线.get('jobs') or {}).items():#作业
            if len(作业)>0:#有
                自身._任务表[会话标识]=作业#写
        for 会话标识,块 in (基线.get('projections') or {}).items():#投影
            存储=自身._投影存储(会话标识)#存储
            切点=_规范游标(块.get('asOfSeq',-1))#切点
            存储.播种({**块,'asOfSeq':切点})#播种
        自身._通知器.标脏()#脏

    def _调度目录刷新(自身,父会话标识):
        """目录防抖刷新。"""
        if 父会话标识 in 自身._目录防抖:#已有
            return#空
        def 到期():
            """到期回调。"""
            自身._目录防抖.pop(父会话标识,None)#清
            if 父会话标识 in 自身._目录飞行:#飞行
                自身._目录陈旧.add(父会话标识)#陈旧
                return#空
            自身.refreshSubagents(父会话标识)#刷
        定时器=threading.Timer(0.05,到期)#50ms
        定时器.daemon=True#守护
        自身._目录防抖[父会话标识]=定时器#登记
        定时器.start()#启

    def _更新目录活动(自身,子会话标识,运行中):
        """目录活动。"""
        活动='running' if 运行中 else 'inactive'#活动
        for 飞行 in 自身._目录飞行.values():#飞行
            飞行['activityRows'][子会话标识]=活动#记
        变了=False#变
        for 父标识,目录 in list(自身._目录表.items()):#目录
            if not any(条目.get('kind')=='child' and 条目.get('id')==子会话标识 and 条目.get('activity')!=活动 for 条目 in 目录['entries']):#无变
                continue#跳过
            条目列表=[]#新表
            for 条目 in 目录['entries']:#逐条
                if 条目.get('kind')=='child' and 条目.get('id')==子会话标识:#命中
                    行=dict(条目)#拷
                    行['activity']=活动#写
                    条目列表.append(行)#收
                else:#其它
                    条目列表.append(条目)#原样
            新目录=dict(目录)#拷
            新目录['entries']=条目列表#写
            自身._目录表[父标识]=新目录#入表
            变了=True#变
        if 变了:#变
            自身._通知器.标脏()#脏

    def _标记目录父可展开(自身,父会话标识):
        """可展开提示。"""
        自身._应用目录父可展开(父会话标识)#应用
        for 飞行 in 自身._目录飞行.values():#飞行
            飞行['expandableRows'].add(父会话标识)#记

    def _应用目录父可展开(自身,父会话标识):
        """应用可展开。"""
        变了=False#变
        for 目录父,目录 in list(自身._目录表.items()):#目录
            if not any(条目.get('kind')=='child' and 条目.get('id')==父会话标识 and not 条目.get('hasChildren') for 条目 in 目录['entries']):#无
                continue#跳过
            条目列表=[]#新
            for 条目 in 目录['entries']:#逐条
                if 条目.get('kind')=='child' and 条目.get('id')==父会话标识 and not 条目.get('hasChildren'):#命中
                    行=dict(条目)#拷
                    行['hasChildren']=True#可展开
                    条目列表.append(行)#收
                else:#其它
                    条目列表.append(条目)#原样
            新目录=dict(目录)#拷
            新目录['entries']=条目列表#写
            自身._目录表[目录父]=新目录#入表
            变了=True#变
        if 变了:#变
            自身._通知器.标脏()#脏

    def _带目录变更(自身,条目,可展开,活动行):
        """折叠目录变更。"""
        结果=[]#行
        for 条目项 in 条目:#逐条
            if 条目项.get('kind')!='child':#非子
                结果.append(条目项)#原样
                continue#下一项
            活动=活动行[条目项['id']] if 条目项['id'] in 活动行 else None#活动
            if 条目项['id'] not in 可展开 and 活动 is None:#无变
                结果.append(条目项)#原样
                continue#下一项
            行=dict(条目项)#拷
            if 条目项['id'] in 可展开:#可展开
                行['hasChildren']=True#写
            if 活动 is not None:#活动
                行['activity']=活动#写
            结果.append(行)#收
        return 结果#结果

    def _重建列表快照(自身):
        """通知器回调。"""
        自身._列表快照=自身._构建列表快照()#重建

    def _构建列表快照(自身):
        """构建列表快照。"""
        合并=[]#带标题
        for 摘要 in 自身._摘要列表:#逐行
            存储=自身._投影存储表[摘要['sessionId']] if 摘要['sessionId'] in 自身._投影存储表 else None#存储
            标题=存储.取('title') if 存储 is not None else None#标题
            投影值=存储.诸值() if 存储 is not None else None#投影
            行=dict(摘要)#拷
            if isinstance(标题,str) and 标题!='':#有标题
                行['title']=标题#写
            if 投影值 is not None:#有投影
                行['projectionValues']=投影值#写
            合并.append(行)#收
        新鲜=展平谱系(合并)#展平
        项=[]#项
        for 条目 in 新鲜:#逐条
            前=自身._条目缓存[条目['sessionId']] if 条目['sessionId'] in 自身._条目缓存 else None#前
            if (前 is not None and 前.get('updatedAt')==条目.get('updatedAt')
                and 前.get('running')==条目.get('running') and 前.get('blank')==条目.get('blank')
                and 前.get('parentSessionId')==条目.get('parentSessionId') and 前.get('cwd')==条目.get('cwd')
                and 前.get('origin')==条目.get('origin') and 前.get('title')==条目.get('title')
                and 前.get('depth')==条目.get('depth') and 前.get('projectionValues') is 条目.get('projectionValues')):#稳定
                项.append(前)#复用
            else:#新
                自身._条目缓存[条目['sessionId']]=条目#缓存
                项.append(条目)#收
        标识集=set(条目['sessionId'] for 条目 in 项)#ids
        for 标识 in list(自身._条目缓存.keys()):#清旧
            if 标识 not in 标识集:#不在
                自身._条目缓存.pop(标识,None)#删
        同序=len(项)==len(自身._项缓存) and all(项[下标] is 自身._项缓存[下标] for 下标 in range(len(项)))#同序
        if not 同序:#变
            自身._项缓存=tuple(项)#缓存
        return {
            'items':自身._项缓存,
            'state':自身._列表状态,
            'phase':自身._列表相位,
            'error':自身._列表错误,
            'subagentsByParent':dict(自身._目录表),
            'jobsBySession':dict(自身._任务表),
        }#快照
