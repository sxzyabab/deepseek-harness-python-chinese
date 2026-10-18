'会话簇：实例簇、帧分发与列表状态'
from ....基础设施.通用工具 import 当前毫秒,启动守护线程
from .有序基线 import 合并有序基线#有序合并
from .谱系 import 展平谱系#谱系
from .通知器 import 通知器#通知
from .投影存储 import 投影值存储#投影
from .会话 import 会话#会话类
from ..异常 import 远程错误#远程失败

__all__=['会话簇']#仅中文公开名

def _规范游标(值):
    '规范投影游标'
    return -1 if 值==-1 else 值#游标

def _工作区附着会话标识(错误):
    '从附着失败细节取已发布会话 id'
    if 错误 is None:#无
        return None#无
    码=错误.code if hasattr(错误,'code') else (错误.get('code') if isinstance(错误,dict) else None)#码
    if 码!='session/workspace-attach-failed':#其它
        return None#无
    细节=错误.details if hasattr(错误,'details') else (错误['details'] if isinstance(错误,dict) and 'details' in 错误 else None)#细节
    if not isinstance(细节,dict) or 'sessionId' not in 细节:#无
        return None#无
    return 细节['sessionId']#id

def _取会话标识(摘要):
    '列表合并用的稳定身份'
    return 摘要['sessionId']#id

def _是否远程失败(错误):
    '结构识别远程失败'
    if isinstance(错误,远程错误):#本包
        return True#是
    if isinstance(错误,dict) and 'code' in 错误 and 'message' in 错误:#信封
        return True#是
    return getattr(错误,'isDSHRemoteError',False) is True#标记

def _应用变更(摘要列表,变更):
    '应用一条列表变更，不另排显示顺序'
    种类=变更['kind']#种类
    if 种类=='upsert' or 种类=='placeholder':#插入或补元数据
        摘要=变更['summary']#摘要
        标识=摘要['sessionId']#id
        for 下标,项 in enumerate(摘要列表):#找已有
            if 项['sessionId']!=标识:#其它
                continue#下一项
            合并=dict(项)#拷
            合并['blank']=项.get('blank',True) and 摘要.get('blank',True)#blank 仅降
            if 种类=='upsert':#宿主摘要改运行态
                合并['agentAvailable']=摘要.get('agentAvailable')#可用性
                合并['running']=摘要.get('running',False)#运行
                if 'formatStatus' in 摘要:#格式
                    合并['formatStatus']=摘要['formatStatus']#写入
            if 'cwd' not in 项 and 'cwd' in 摘要:#填 cwd
                合并['cwd']=摘要['cwd']#写入
            if 'parentSessionId' not in 项 and 'parentSessionId' in 摘要:#填父
                合并['parentSessionId']=摘要['parentSessionId']#写入
            if 'origin' not in 项 and 'origin' in 摘要:#填来源
                合并['origin']=摘要['origin']#写入
            if (合并.get('cwd')==项.get('cwd') and 合并.get('parentSessionId')==项.get('parentSessionId')
                and 合并.get('origin')==项.get('origin') and 合并.get('blank')==项.get('blank')
                and 合并.get('agentAvailable')==项.get('agentAvailable') and 合并.get('running')==项.get('running')
                and 合并.get('formatStatus')==项.get('formatStatus')):#无变
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
            elif (项.get('running')!=变更['running'] or 项.get('agentAvailable')!=变更.get('agentAvailable')
                or (变更['running'] and 项.get('blank'))):#需改
                行=dict(项)#拷
                行['running']=变更['running']#写入
                行['agentAvailable']=变更['agentAvailable']#可用性
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
    '归一远程结果'
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

class 会话簇:
    '实例簇 + 帧入口 + session 列表'

    def __init__(自身,远程):
        '构造'
        自身._远程=远程#远程
        自身._会话表={}#实例簇
        自身._已接入=set()#本地已发送或宿主运行
        自身._已拆=False#已拆
        自身._投影存储表={}#投影
        自身._投影负载={}#显式读取状态
        自身._摘要列表=[]#摘要
        自身._列表状态='idle'#活动态
        自身._列表相位='pending'#到达相位
        自身._列表错误=None#错误
        自身._列表飞行=None#飞行
        自身._列表变更=None#待重放
        自身._地址表={}#子地址
        自身._条目缓存={}#条目身份
        自身._项缓存=()#items
        自身._通知器=通知器(自身._重建列表快照)#通知
        自身._列表快照=自身._构建列表快照()#首快照

    def resolveTarget(自身,目标):
        '解析获取目标而不物化 Session'
        if isinstance(目标,str):#身份
            标识=目标#id
            地址=自身.subagentAddress(标识)#导航
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
        if 实例 is not None:#已有
            父可用=None if 地址 is None else 自身._智能体可用(地址['parentSessionId'])#父
            实例.configureSubagent(地址,父可用)#配置
        return 标识#id

    def subagentAddress(自身,会话标识):
        '保留地址、目录投影、再退到未知模式的列表头'
        if 会话标识 in 自身._地址表:#保留
            return 自身._地址表[会话标识]#命中
        for 父标识,存储 in 自身._投影存储表.items():#扫投影
            目录=存储.诸值().get('subagentCatalog')#名录
            if not isinstance(目录,list):#无
                continue#下一父
            for 条目 in 目录:#找子
                if isinstance(条目,dict) and 条目.get('id')==会话标识 and 条目.get('mode')!='external':#命中
                    return {'parentSessionId':父标识,'childSessionId':会话标识,'mode':条目.get('mode')}#派生
        for 摘要 in 自身._摘要列表:#列表头
            if 摘要['sessionId']==会话标识 and 摘要.get('origin')=='subagent' and 摘要.get('parentSessionId') is not None:#子
                return {'parentSessionId':摘要['parentSessionId'],'childSessionId':会话标识,'mode':'unknown'}#未知
        return None#无

    def drop(自身,会话标识,期望=None):
        '丢弃精确实例'
        实例=自身._会话表[会话标识] if 会话标识 in 自身._会话表 else None#实例
        if 实例 is not 期望:#替换或没有
            return#空
        自身._会话表.pop(会话标识,None)#移出
        自身._地址表.pop(会话标识,None)#地址
        自身._修剪接入(会话标识,自身._保留标识(自身._摘要列表))#接入
        实例.dispose()#拆

    def dispose(自身):
        '停止列表请求并拆掉全部实例'
        自身._已拆=True#标记
        自身._列表变更=None#清
        自身._列表飞行=None#清
        自身._已接入.clear()#清
        实例列表=list(自身._会话表.values())#快照
        自身._会话表.clear()#清空
        自身._地址表.clear()#清空
        for 实例 in 实例列表:#处置
            实例.dispose()#拆

    def get(自身,会话标识):
        '惰性构建：返回已有或新建实例'
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
            实例.handleBlank(自身._有效空白(摘要))#空白
            实例.handleRunning(摘要.get('running',False))#运行
        else:#目录子项或尚未入列表
            地址=自身._地址表[会话标识] if 会话标识 in 自身._地址表 else None#地址
            子=None#目录项
            if 地址 is not None and 地址['parentSessionId'] in 自身._投影存储表:#有父投影
                目录=自身._投影存储表[地址['parentSessionId']].诸值().get('subagentCatalog')#名录
                if isinstance(目录,list):#有
                    for 条目 in 目录:#找子
                        if isinstance(条目,dict) and 条目.get('id')==会话标识:#命中
                            子=条目#记下
                            break#停
            if 子 is not None and 子.get('mode')!='external':#已编目
                实例.handleBlank(False)#非空白
                实例.handleRunning(False)#未运行
            else:#保留先到
                实例.handleBlank(True)#空白
        return 实例#实例

    def refreshProjections(自身,会话标识):
        '不启动迁移地读投影。已就绪的不重复拉，失败和待迁移可以再读'
        if 自身._投影负载.get(会话标识,{}).get('state')=='ready':#已就绪
            return None#空
        存储=自身._投影存储(会话标识)#存储
        初始值=存储.诸值()#读前引用
        自身._投影负载[会话标识]={'state':'loading','error':None}#加载
        自身._通知器.标脏()#脏
        try:
            结果=_调用远程(自身._远程.session.projections,{'sessionId':会话标识})#读取
            if 自身._已拆:#已拆
                return None#停
            if 结果.get('ok'):#成功
                值=结果.get('value')#结果
                if 值 is not None:#有块
                    种类=值.get('kind')#种类
                    if 种类=='sequenced':#有序号
                        存储.播种({'values':值.get('values') or {},'asOfSeq':_规范游标(值.get('asOfSeq',-1))})#播种
                    elif 种类=='migration-required':#待迁移
                        存储.应用缓存(值.get('values') or {})#缓存提示
                    else:#未知
                        raise RuntimeError('session projections result')#封闭
                elif 存储.诸值() is 初始值:#没有后来的帧
                    存储.清空()#缺席
                自身._投影负载[会话标识]={
                    'state':'migration-required' if 值 is not None and 值.get('kind')=='migration-required' else 'ready',
                    'error':None,
                }#落定
            else:#业务失败
                自身._投影负载[会话标识]={'state':'error','error':结果.get('error')}#错误
        except BaseException as 错误:
            if 自身._已拆:#已拆
                return None#停
            if not _是否远程失败(错误):#其它
                raise#抛
            自身._投影负载[会话标识]={'state':'error','error':错误}#错误
        finally:
            自身._通知器.标脏()#脏
        return None#完成

    def _智能体可用(自身,会话标识):
        '父会话是否还能派子任务'
        for 摘要 in 自身._摘要列表:#找
            if 摘要['sessionId']==会话标识:#命中
                return 摘要.get('agentAvailable')#可用性
        if 自身._列表相位=='ready':#列表已到
            return False#不可用
        return None#未知

    def _更新父可用(自身):
        '把父可用性推到已保留的子实例'
        for 子标识,地址 in 自身._地址表.items():#子
            可用=自身._智能体可用(地址['parentSessionId'])#父
            if 可用 is not None and 子标识 in 自身._会话表:#可写
                自身._会话表[子标识].handleSubagentParentAvailable(可用)#推

    def _有效空白(自身,摘要):
        '本地已接入的会话不再显示为空白'
        return bool(摘要.get('blank',True)) and 摘要['sessionId'] not in 自身._已接入#空白

    def _保留标识(自身,摘要列表):
        '列表行、实例和保留地址都还占着这个身份'
        保留=set(项['sessionId'] for 项 in 摘要列表)#行
        for 会话标识 in 自身._会话表:#实例
            保留.add(会话标识)#加上
        for 会话标识 in 自身._地址表:#地址
            保留.add(会话标识)#加上
        return 保留#集合

    def _修剪接入(自身,会话标识,保留):
        '没有保留身份时忘掉本地接入'
        if 会话标识 not in 保留:#不在
            自身._已接入.discard(会话标识)#删

    def refreshList(自身):
        '全量刷新列表'
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
            '拉列表'
            try:
                会话面=自身._远程.session#session
                结果=_调用远程(会话面.list,{})#列表
                if 自身._列表变更 is not 变更:#代际
                    return#丢
                if 结果.get('ok'):#成功
                    项=结果['value'].get('items',[])#项
                    基线=list(项) if 自身._列表相位=='pending' else 合并有序基线(已建,项,_取会话标识)#合并
                    期间移除=set()#拉取后移除
                    for 一条 in 变更:#找移除
                        if 一条['kind']=='remove':#移除
                            期间移除.add(一条['sessionId'])#记下
                    for 行 in 基线:#运行即接入
                        if 行.get('running') and 行['sessionId'] not in 期间移除:#仍在
                            自身._已接入.add(行['sessionId'])#接入
                    摘要=基线#起点
                    for 一条 in 变更:#重放
                        摘要=_应用变更(摘要,一条)#应用
                    自身._摘要列表=摘要#写入
                    保留=自身._保留标识(摘要)#保留
                    for 会话标识 in list(自身._已接入):#修剪
                        自身._修剪接入(会话标识,保留)#修剪
                    自身._列表状态='idle'#空闲
                    自身._列表相位='ready'#就绪
                    自身._更新父可用()#父
                    for 行 in 自身._摘要列表:#推位
                        if 行['sessionId'] not in 自身._会话表:#未实例
                            continue#跳过
                        实例=自身._会话表[行['sessionId']]#实例
                        实例.handleBlank(自身._有效空白(行))#空白
                        实例.handleRunning(行.get('running',False))#运行
                    for 行 in 项:#投影块
                        if 行.get('projections') is not None:#有
                            自身._应用列表块(行['sessionId'],行['projections'])#合并
                else:
                    自身._列表状态='error'#错误
                    自身._列表错误=结果['error']#记下
            except BaseException as 错误:
                if not _是否远程失败(错误):#其它
                    raise#抛
                if 自身._列表变更 is not 变更:#代际
                    return#丢
                自身._列表状态='error'#错误
                自身._列表错误=错误#记下
            finally:
                if 自身._列表变更 is 变更:#本代
                    自身._列表变更=None#清
                    自身._列表飞行=None#清
                    自身._通知器.标脏()#脏
        启动守护线程(后台刷新列表)#启

    def search(自身,查询,信号=None):
        '搜索'
        会话面=自身._远程.session#session
        结果=_调用远程(会话面.search,{'query':查询},信号=信号)#搜索
        if not 结果.get('ok'):
            return 结果#原样
        值=结果['value']#值
        return {'ok':True,'value':{'items':list(值.get('items',[])),'hasMore':值.get('hasMore',False)}}#结果

    def create(自身,选项=None):
        '创建会话'
        if 选项 is None:#缺省
            选项={}#空
        共享={}#共享
        if 'sessionId' in 选项 and 选项['sessionId'] is not None:#点名
            共享['sessionId']=选项['sessionId']#id
        if 'agentPreset' in 选项 and 选项['agentPreset'] is not None:#预设
            共享['agentPreset']=选项['agentPreset']#预设
        if 'workspaceId' in 选项 and 选项['workspaceId'] is not None:#工作区
            载荷={'workspaceId':选项['workspaceId'],**共享}#载荷
        else:#目录
            载荷=dict(共享)#载荷
            if 'cwd' in 选项 and 选项['cwd'] is not None:#目录
                载荷['cwd']=选项['cwd']#写入
        会话面=自身._远程.session#session
        结果=_调用远程(会话面.create,载荷)#创建
        if 结果.get('ok'):#成功
            自身._记录变更({'kind':'placeholder','summary':{
                'sessionId':结果['value']['sessionId'],'updatedAt':当前毫秒(),
                'running':False,'blank':True,'agentAvailable':True,
                **({} if 'cwd' not in 选项 or 选项.get('cwd') is None else {'cwd':选项['cwd']}),
            }})#占位
        else:
            已发布=_工作区附着会话标识(结果.get('error'))#已发布
            if 已发布 is not None:#有
                自身._记录变更({'kind':'placeholder','summary':{
                    'sessionId':已发布,'updatedAt':当前毫秒(),'running':False,'blank':True,'agentAvailable':True,
                }})#暴露
        return 结果#结果

    def fork(自身,选项):
        '分叉会话'
        源=None#源
        for 项 in 自身._摘要列表:#找
            if 项['sessionId']==选项['sessionId']:#命中
                源=项#记下
                break#停
        载荷={'sessionId':选项['sessionId']}#载荷
        if 'atSeq' in 选项 and 选项['atSeq'] is not None:#锚定
            载荷['atSeq']=选项['atSeq']#序号
        if 'allowMigration' in 选项:#迁移
            载荷['allowMigration']=选项['allowMigration']#许可
        会话面=自身._远程.session#session
        结果=_调用远程(会话面.fork,载荷)#分叉
        子标识=结果['value']['sessionId'] if 结果.get('ok') else _工作区附着会话标识(结果.get('error'))#子
        if 子标识 is not None:#有
            自身._记录变更({'kind':'placeholder','summary':{
                'sessionId':子标识,'updatedAt':当前毫秒(),'running':False,'blank':True,'agentAvailable':True,
                'parentSessionId':选项['sessionId'],
                **({} if 源 is None or 'cwd' not in 源 else {'cwd':源['cwd']}),
            }})#占位
        return 结果#结果

    def 订阅(自身,监听者):
        '订阅列表'
        return 自身._通知器.订阅(监听者)#取消

    def getListSnapshot(自身):
        '取列表快照'
        自身._通知器.确保新鲜()#新鲜
        return 自身._列表快照#快照

    def projectionValues(自身,会话标识):
        '读投影值'
        存储=自身._投影存储表[会话标识] if 会话标识 in 自身._投影存储表 else None#存储
        return None if 存储 is None else 存储.诸值()#值

    def handleControlFrame(自身,帧):
        '控制帧'
        类型=帧.get('type') if isinstance(帧,dict) else getattr(帧,'type',None)#类型
        if 类型=='baseline':#基线
            自身._替换控制基线(帧['value'] if isinstance(帧,dict) else 帧.value)#替换
            return#停
        if 类型=='projection':#投影
            会话标识=帧['sessionId'] if isinstance(帧,dict) else 帧.sessionId#id
            键=帧['key'] if isinstance(帧,dict) else 帧.key#键
            值=帧['value'] if isinstance(帧,dict) else 帧.value#值
            序号=帧['seq'] if isinstance(帧,dict) else 帧.seq#序号
            自身._投影存储(会话标识).应用(键,值,_规范游标(序号))#应用
            自身._通知器.标脏()#脏
            return#停
        raise RuntimeError('unknown control frame')#封闭

    def _替换控制基线(自身,基线):
        '替换控制基线里的投影块'
        for 会话标识,块 in (基线.get('projections') or {}).items():#投影
            存储=自身._投影存储(会话标识)#存储
            切点=_规范游标(块.get('asOfSeq',-1))#切点
            存储.播种({**块,'asOfSeq':切点})#播种
        自身._通知器.标脏()#脏

    def _应用列表块(自身,会话标识,块):
        '按块声明的序号空间合并列表投影'
        存储=自身._投影存储(会话标识)#存储
        种类=块.get('kind')#种类
        if 种类=='sequenced':#有序号
            序号=_规范游标(块.get('asOfSeq',-1))#水位
            值表=块.get('values') or {}#值
            for 键,值 in 值表.items():#逐键
                存储.应用(键,值,序号)#应用
            return#停
        if 种类=='cached':#缓存
            存储.应用缓存(块.get('values') or {})#填缺
            return#停
        raise RuntimeError('session list projection block kind')#封闭

    def handleSessionAdded(自身,摘要):
        '列表新增'
        自身._合并摘要(摘要)#合并
        if not 自身._已拆 and 摘要.get('running'):#运行
            自身._已接入.add(摘要['sessionId'])#接入
        if 摘要['sessionId'] in 自身._会话表:#已实例
            自身._会话表[摘要['sessionId']].handleBlank(自身._有效空白(摘要))#空白
        if 摘要.get('projections') is not None:#有投影
            自身._应用列表块(摘要['sessionId'],摘要['projections'])#合并

    def _合并摘要(自身,摘要):
        '写入一条宿主摘要'
        自身._记录变更({'kind':'upsert','summary':摘要})#合并
        自身._更新父可用()#父

    def handleSessionRemoved(自身,会话标识):
        '列表移除'
        摘要=None#摘要
        for 项 in 自身._摘要列表:#找
            if 项['sessionId']==会话标识:#命中
                摘要=项#记下
                break#停
        持久子=自身.subagentAddress(会话标识) is not None or (摘要 is not None and 摘要.get('origin')=='subagent')#持久子
        自身._记录变更({
            'kind':'status','sessionId':会话标识,'running':False,'agentAvailable':False,
        } if 持久子 else {'kind':'remove','sessionId':会话标识})#变更
        if 会话标识 in 自身._会话表:#已实例
            if 持久子:#持久
                自身._会话表[会话标识].handleRunning(False)#停
            else:#普通
                自身._会话表[会话标识].handleRemoved()#移除
        目录=None#名录
        if 会话标识 in 自身._投影存储表:#有存储
            目录=自身._投影存储表[会话标识].诸值().get('subagentCatalog')#名录
        if not 持久子 and (not isinstance(目录,list) or len(目录)==0):#可丢
            自身._投影存储表.pop(会话标识,None)#投影
        自身._修剪接入(会话标识,自身._保留标识(自身._摘要列表))#接入
        自身._投影负载.pop(会话标识,None)#读取状态
        for 子标识,地址 in list(自身._地址表.items()):#子
            if 地址['parentSessionId']==会话标识 and 子标识 in 自身._会话表:#父被移
                自身._会话表[子标识].handleSubagentParentAvailable(False)#父不可用

    def handleSessionStatus(自身,会话标识,运行中):
        '状态'
        if not 自身._已拆 and 运行中:#运行
            自身._已接入.add(会话标识)#接入
        自身._记录变更({'kind':'status','sessionId':会话标识,'running':运行中,'agentAvailable':True})#变更
        自身._更新父可用()#父
        if 会话标识 in 自身._会话表:#已实例
            自身._会话表[会话标识].handleRunning(运行中)#转发

    def handleSessionActivity(自身,会话标识,更新于):
        '活动'
        自身._记录变更({'kind':'activity','sessionId':会话标识,'updatedAt':更新于})#变更

    def handleSessionError(自身,会话标识,消息):
        '错误'
        if 会话标识 in 自身._会话表:#已实例
            自身._会话表[会话标识].handleAgentError(消息)#转发

    def handleConnected(自身):
        '重连后丢掉旧投影切面再拉列表和父投影'
        for 存储 in 自身._投影存储表.values():#清空投影
            存储.清空()#清
        自身._列表变更=None#清
        自身._列表飞行=None#清
        自身.refreshList()#刷新列表
        父集=set(自身._投影负载.keys())#曾读过的
        for 标识 in 自身._会话表:#已实例
            地址=自身._地址表[标识] if 标识 in 自身._地址表 else None#地址
            if 地址 is not None:#有
                父集.add(地址['parentSessionId'])#父
        自身._投影负载.clear()#清状态
        for 父 in 父集:#再读
            自身.refreshProjections(父)#读

    def _创建会话(自身,会话标识):
        '新建会话'
        地址=自身._地址表[会话标识] if 会话标识 in 自身._地址表 else None#地址
        父可用=None if 地址 is None else 自身._智能体可用(地址['parentSessionId'])#父
        选项={}#选项
        if 地址 is not None:#有地址
            选项['address']=地址#地址
            if 父可用 is not None:#已知
                选项['parentAvailable']=父可用#父
        def 已接入(接入会话):
            '首次发送翻掉空白'
            if 自身._已拆 or 接入会话.sessionId not in 自身._保留标识(自身._摘要列表):#不可
                return#停
            if 接入会话.sessionId not in 自身._已接入:#尚未记账
                自身._已接入.add(接入会话.sessionId)#记下
                自身._记录变更({'kind':'engaged','sessionId':接入会话.sessionId})#变更
            if 接入会话.sessionId in 自身._会话表:#仍在
                自身._会话表[接入会话.sessionId].handleBlank(False)#非空白
        选项['onEngaged']=已接入#回调
        选项['projections']=自身._投影存储(会话标识)#投影
        return 会话(会话标识,自身._远程,选项)#实例

    def _投影存储(自身,会话标识):
        '按需投影存储'
        if 会话标识 in 自身._投影存储表:#已有
            return 自身._投影存储表[会话标识]#存储
        存储=投影值存储()#新建
        def 任意变更(钉存储=存储,钉标识=会话标识):
            '元数据说不再空白时，纠正列表提示'
            值=钉存储.诸值()#值
            元数据=值.get('sessionListMetadata') if isinstance(值,dict) else None#元数据
            if isinstance(元数据,dict) and 元数据.get('blank') is False and 钉标识 in 自身._会话表:#已定
                自身._会话表[钉标识].handleBlank(False)#非空白
            自身._通知器.标脏()#脏
        存储.订阅任意(任意变更)#任意键
        自身._投影存储表[会话标识]=存储#入表
        return 存储#存储

    def _记录变更(自身,变更):
        '记录并应用变更'
        if 自身._已拆:#已拆
            return#停
        if 自身._列表变更 is not None:#飞行
            自身._列表变更.append(变更)#日志
        自身._摘要列表=_应用变更(自身._摘要列表,变更)#应用
        自身._通知器.标脏()#脏

    def _重建列表快照(自身):
        '通知器回调'
        自身._列表快照=自身._构建列表快照()#重建

    def _构建列表快照(自身):
        '构建列表快照'
        合并=[]#带标题
        for 摘要 in 自身._摘要列表:#逐行
            存储=自身._投影存储表[摘要['sessionId']] if 摘要['sessionId'] in 自身._投影存储表 else None#存储
            标题=存储.取('title') if 存储 is not None else None#标题
            投影值=存储.诸值() if 存储 is not None else None#投影
            元数据=投影值.get('sessionListMetadata') if isinstance(投影值,dict) else None#元数据
            最近=0#最近提示
            if isinstance(元数据,dict) and 元数据.get('lastPromptAt') is not None:#有
                最近=元数据['lastPromptAt']#时间
            行=dict(摘要)#拷
            行['blank']=自身._有效空白(摘要) and not (isinstance(元数据,dict) and 元数据.get('blank') is False)#空白
            行['updatedAt']=max(摘要.get('updatedAt',0),最近)#活动
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
                and 前.get('depth')==条目.get('depth') and 前.get('formatStatus')==条目.get('formatStatus')
                and 前.get('projectionValues') is 条目.get('projectionValues')):#稳定
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
        投影按会话={}#按会话
        for 会话标识,存储 in 自身._投影存储表.items():#存储
            负载=自身._投影负载.get(会话标识)#读取状态
            快照={'values':存储.诸值(),'state':'idle','error':None}#空闲
            if 负载 is not None:#有读取
                快照['state']=负载['state']#状态
                快照['error']=负载['error']#错误
            投影按会话[会话标识]=快照#写入
        return {
            'items':自身._项缓存,
            'state':自身._列表状态,
            'phase':自身._列表相位,
            'error':自身._列表错误,
            'projectionsBySession':投影按会话,
        }#快照
