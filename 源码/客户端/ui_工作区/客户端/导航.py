'工作区归档、打开会话和目录操作。给别的界面调用的方法同时留着上游英文名'
from datetime import datetime
from ....依赖.cordis.服务 import 服务
from ...存储 import 创建快照存储
from ..异常 import 目录浏览错误,错误名,远程码
from .文案 import 中文
from .置顶顺序 import 置顶账本键,置顶顺序来源

__all__=['工作区界面服务','取同步结果','最近工作区']

def 取同步结果(产出):
    '封装直接返回值就用它。期约若在这次调用里结算，取出值或抛出拒绝'
    if 产出 is None or not (hasattr(产出,'然后') or hasattr(产出,'then')):#不是期约
        return 产出#原值
    箱={'好':False,'坏':False,'值':None}#结算箱
    def 成功(值):
        '兑现'
        箱['好']=True#成功
        箱['值']=值#值
    def 失败(错):
        '拒绝'
        箱['坏']=True#失败
        箱['值']=错#原因
    if hasattr(产出,'然后'):#中文期约
        产出.然后(成功,失败)#接上
    else:#上游期约
        产出.then(成功,失败)#接上
    if not 箱['好'] and not 箱['坏']:#回调还没跑
        态=getattr(产出,'state',None)#状态
        if 态 in ('fulfilled','resolved'):#已兑现
            箱['好']=True#成功
            箱['值']=getattr(产出,'data',None)#数据
        elif 态=='rejected':#已拒绝
            箱['坏']=True#失败
            箱['值']=getattr(产出,'data',None)#原因
    if 箱['坏']:#拒绝
        错=箱['值']#原因
        if isinstance(错,BaseException):#异常
            raise 错#抛出
        raise RuntimeError(str(错))#包成异常
    if 箱['好']:#兑现
        return 箱['值']#值
    raise RuntimeError('期约没有等待')#还没结算

def 最近工作区(工作区列,摘要表):
    '最近有会话更新的工作区。打平时间用工作区创建时间，并列时保持宿主顺序里先遇到的'
    选中=None#工作区号
    选中时间=float('-inf')#时间
    for 工作区 in 工作区列:#宿主顺序
        最近=float('-inf')#组内最近
        for 会话号 in 工作区['sessionIds']:#成员
            会话=摘要表.get(会话号)#摘要
            if 会话 is not None:#有
                最近=max(最近,会话['updatedAt'])#更新
        if 最近==float('-inf'):#没有会话时间
            原文=工作区.get('createdAt')#创建串
            try:#解析
                最近=datetime.fromisoformat(str(原文).replace('Z','+00:00')).timestamp()*1000#毫秒
            except (TypeError,ValueError):#解析不了
                最近=float('-inf')#保持
        if 选中 is None or 最近>选中时间:#更新或第一次
            选中=工作区['workspaceId']#选它
            选中时间=最近#时间
    return 选中#可能没有

class 工作区界面服务(服务):
    '跨控制器的工作区导航和目录能力'
    def __init__(自身,上下文,目录选择器,工作区,会话,视图,通知):
        '登记 uiWorkspace，并开始监视列表以便恢复选中'
        super().__init__(上下文,'uiWorkspace')#服务名
        自身.目录选择器=目录选择器#目录远程
        自身.工作区=工作区#工作区控制器
        自身.会话=会话#会话控制器
        自身.视图=视图#浏览区顺序写入
        自身.通知=通知#提示通道
        自身.连接中={}#每个工作区正在连接的一次
        自身.已中止=False#寿命
        自身.选中=创建快照存储({},{'persist':{'name':'dsh.sessions.current'}})#当前选中
        自身.主引用=None#主视图引用
        自身.初始='waiting'#恢复阶段
        def 监视寿命():
            '卸下时停监视、中止寿命并释放主引用'
            停=自身.监视导航()#开始监视
            def 拆():
                '停订阅并放开引用'
                停()#退订
                自身.已中止=True#中止
                引用=自身.主引用#当前
                自身.主引用=None#清空
                if 引用 is not None:#有
                    引用.release()#释放
            return 拆#拆除
        上下文.副作用(监视寿命,'ui-workspace: Workspace navigation policy')#寿命

    def 已取消(自身,信号):
        '寿命中止，或这次导航的信号已经作废'
        if 自身.已中止:#寿命
            return True#取消
        if 信号 is None:#无信号
            return False#还在
        if getattr(信号,'aborted',False) is True:#AbortSignal
            return True#取消
        已设=getattr(信号,'is_set',None)#threading.Event
        if callable(已设) and 已设() is True:#布局导航被顶掉
            return True#取消
        return False#还在

    def 若已取消则抛(自身,信号):
        '取消之后不再替换主视图'
        if 自身.已取消(信号):#已取消
            raise RuntimeError('This operation was aborted')#中止

    def 连接工作区(自身,工作区号,选项=None):
        '复用或创建该工作区里的空白会话'
        if 选项 is None:#缺省
            选项={}#空
        return 自身.连接空白(工作区号,选项)#连接

    def 连接空白(自身,工作区号,复用):
        '没有复用选项就新建。同一工作区、同一预设的重入返回上一次结果'
        工作区=None#目标
        for 项 in 自身.工作区.list.getSnapshot()['items']:#列表
            if 项['workspaceId']==工作区号:#命中
                工作区=项#留下
                break#停
        if 工作区 is None:#没有
            raise RuntimeError('uiWorkspace.connectWorkspace: unknown workspace '+str(工作区号))#未知
        if 复用 is None:#不要复用空白
            return 取同步结果(自身.会话.create({'workspaceId':工作区号}))#新建
        预设=复用.get('agentPreset')#预设
        在途=自身.连接中.get(工作区号)#在途
        if 在途 is not None and 在途['预设']==预设 and 在途['结果'] is not None:#同一次已有结果
            return 在途['结果']#复用
        盒子={'预设':预设,'结果':None}#这次
        自身.连接中[工作区号]=盒子#记下
        try:#创建
            结果=自身.在工作区创建(工作区,复用)#创建或复用
            盒子['结果']=结果#记下
            return 结果#会话号
        finally:#结束就清
            if 自身.连接中.get(工作区号) is 盒子:#仍是这次
                del 自身.连接中[工作区号]#清掉

    def 在工作区创建(自身,工作区,选项):
        '空白且目录一致、未归档的第一条可以被复用'
        快照=自身.工作区.list.getSnapshot()#工作区
        归档=快照['archivedSessionIds']#归档
        会话快照=自身.会话.list.getSnapshot()#会话
        空白=None#可复用空白
        for 标识 in 会话快照['ids']:#列表顺序
            摘要=会话快照['byId'].get(标识)#摘要
            if 摘要 is None:#没有
                continue#跳过
            if 摘要.get('blank') and 摘要.get('cwd')==工作区['path'] and 标识 in 工作区['sessionIds'] and 标识 not in 归档:#可复用
                空白=标识#这条
                break#第一条
        请求={'workspaceId':工作区['workspaceId']}#请求
        if 空白 is not None:#有空白
            请求['sessionId']=空白#点名
        if 选项.get('agentPreset') is not None:#有预设
            请求['agentPreset']=选项['agentPreset']#带上
        return 自身.创建具名(请求)#创建

    def 创建具名(自身,请求):
        '宿主若没用点名的空白，就刷新那条的投影，避免行上仍显示空白'
        会话号=取同步结果(自身.会话.create(请求))#创建
        点名=请求.get('sessionId')#点名
        if 点名 is not None and 点名!=会话号:#空白被拒绝
            try:#刷新投影
                取同步结果(自身.会话.refreshProjections(点名))#重载
            except Exception as 原因:#刷新失败只记日志
                print('declined blank Session projection reload failed:',原因)#日志
        return 会话号#会话号

    def 恢复空白(自身,工作区号,会话号):
        '按日志里的预设重新打开空白。预设没了就退回宿主默认'
        取同步结果(自身.会话.refreshProjections(会话号))#先重载
        摘要=自身.会话.list.getSnapshot()['byId'].get(会话号) or {}#摘要
        投影=摘要.get('projectionValues') or {}#投影
        记录=投影.get('agentPreset')#预设
        请求={'workspaceId':工作区号,'sessionId':会话号}#请求
        if not isinstance(记录,str):#没有预设
            return 自身.创建具名(请求)#默认
        try:#按记录的预设
            return 自身.创建具名({**请求,'agentPreset':记录})#带预设
        except Exception as 错误:#失败
            码=远程码(错误) if 错误名(错误)=='SessionCreateError' else None#创建拒绝才读码
            if 码!='agent-preset/not-found' and 码!='agent-preset/invalid':#不是预设失效
                raise#其它照抛
            return 自身.创建具名(请求)#退回默认

    def 打开会话(自身,目标):
        '选中会话并露出对话'
        自身.替换主(目标,自身,'reveal')#替换

    def 打开工作区(自身,工作区号,打开前=None,选项=None):
        '连上工作区并打开会话。后来的导航可以盖掉这一次'
        if 选项 is None:#缺省
            选项={}#空
        return 自身.打开工作区会话(工作区号,打开前,选项)#打开

    def 打开工作区会话(自身,工作区号,打开前,复用):
        '连接失败时，若这次导航还没被盖掉，就发创建失败提示'
        导航=自身.ctx.layout.开始导航()#这次导航
        try:#连接
            会话号=自身.连接空白(工作区号,复用)#会话
        except Exception as 错误:#失败
            if not 自身.已取消(导航):#还没被盖掉
                if 错误名(错误)=='SessionCreateError':#宿主拒绝
                    远程=getattr(错误,'rpcError',None)#远程
                    if isinstance(远程,dict):#字典
                        消息=str(远程.get('code'))+': '+str(远程.get('message'))#码和说明
                    else:#对象
                        消息=str(getattr(远程,'code',''))+': '+str(getattr(远程,'message',''))#码和说明
                elif isinstance(错误,BaseException):#其它异常
                    消息=错误.args[0] if len(错误.args)>0 else str(错误)#自己的说明
                else:#不是异常
                    消息=str(错误)#转成字
                自身.通知({'kind':'createFailed','message':消息})#提示
            raise#仍抛出
        if 自身.已取消(导航):#被盖掉
            return#不打开
        自身.替换主(会话号,导航,'reveal',打开前)#打开

    def 分叉会话(自身,会话号,创建时=None,选项=None):
        '分叉。不改当前选中。标题按宿主规则递增'
        请求={'sessionId':会话号,'increaseTitle':True}#请求
        if 创建时 is not None:#有观察者
            请求['onCreated']=创建时#创建后
        if 选项 is not None and 选项.get('allowMigration') is not None:#显式迁移许可
            请求['allowMigration']=选项['allowMigration']#带上
        return 取同步结果(自身.会话.fork(请求))#子会话

    def 开始会话(自身,工作区号=None,选项=None):
        '新建或复用空白。没有工作区时，带草稿就提示，否则清空主视图'
        草稿=dict(选项 or {})#拷贝
        预设=草稿.pop('agentPreset',None) if 选项 is not None else None#预设
        草稿选项=None if 选项 is None else 草稿#其余是草稿
        要填草稿=草稿选项 is not None and (草稿选项.get('prompt') is not None or 草稿选项.get('clearPreviousDraft') is True)#要准备草稿
        工作区快照=自身.工作区.list.getSnapshot()#工作区
        会话快照=自身.会话.list.getSnapshot()#会话
        当前=None if 自身.主引用 is None else 自身.主引用.sessionId#当前
        当前工作区=None#当前所在
        if 当前 is not None:#有当前
            for 项 in 工作区快照['items']:#找
                if 当前 in 项['sessionIds']:#成员
                    当前工作区=项['workspaceId']#工作区
                    break#停
        最近=None#最近工作区
        if 工作区快照.get('phase')=='ready' and 会话快照.get('phase')=='ready':#都就绪
            最近=最近工作区(工作区快照['items'],会话快照['byId'])#最近
        目标=工作区号 if 工作区号 is not None else (当前工作区 if 当前工作区 is not None else 最近)#目标
        if 目标 is None:#没有工作区
            if 要填草稿:#还想填草稿
                自身.通知({'kind':'createFailed','message':中文['draft.workspaceRequired']})#请先选择
                return#停
            自身.清空主()#回到新会话
            return#停
        try:#打开
            if 草稿选项 is None:#普通新建
                自身.打开工作区会话(目标,None,None)#新建
            else:#带草稿
                def 准备(标识):
                    '打开前填草稿'
                    绑定=自身.会话.binding(标识)#绑定
                    if 绑定 is None:#没有
                        自身.草稿准备失败()#失败
                    自身.准备草稿(绑定,草稿选项)#填入
                打开前=准备 if 要填草稿 else None#要填才准备
                复用={} if 预设 is None else {'agentPreset':预设}#预设
                自身.打开工作区(目标,打开前,复用)#打开
        except Exception as 原因:#失败只记日志
            print('new session failed:',原因)#日志

    def 准备草稿(自身,绑定,选项):
        '交给对话输入。没有对话或被挡住都算准备失败'
        对话=自身.ctx.获取服务('conversation',False)#对话
        if 对话 is None:#没有
            自身.草稿准备失败()#失败
        结果=对话.input.requestDraftInitialization(绑定,选项)#填入
        if 结果=='blocked':#被挡住
            自身.草稿准备失败()#失败

    def 草稿准备失败(自身):
        '提示并抛出。调用处写了两次，所以留在这里'
        消息=中文['draft.initializationFailed']#中文原文
        自身.通知({'kind':'createFailed','message':消息})#提示
        raise RuntimeError(消息)#抛出

    def 归档会话(自身,会话号,选项=None):
        '归档。若归档的是当前会话，清空主视图'
        if 选项 is None:#缺省
            选项={}#空
        取同步结果(自身.工作区.archiveSession(会话号,选项))#归档
        if 自身.主引用 is not None and 自身.主引用.sessionId==会话号:#正是当前
            自身.清空主()#清空

    def 取消归档会话(自身,会话号):
        '取消归档，位置回到记录里的工作区'
        取同步结果(自身.工作区.unarchiveSession(会话号))#取消

    def 置顶会话(自身,会话号):
        '宿主置顶之后，再把它写到账本最前'
        取同步结果(自身.工作区.pinSession(会话号))#置顶
        快照=自身.工作区.list.getSnapshot()#完成后的快照
        自身.视图.pinSessionOrder(
            会话号,
            置顶账本键(快照['items'],会话号),
            置顶顺序来源(快照['items'],自身.会话.list.getSnapshot(),{
                'pinnedSessionIds':快照['pinnedSessionIds'],
                'archivedSessionIds':快照['archivedSessionIds'],
            }),
        )#提前

    def 取消置顶会话(自身,会话号):
        '取消置顶。已保存的位置不动'
        取同步结果(自身.工作区.unpinSession(会话号))#取消

    def 挑选目录(自身):
        '打开宿主目录选择。取消则返回 None'
        结果=取同步结果(自身.目录选择器.pick())#选择
        if not isinstance(结果,dict) or not 结果.get('ok'):#失败
            错=结果.get('error') if isinstance(结果,dict) else None#错误
            消息=错.get('message') if isinstance(错,dict) else getattr(错,'message','')#说明
            raise RuntimeError('directory picker failed: '+str(消息))#抛出
        return 结果.get('value')#路径或空

    def 列出目录(自身,路径=None,信号=None):
        '列一层目录。失败抛目录浏览错误'
        结果=取同步结果(自身.目录选择器.list(路径,信号))#列举
        if not isinstance(结果,dict) or not 结果.get('ok'):#失败
            错=结果.get('error') if isinstance(结果,dict) else 结果#错误
            raise 目录浏览错误(错)#浏览失败
        return 结果.get('value')#列表

    def 创建目录(自身,路径,名称):
        '在已有目录下建子目录'
        结果=取同步结果(自身.目录选择器.createDirectory(路径,名称))#创建
        if not isinstance(结果,dict) or not 结果.get('ok'):#失败
            错=结果.get('error') if isinstance(结果,dict) else 结果#错误
            raise 目录浏览错误(错)#浏览失败
        return 结果.get('value')#绝对路径

    def 监视导航(自身):
        '列表一变就核对当前选中。第一次就绪时恢复上次的会话'
        def 核对():
            '归档的当前选中先清掉。还在等待时才做初次恢复'
            if 自身.已中止:#已卸
                return#停
            if 自身.清掉已归档的当前():#清掉了
                return#这次到此
            if 自身.初始!='waiting':#不是等待
                return#不再恢复
            工作区=自身.工作区.list.getSnapshot()#工作区
            会话=自身.会话.list.getSnapshot()#会话
            if 工作区.get('phase')!='ready' or 会话.get('phase')!='ready':#还没就绪
                return#再等
            if 自身.主引用 is not None:#已经有主视图
                自身.初始='done'#完成
                return#停
            自身.初始='connecting'#开始连
            try:#恢复
                自身.恢复选中(工作区,会话)#恢复
                自身.初始='done'#完成
            except Exception as 原因:#失败回到等待
                if 自身.已中止:#已卸
                    return#不改
                自身.初始='waiting'#再试
                print('initial Session restoration failed:',原因)#日志
        卸工作区=自身.工作区.list.subscribe(核对)#订工作区
        卸会话=自身.会话.list.subscribe(核对)#订会话
        核对()#立刻一次
        def 停():
            '退订并中止寿命'
            自身.已中止=True#中止
            卸会话()#退会话
            卸工作区()#退工作区
        return 停#拆除

    def 恢复选中(自身,工作区,会话):
        '有子地址就打开它。空白且还在原目录则按预设恢复，否则打开最近工作区'
        已存=自身.选中.getSnapshot()#持久选中
        if 已存.get('subagentAddress') is not None:#子地址
            自身.替换主(已存['subagentAddress'],自身,'preserve')#打开
            return#停
        摘要=None if 已存.get('sessionId') is None else 会话['byId'].get(已存['sessionId'])#摘要
        所在=None#工作区
        if 摘要 is not None:#有摘要
            for 项 in 工作区['items']:#找
                if 摘要['id'] in 项['sessionIds']:#成员
                    所在=项#工作区
                    break#停
        if 摘要 is not None and (not 摘要.get('blank') or 所在 is None):#不是可恢复的空白
            自身.替换主(摘要['id'],自身,'preserve')#打开
            return#停
        导航=自身.ctx.layout.开始导航()#这次恢复
        会话号=None#要打开的
        if 摘要 is not None and 所在 is not None and 摘要.get('cwd')==所在['path'] and 摘要['id'] not in 工作区['archivedSessionIds']:#空白还在
            会话号=自身.恢复空白(所在['workspaceId'],摘要['id'])#按预设
        目标=所在['workspaceId'] if 所在 is not None else 最近工作区(工作区['items'],会话['byId'])#目标
        if 目标 is None and len(工作区['items'])==0 and len(会话['ids'])==0:#完全是空的
            准备=自身.初始化默认工作区(导航)#默认工作区
            if 自身.已取消(导航):#被盖掉
                return#停
            if 准备 is not None:#有
                目标=准备.get('workspaceId')#用它
        if 会话号 is None and 目标 is not None:#还要连接
            会话号=自身.连接工作区(目标)#连接
        if 会话号 is not None and not 自身.已取消(导航):#可以打开
            自身.替换主(会话号,导航,'preserve')#保持面板

    def 初始化默认工作区(自身,信号):
        '失败只发提示，不抛'
        try:#初始化
            return 取同步结果(自身.工作区.initializeDefault(信号))#工作区或空
        except Exception:#失败
            if not 自身.已取消(信号):#还没被盖掉
                自身.通知({'kind':'defaultWorkspaceFailed'})#提示
            return None#没有

    def 清掉已归档的当前(自身):
        '当前会话被归档就清空主视图'
        当前=None if 自身.主引用 is None else 自身.主引用.sessionId#当前
        if 当前 is None:#没有
            return False#没清
        if 当前 not in 自身.工作区.list.getSnapshot()['archivedSessionIds']:#没归档
            return False#没清
        自身.清空主()#清空
        return True#清了

    def 清空主(自身):
        '放开主引用，选中写空，面板回到对话'
        先前=自身.主引用#旧引用
        自身.主引用=None#清空
        自身.选中.set({})#空选中
        if 先前 is not None:#有
            先前.release()#释放
        自身.ctx.layout.selectPanel(None)#回对话

    def 替换主(自身,目标,信号,面板,打开前=None):
        '保留新引用，写上选中。reveal 时把面板收成对话'
        自身.若已取消则抛(信号)#先看取消
        引用=自身.会话.retain(目标,{'source':'mainView'})#保留
        try:#打开前和写选中
            自身.若已取消则抛(信号)#再看
            if 打开前 is not None:#有准备
                打开前(引用.sessionId)#准备
            if 自身.已取消(信号):#准备期间被盖掉
                引用.release()#放开
                return#不替换
            if isinstance(目标,str):#会话号
                子地址=自身.会话.subagentAddress(引用.sessionId)#可能有子地址
            else:#已经是子地址
                子地址=目标#用它
            选中={'sessionId':引用.sessionId}#选中
            if 子地址 is not None:#有子地址
                选中['subagentAddress']=子地址#带上
            自身.选中.set(选中)#写入
        except Exception:#失败放开这次引用
            引用.release()#放开
            raise#再抛
        先前=自身.主引用#旧的
        自身.主引用=引用#换成新的
        if 先前 is not None:#有旧的
            先前.release()#放开
        if 面板=='reveal':#要露出对话
            自身.ctx.layout.selectPanel(None)#收面板

    connectWorkspace=连接工作区#跨包
    openSession=打开会话#跨包
    openWorkspace=打开工作区#跨包
    forkSession=分叉会话#跨包
    startSession=开始会话#跨包
    archiveSession=归档会话#跨包
    unarchiveSession=取消归档会话#跨包
    pinSession=置顶会话#跨包
    unpinSession=取消置顶会话#跨包
    pickDirectory=挑选目录#跨包
    listDirectory=列出目录#跨包
    createDirectory=创建目录#跨包
