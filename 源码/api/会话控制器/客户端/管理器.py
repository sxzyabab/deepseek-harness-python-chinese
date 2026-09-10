"""会话管理器：实例簇、帧分发与列表状态。

对齐上游 `session-controller/src/client/sessions/manager.ts`。公开面仅中文名。
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
            if 项['sessionId']==标识:#命中
                合并=dict(项)#拷
                for 键,值 in 摘要.items():#填缺失／更新
                    if 键=='sessionId':#身份
                        continue#跳过
                    if 键 not in 合并 or 合并[键] is None:#缺失
                        合并[键]=值#写入
                    elif 键 in ('updatedAt','running','blank','cwd','parentSessionId','origin','title'):#权威字段
                        合并[键]=值#覆盖
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
            else:#命中
                行=dict(项)#拷
                行['running']=变更['running']#写入
                结果.append(行)#收下
        return 结果#结果
    if 种类=='activity':#活动
        结果=[]#行
        for 项 in 摘要列表:#逐项
            if 项['sessionId']!=变更['sessionId']:#其它
                结果.append(项)#原样
            else:#命中
                行=dict(项)#拷
                行['updatedAt']=变更['updatedAt']#写入
                结果.append(行)#收下
        return 结果#结果
    if 种类=='engaged':#接入
        结果=[]#行
        for 项 in 摘要列表:#逐项
            if 项['sessionId']!=变更['sessionId']:#其它
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

    def __init__(自身,远程,恢复选中=None,恢复地址=None):
        """构造。"""
        自身._远程=远程#远程
        自身._会话表={}#实例簇
        自身._处置中=set()#处置
        自身._队列表={}#队列缓存
        自身._完成提醒=set()#完成提醒
        自身._先前运行={}#上次运行
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
        自身._选中=恢复选中#选中
        if 恢复地址 is not None:#恢复地址
            自身._地址表[恢复地址['childSessionId']]=恢复地址#写入
        自身._条目缓存={}#条目身份
        自身._项缓存=()#items
        自身._通知器=通知器(自身._重建列表快照)#通知
        自身._列表快照=自身._构建列表快照()#首快照

    def select(自身,会话标识):
        """选择已列出或目录寻址会话。"""
        地址=自身.navigationAddress(会话标识)#导航地址
        if (not any(摘要['sessionId']==会话标识 for 摘要 in 自身._摘要列表)) and 地址 is None:#未知
            raise RuntimeError('sessions.select: unknown session '+str(会话标识))#拒绝
        if 地址 is not None:#保留
            自身._地址表[会话标识]=地址#写入
        实例=自身._会话表[会话标识] if 会话标识 in 自身._会话表 else None#实例
        if 实例 is not None:#配置
            父可用=None if 地址 is None else (自身._目录表[地址['parentSessionId']]['parentAvailable'] if 地址['parentSessionId'] in 自身._目录表 and 'parentAvailable' in 自身._目录表[地址['parentSessionId']] else None)#父
            实例.configureSubagent(地址,父可用)#配置
        自身._选中=会话标识#选中
        自身._完成提醒.discard(会话标识)#清提醒
        自身.refreshSubagents(会话标识)#刷新
        自身._通知器.立即通知()#通知

    def selectSubagent(自身,地址):
        """经持久直接父地址选择健康子项。"""
        目录=自身._目录表[地址['parentSessionId']] if 地址['parentSessionId'] in 自身._目录表 else None#目录
        条目=None#条目
        if 目录 is not None:#有目录
            for 候选 in 目录['entries']:#找子
                if 候选.get('kind')=='child' and 候选.get('id')==地址['childSessionId']:#命中
                    条目=候选#记下
                    break#停
        if 条目 is None or 条目.get('mode')!=地址.get('mode'):#不健康
            raise RuntimeError('sessions.selectSubagent: '+str(地址['childSessionId'])+' is not a healthy catalog child')#拒绝
        自身._地址表[地址['childSessionId']]=地址#保留
        实例=自身._会话表[地址['childSessionId']] if 地址['childSessionId'] in 自身._会话表 else None#实例
        if 实例 is not None:#配置
            实例.configureSubagent(地址,目录.get('parentAvailable') if 目录 else None)#配置
        自身._选中=地址['childSessionId']#选中
        自身._完成提醒.discard(地址['childSessionId'])#清
        自身.refreshSubagents(地址['childSessionId'])#刷新
        自身._通知器.立即通知()#通知

    def clearSelection(自身):
        """清除选择。"""
        自身._选中=None#清空
        自身._通知器.立即通知()#通知

    def subagentAddress(自身,会话标识):
        """返回保留的子地址。"""
        return 自身._地址表[会话标识] if 会话标识 in 自身._地址表 else None#地址

    def navigationAddress(自身,会话标识):
        """解析面包屑导航地址。"""
        if 会话标识 in 自身._地址表:#保留
            return 自身._地址表[会话标识]#命中
        for 父标识,目录 in 自身._目录表.items():#扫目录
            for 条目 in 目录['entries']:#找子
                if 条目.get('kind')=='child' and 条目.get('id')==会话标识:#命中
                    return {'parentSessionId':父标识,'childSessionId':会话标识,'mode':条目['mode']}#派生
        return None#无

    def drop(自身,会话标识):
        """丢弃会话实例。"""
        实例=自身._会话表.pop(会话标识,None)#取出
        if 实例 is not None:#有
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
        实例.replaceControl(自身._队列表[会话标识] if 会话标识 in 自身._队列表 else [])#安装队列
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
        def 跑():
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
                    for 条目项 in 条目:#保留地址
                        if 条目项.get('kind')!='child':#非子
                            continue#跳过
                        子标识=条目项['id']#id
                        自身._地址表[子标识]={'parentSessionId':父会话标识,'childSessionId':子标识,'mode':条目项['mode']}#地址
                        if 子标识 in 自身._会话表:#已实例
                            自身._会话表[子标识].configureSubagent(自身._地址表[子标识],父可用)#配置
                            自身._会话表[子标识].handleSubagentParentAvailable(bool(父可用))#父可用
                else:#失败
                    自身._目录表[父会话标识]={
                        'entries':list(先前['entries']) if 先前 is not None else [],
                        **(_目录可用性(先前.get('parentAvailable') if 先前 else None)),
                        'state':'error',
                        'error':结果['error'],
                    }#错误
            finally:
                自身._目录飞行.pop(父会话标识,None)#移除飞行
                自身._通知器.标脏()#脏
                if 父会话标识 in 自身._目录陈旧:#trailing
                    自身._目录陈旧.discard(父会话标识)#清
                    自身.refreshSubagents(父会话标识)#再刷
        threading.Thread(target=跑,daemon=True).start()#后台

    def setSubagentCatalogOpen(自身,父会话标识,打开):
        """标记目录菜单打开态。"""
        if 打开:#打开
            自身._打开目录.add(父会话标识)#登记
            自身.refreshSubagents(父会话标识)#刷新
        else:#关闭
            自身._打开目录.discard(父会话标识)#移除

    def refreshList(自身):
        """经 session.list 全量刷新（single-flight）。"""
        if 自身._列表飞行 is not None:#复用
            自身._列表飞行.等待()#等
            return#空
        自身._列表状态='loading'#加载
        自身._列表错误=None#清
        已建立=list(自身._摘要列表)#已建立
        变更列表=[]#变更
        自身._列表变更=变更列表#登记
        自身._通知器.标脏()#脏
        任务=_任务()#飞行
        自身._列表飞行=任务#登记
        def 跑():
            """拉列表。"""
            try:
                会话面=自身._远程.session if hasattr(自身._远程,'session') else 自身._远程['session']#session
                结果=_调用远程(会话面.list,{})#列表
                if 结果.get('ok'):#成功
                    项=结果['value']['items'] if isinstance(结果['value'],dict) else 结果['value']#项
                    if 自身._列表相位=='pending':#首次
                        基线=list(项)#直接
                    else:#合并
                        基线=合并有序基线(已建立,项,lambda 摘要:摘要['sessionId'])#合并
                    for 摘要 in 基线:#播种运行位
                        if 摘要['sessionId'] not in 自身._先前运行:#首次
                            自身._先前运行[摘要['sessionId']]=摘要.get('running',False)#记录
                    摘要列表=基线#起点
                    for 变更 in 变更列表:#重放
                        摘要列表=_应用变更(摘要列表,变更)#应用
                        自身._摘要列表=摘要列表#写入
                        自身._同步完成提醒()#提醒
                    自身._摘要列表=摘要列表#最终
                    自身._列表状态='idle'#闲
                    自身._列表相位='ready'#就绪
                    自身._同步完成提醒()#提醒
                    for 摘要 in 自身._摘要列表:#推至实例
                        if 摘要['sessionId'] not in 自身._会话表:#未实例
                            continue#跳过
                        实例=自身._会话表[摘要['sessionId']]#实例
                        实例.handleBlank(摘要.get('blank',True))#空白
                        实例.handleRunning(摘要.get('running',False))#运行
                    for 摘要 in 项:#投影块
                        块=摘要['projections'] if 'projections' in 摘要 else None#块
                        if 块 is None:#无
                            continue#跳过
                        存储=自身._投影存储(摘要['sessionId'])#存储
                        值表=块['values'] if isinstance(块.get('values'),dict) else {}#值
                        切点=_规范游标(块['asOfSeq'])#切点
                        for 键 in 值表:#应用
                            存储.应用(键,值表[键],切点)#应用
                else:#失败
                    自身._列表状态='error'#错
                    自身._列表错误=结果['error']#记下
            except BaseException as 错误:
                自身._列表状态='error'#错
                自身._列表错误=错误#记下
            finally:
                自身._列表变更=None#清
                自身._列表飞行=None#清
                自身._通知器.标脏()#脏
                任务.兑现(None)#完成
        threading.Thread(target=跑,daemon=True).start()#后台
        任务.等待()#等

    def search(自身,查询,信号=None):
        """搜索消息内容。"""
        会话面=自身._远程.session if hasattr(自身._远程,'session') else 自身._远程['session']#session
        结果=_调用远程(会话面.search,{'query':查询},信号=信号)#搜索
        if not 结果.get('ok'):#失败
            return 结果#原样
        值=结果['value']#值
        return {'ok':True,'value':{'items':list(值['items']),'hasMore':值['hasMore']}}#结果

    def create(自身,选项=None):
        """创建会话并立即 merge。"""
        if 选项 is None:#缺省
            选项={}#空
        载荷={}#载荷
        if 'sessionId' in 选项 and 选项['sessionId'] is not None:#预分配
            载荷['sessionId']=选项['sessionId']#id
        if 'workspaceId' in 选项 and 选项['workspaceId'] is not None:#工作区
            载荷['workspaceId']=选项['workspaceId']#写入
        elif 'cwd' in 选项 and 选项['cwd'] is not None:#cwd
            载荷['cwd']=选项['cwd']#写入
        会话面=自身._远程.session if hasattr(自身._远程,'session') else 自身._远程['session']#session
        结果=_调用远程(会话面.create,载荷)#创建
        if 结果.get('ok'):#成功
            摘要={'sessionId':结果['value']['sessionId'],'updatedAt':int(time.time()*1000),'running':False,'blank':True}#摘要
            if 'cwd' in 选项 and 选项['cwd'] is not None:#cwd
                摘要['cwd']=选项['cwd']#写入
            自身._记录变更({'kind':'upsert','summary':摘要})#变更
        else:#失败
            已发布=_工作区附着会话标识(结果['error'])#已发布
            if 已发布 is not None:#有
                自身._记录变更({'kind':'upsert','summary':{'sessionId':已发布,'updatedAt':int(time.time()*1000),'running':False,'blank':True}})#暴露
        return 结果#结果

    def fork(自身,选项):
        """分叉并立即 merge 子项。"""
        源=None#源
        for 摘要 in 自身._摘要列表:#找源
            if 摘要['sessionId']==选项['sessionId']:#命中
                源=摘要#记下
                break#停
        载荷={'sessionId':选项['sessionId']}#载荷
        if 'atSeq' in 选项 and 选项['atSeq'] is not None:#锚点
            载荷['atSeq']=选项['atSeq']#写入
        会话面=自身._远程.session if hasattr(自身._远程,'session') else 自身._远程['session']#session
        结果=_调用远程(会话面.fork,载荷)#分叉
        子标识=结果['value']['sessionId'] if 结果.get('ok') else _工作区附着会话标识(结果.get('error'))#子 id
        if 子标识 is not None:#有子
            摘要={'sessionId':子标识,'updatedAt':int(time.time()*1000),'running':False,'blank':False,'parentSessionId':选项['sessionId']}#摘要
            if 源 is not None and 'cwd' in 源:#继承 cwd
                摘要['cwd']=源['cwd']#写入
            自身._记录变更({'kind':'upsert','summary':摘要})#变更
        return 结果#结果

    def 订阅(自身,监听者):
        """列表订阅。"""
        return 自身._通知器.订阅(监听者)#取消

    def getListSnapshot(自身):
        """缓存列表快照。"""
        自身._通知器.确保新鲜()#新鲜
        return 自身._列表快照#快照

    def handleControlFrame(自身,帧):
        """应用控制基线或替换帧。"""
        类型=帧['type']#类型
        if 类型=='baseline':#基线
            自身._替换控制基线(帧['value'])#替换
            return#结束
        if 类型=='projection':#投影
            自身._投影存储(帧['sessionId']).应用(帧['key'],帧['value'],帧['seq'])#应用
            自身._通知器.标脏()#脏
            return#结束
        if 类型=='jobs':#任务
            if len(帧['jobs'])==0:#空
                自身._任务表.pop(帧['sessionId'],None)#删
            else:#有
                自身._任务表[帧['sessionId']]=帧['jobs']#写
            自身._通知器.标脏()#脏
            return#结束
        自身._队列表[帧['sessionId']]=帧['items']#队列
        if 帧['sessionId'] in 自身._会话表:#已实例
            自身._会话表[帧['sessionId']].handleControlFrame(帧)#转发

    def handleSessionAdded(自身,摘要):
        """列表新增。"""
        自身._记录变更({'kind':'upsert','summary':摘要})#变更
        if 摘要['sessionId'] in 自身._会话表:#已实例
            自身._会话表[摘要['sessionId']].handleBlank(摘要.get('blank',True))#空白
        投影=摘要['projections'] if 'projections' in 摘要 else None#投影
        if 投影 is not None:#有
            存储=自身._投影存储(摘要['sessionId'])#存储
            值表=投影['values'] if isinstance(投影.get('values'),dict) else {}#值
            切点=_规范游标(投影['asOfSeq'])#切点
            for 键 in 值表:#应用
                存储.应用(键,值表[键],切点)#应用
        if 摘要.get('origin')=='subagent' and 'parentSessionId' in 摘要:#子
            自身._标记目录可展开(摘要['parentSessionId'])#可展开
        if 'parentSessionId' in 摘要 and (自身._选中==摘要['parentSessionId'] or 摘要['parentSessionId'] in 自身._打开目录):#需刷
            自身._调度目录刷新(摘要['parentSessionId'])#防抖

    def handleSessionRemoved(自身,会话标识):
        """列表移除。"""
        摘要=None#摘要
        for 项 in 自身._摘要列表:#找
            if 项['sessionId']==会话标识:#命中
                摘要=项#记下
                break#停
        耐久子= (摘要 is not None and 摘要.get('origin')=='subagent') or 会话标识 in 自身._地址表#耐久
        自身._记录变更({'kind':'status','sessionId':会话标识,'running':False} if 耐久子 else {'kind':'remove','sessionId':会话标识})#变更
        自身._更新目录活动(会话标识,False)#活动
        if 耐久子:#耐久
            if 会话标识 in 自身._会话表:#实例
                自身._会话表[会话标识].handleRunning(False)#停
        else:#普通
            if 会话标识 in 自身._会话表:#实例
                自身._会话表[会话标识].handleRemoved()#移除
            自身._投影存储表.pop(会话标识,None)#投影
        自身._队列表.pop(会话标识,None)#队列
        自身._任务表.pop(会话标识,None)#任务

    def handleSessionStatus(自身,会话标识,运行中):
        """运行态。"""
        自身._记录变更({'kind':'status','sessionId':会话标识,'running':运行中})#变更
        if 会话标识 in 自身._会话表:#实例
            自身._会话表[会话标识].handleRunning(运行中)#转发
        自身._更新目录活动(会话标识,运行中)#目录

    def handleSessionActivity(自身,会话标识,更新于):
        """活动时间。"""
        自身._记录变更({'kind':'activity','sessionId':会话标识,'updatedAt':更新于})#变更

    def handleSessionError(自身,会话标识,消息):
        """Agent 失败。"""
        if 会话标识 in 自身._会话表:#实例
            自身._会话表[会话标识].handleAgentError(消息)#转发

    def handleConnected(自身):
        """重连修复。"""
        自身.refreshList()#刷列表
        if 自身._选中 is not None:#有选中
            地址=自身._地址表[自身._选中] if 自身._选中 in 自身._地址表 else None#地址
            if 地址 is not None:#子
                自身.refreshSubagents(地址['parentSessionId'])#刷父
            自身.refreshSubagents(自身._选中)#刷选中
        for 父 in list(自身._打开目录):#打开目录
            自身.refreshSubagents(父)#刷

    def _创建会话(自身,会话标识):
        """创建会话实例。"""
        地址=自身._地址表[会话标识] if 会话标识 in 自身._地址表 else None#地址
        父可用=None if 地址 is None else (自身._目录表[地址['parentSessionId']].get('parentAvailable') if 地址['parentSessionId'] in 自身._目录表 else None)#父
        选项={'projections':自身._投影存储(会话标识),'onEngaged':lambda 已接入:自身._记录变更({'kind':'engaged','sessionId':已接入.sessionId})}#选项
        if 地址 is not None:#子
            选项['address']=地址#地址
            选项.update(_目录可用性(父可用))#父可用
        return 会话(会话标识,自身._远程,选项)#实例

    def _投影存储(自身,会话标识):
        """常驻 per-session 投影存储。"""
        if 会话标识 not in 自身._投影存储表:#新建
            存储=投影值存储()#新建
            存储.订阅任意(lambda:自身._通知器.标脏())#任意脏
            自身._投影存储表[会话标识]=存储#入表
        return 自身._投影存储表[会话标识]#存储

    def _替换控制基线(自身,基线):
        """替换完整控制基线。"""
        自身._队列表.clear()#清
        for 标识,项 in (基线.get('queues') or {}).items():#队列
            自身._队列表[标识]=项#写
        自身._任务表.clear()#清
        for 标识,任务 in (基线.get('jobs') or {}).items():#任务
            if len(任务)>0:#非空
                自身._任务表[标识]=任务#写
        for 标识,块 in (基线.get('projections') or {}).items():#投影
            存储=自身._投影存储(标识)#存储
            切点=_规范游标(块['asOfSeq'])#切点
            存储.截断(切点)#截断
            存储.播种({'asOfSeq':切点,'values':块['values']})#播种
        for 标识,实例 in 自身._会话表.items():#实例
            实例.replaceControl(自身._队列表[标识] if 标识 in 自身._队列表 else [])#替换
        自身._通知器.标脏()#脏

    def _记录变更(自身,变更):
        """立即应用并可选重放。"""
        if 自身._列表变更 is not None:#飞行中
            自身._列表变更.append(变更)#保留
        自身._摘要列表=_应用变更(自身._摘要列表,变更)#应用
        自身._同步完成提醒()#提醒
        自身._通知器.标脏()#脏

    def _同步完成提醒(自身):
        """reconcile 完成提醒。"""
        见到=set()#见到
        for 摘要 in 自身._摘要列表:#逐项
            标识=摘要['sessionId']#id
            见到.add(标识)#记下
            先前=自身._先前运行[标识] if 标识 in 自身._先前运行 else None#先前
            运行=摘要.get('running',False)#运行
            if 先前 is None:#首次
                自身._先前运行[标识]=运行#记录
                continue#下一项
            if 先前 and (not 运行):#下降边
                if 标识!=自身._选中:#非选中
                    自身._完成提醒.add(标识)#arm
            elif 运行:#运行
                自身._完成提醒.discard(标识)#清
            自身._先前运行[标识]=运行#更新
        for 标识 in list(自身._先前运行.keys()):#修剪
            if 标识 not in 见到:#消失
                del 自身._先前运行[标识]#删
        for 标识 in list(自身._完成提醒):#修剪提醒
            if 标识 not in 见到:#消失
                自身._完成提醒.discard(标识)#删

    def _构建列表快照(自身):
        """构造列表快照。"""
        合并=[]#行
        for 摘要 in 自身._摘要列表:#逐项
            存储=自身._投影存储表[摘要['sessionId']] if 摘要['sessionId'] in 自身._投影存储表 else None#存储
            行=dict(摘要)#拷
            if 存储 is not None:#有投影
                标题=存储.取('title')#标题
                if isinstance(标题,str) and 标题!='':#有
                    行['title']=标题#写入
                行['projectionValues']=存储.诸值()#投影值
            合并.append(行)#收下
        新鲜=展平谱系(合并,自身._完成提醒)#展平
        项列表=[]#items
        for 条目 in 新鲜:#复用身份
            先前=自身._条目缓存[条目['sessionId']] if 条目['sessionId'] in 自身._条目缓存 else None#先前
            if (
                先前 is not None
                and 先前.get('updatedAt')==条目.get('updatedAt')
                and 先前.get('running')==条目.get('running')
                and 先前.get('blank')==条目.get('blank')
                and 先前.get('parentSessionId')==条目.get('parentSessionId')
                and 先前.get('cwd')==条目.get('cwd')
                and 先前.get('title')==条目.get('title')
                and 先前.get('completed')==条目.get('completed')
                and 先前.get('depth')==条目.get('depth')
            ):#同值
                项列表.append(先前)#复用
            else:#新
                自身._条目缓存[条目['sessionId']]=条目#缓存
                项列表.append(条目)#收下
        当前=自身._选中#选中
        if 当前 is not None and (not any(项['sessionId']==当前 for 项 in 项列表)) and 当前 not in 自身._地址表:#masked
            当前=None#掩码
        地址=None if 当前 is None else (自身._地址表[当前] if 当前 in 自身._地址表 else None)#当前地址
        return {
            'items':tuple(项列表),
            'current':当前,
            'state':自身._列表状态,
            'phase':自身._列表相位,
            'error':自身._列表错误,
            'subagentsByParent':dict(自身._目录表),
            'jobsBySession':dict(自身._任务表),
            'currentAddress':地址,
        }#快照

    def _重建列表快照(自身):
        """通知器重建。"""
        自身._列表快照=自身._构建列表快照()#重建

    def _启动处置(自身,实例):
        """启动会话处置。"""
        自身._处置中.add(实例)#登记
        try:
            实例.dispose()#处置
        finally:
            自身._处置中.discard(实例)#移除

    def _调度目录刷新(自身,父会话标识):
        """防抖刷新。"""
        if 父会话标识 in 自身._目录防抖:#已调度
            return#空
        def 到期():
            """到期回调。"""
            自身._目录防抖.pop(父会话标识,None)#清
            if 父会话标识 in 自身._目录飞行:#飞行中
                自身._目录陈旧.add(父会话标识)#陈旧
                return#停
            自身.refreshSubagents(父会话标识)#刷
        定时器=threading.Timer(0.05,到期)#50ms
        定时器.daemon=True#守护
        自身._目录防抖[父会话标识]=定时器#登记
        定时器.start()#启

    def _更新目录活动(自身,子标识,运行中):
        """更新目录活动位。"""
        活动='running' if 运行中 else 'inactive'#活动
        for 飞行 in 自身._目录飞行.values():#飞行
            飞行['activityRows'][子标识]=活动#写入
        变=False#变
        for 父标识,目录 in list(自身._目录表.items()):#目录
            新条目=[]#条目
            本变=False#本变
            for 条目 in 目录['entries']:#逐条
                if 条目.get('kind')=='child' and 条目.get('id')==子标识 and 条目.get('activity')!=活动:#需改
                    行=dict(条目)#拷
                    行['activity']=活动#写
                    新条目.append(行)#收下
                    本变=True#变
                else:#原样
                    新条目.append(条目)#收下
            if 本变:#写回
                新=dict(目录)#拷
                新['entries']=新条目#写
                自身._目录表[父标识]=新#写
                变=True#变
        if 变:#脏
            自身._通知器.标脏()#脏

    def _标记目录可展开(自身,父会话标识):
        """正向可展开提示。"""
        自身._应用目录可展开(父会话标识)#应用
        for 飞行 in 自身._目录飞行.values():#飞行
            飞行['expandableRows'].add(父会话标识)#记下

    def _应用目录可展开(自身,父会话标识):
        """对已加载目录应用可展开。"""
        变=False#变
        for 目录父,目录 in list(自身._目录表.items()):#目录
            新条目=[]#条目
            本变=False#本变
            for 条目 in 目录['entries']:#逐条
                if 条目.get('kind')=='child' and 条目.get('id')==父会话标识 and not 条目.get('hasChildren'):#需
                    行=dict(条目)#拷
                    行['hasChildren']=True#写
                    新条目.append(行)#收下
                    本变=True#变
                else:#原样
                    新条目.append(条目)#收下
            if 本变:#写回
                新=dict(目录)#拷
                新['entries']=新条目#写
                自身._目录表[目录父]=新#写
                变=True#变
        if 变:#脏
            自身._通知器.标脏()#脏

    def _带目录变更(自身,条目列表,可展开,活动行):
        """折叠请求局部行变更。"""
        结果=[]#结果
        for 条目 in 条目列表:#逐条
            if 条目.get('kind')!='child':#非子
                结果.append(条目)#原样
                continue#下一项
            标识=条目['id']#id
            活动=活动行[标识] if 标识 in 活动行 else None#活动
            if 标识 not in 可展开 and 活动 is None:#无变更
                结果.append(条目)#原样
                continue#下一项
            行=dict(条目)#拷
            if 标识 in 可展开:#可展开
                行['hasChildren']=True#写
            if 活动 is not None:#活动
                行['activity']=活动#写
            结果.append(行)#收下
        return 结果#结果

class _任务:
    """简易同步任务。"""
    def __init__(自身):
        """未决。"""
        自身._事件=threading.Event()#事件
        自身._错误=None#错误
    def 兑现(自身,_值=None):
        """成功。"""
        自身._事件.set()#唤醒
    def 等待(自身):
        """阻塞。"""
        自身._事件.wait()#等
        if 自身._错误 is not None:#失败
            raise 自身._错误#抛
