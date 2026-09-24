import json,re,traceback
from ...依赖.schemastery import 自然数字段
from ...typert.协议 import 远程服务,远程 as _远程
from ...模型后端.llm import 创建用户消息
from ...内核.作用域 import 操作任务
from .门面规则 import 宿主运行器错误,是否插件,规范化处理函数
from .沙箱 import 创建沙箱,求值宿主代码,预检代码
from .注册表 import 动态cordis注册表
from .巡检注册表 import 巡检注册表服务
from .生命周期 import 启动宿主半,缺席服务列表

__all__=[
    '包名','名称','依赖','默认','配置',
    '宿主运行器错误','动态cordis运行器','巡检注册表服务',
    '动态插件标识','动态包标识','动态运行标识','审批请求标识',
]

#常量
包名='@deepseek-ai/dsh-cordis-host-runner'
名称='cordis-host-runner'
依赖=['tools']
前缀模式=re.compile(r'^[a-z]{3,6}\Z',re.ASCII)
缺省超时毫秒=5000
配置={
    'vmTimeoutMs':自然数字段(最小=1,默认值=缺省超时毫秒),
}

#工具
def 动态插件标识(标识):
    """宿主铸造的插件身份。"""
    return 标识

def 动态包标识(标识):
    """宿主铸造的包身份。"""
    return 标识

def 动态运行标识(标识):
    """宿主铸造的一次激活身份。"""
    return 标识

def 审批请求标识(标识):
    """宿主铸造的审批请求身份。"""
    return 标识

def 应用动态组(上下文,配置值=None):
    """cordis-dynamic 组的空入口。"""
    return
应用动态组.name='cordis-dynamic'

def 缺席于(上下文,运行):
    """已结算纤程仍缺席的服务名。"""
    if 'fiber' not in 运行:
        return []
    return 缺席服务列表(上下文,运行['fiber'])

def 缺席插件消息(标识):
    """进程内找不到该动态插件。"""
    return f'本进程没有动态插件 "{标识}" —— 可能已被移除，或随 DSH 重启丢失'

def 错误详情(错误):
    """抽出 message/stack 供转向与回执使用。"""
    if isinstance(错误,BaseException):
        消息=str(错误)
        if 消息=='':
            消息=type(错误).__name__
        出={'message':消息}
        if 错误.__traceback__ is not None:
            出['stack']=''.join(traceback.format_exception(错误))
        return 出
    消息=getattr(错误,'message',None)
    if isinstance(消息,str):
        出={'message':消息}
        栈=getattr(错误,'stack',None)
        if isinstance(栈,str):
            出['stack']=栈
        return 出
    return {'message':str(错误)}

def 格式化错误详情(失败):
    """给人看的失败文本。"""
    文='消息: '+失败['message']
    if 'stack' in 失败:
        文+='\n栈:\n'+失败['stack']
    return 文

def 克隆尝试(尝试):
    """快照用的尝试副本。"""
    出=dict(尝试)
    出['host']={**尝试['host'],'waitingFor':list(尝试['host']['waitingFor'])}
    出['client']={**尝试['client'],'waitingFor':list(尝试['client']['waitingFor'])}
    if 'error' in 尝试:
        出['error']=dict(尝试['error'])
    return 出

#
class 动态cordis运行器(远程服务):
    """动态插件注册表与宿主半生命周期。"""
    def __init__(自身,上下文,配置值=None):
        """登记 dynamicCordisRunner。"""
        super().__init__(上下文,'dynamicCordisRunner')
        if 配置值 is None:
            配置值={}
        自身._根上下文=上下文
        自身._超时毫秒=配置值['vmTimeoutMs'] if 'vmTimeoutMs' in 配置值 else 缺省超时毫秒
        自身._注册表=动态cordis注册表()
        自身._巡检=巡检注册表服务(上下文)
        自身._启动中={}
        自身._组=None

    def 定义(自身,请求):
        """登记新插件的第一包，或给已有插件追加一包。"""
        名称值=请求['name'].strip()
        用途=请求['purpose'].strip()
        if 名称值=='':
            raise 宿主运行器错误('cordis_define 需要非空的 `name`')
        if 用途=='':
            raise 宿主运行器错误('cordis_define 需要非空的 `purpose`')
        代码=请求['code']
        宿主码=代码['host'] if 'host' in 代码 else None
        客户端码=代码['client'] if 'client' in 代码 else None
        if 宿主码 is None and 客户端码 is None:
            raise 宿主运行器错误('cordis_define 需要 `code.host`、`code.client`，或两者都要')
        if 宿主码 is not None:
            预检代码(宿主码,'code.host')
        if 客户端码 is not None:
            预检代码(客户端码,'code.client')
        插件选择=请求['plugin']
        if 插件选择['kind']=='new':
            前缀=插件选择['idPrefix'].strip()
            if 前缀模式.match(前缀) is None:
                raise 宿主运行器错误('cordis_define 的 `plugin.idPrefix` 必须是 3–6 个小写英文字母')
            插件标识=动态插件标识(自身._注册表.铸造插件标识(前缀))
            插件={
                'pluginId':插件标识,
                'sessionId':请求['sessionId'],
                'packages':{},
                'approvedClientPackages':set(),
                'clientVersionUpdatesApproved':False,
            }
            自身._注册表.加入(插件)
        else:
            找到=自身._注册表.获取(插件选择['pluginId'])
            if 找到 is None or 找到['sessionId']!=请求['sessionId']:
                raise 宿主运行器错误(缺席插件消息(插件选择['pluginId']))
            插件=找到
        包标识=动态包标识(自身._注册表.铸造包标识())
        定义={'packageId':包标识,'name':名称值,'purpose':用途}
        if 宿主码 is not None:
            定义['hostCode']=宿主码
        if 客户端码 is not None:
            定义['clientCode']=客户端码
        插件['packages'][包标识]=定义
        return {
            'pluginId':插件['pluginId'],
            'packageId':包标识,
            'name':名称值,
            'purpose':用途,
            'hasHostHalf':'hostCode' in 定义,
            'hasClientHalf':'clientCode' in 定义,
        }

    def 取消定义(自身,智能体,插件标识):
        """移除插件、其活动运行与全部不可变包。"""
        插件=自身._属下(智能体,插件标识)
        if 插件 is None:
            return {'ok':False,'reason':'plugin-missing','message':缺席插件消息(插件标识)}
        曾在运行='run' in 插件
        自身._取消待决(插件标识,f'动态插件 "{插件标识}" 在审批前被移除')
        if 'run' in 插件:
            自身._撤回(插件)
        自身._注册表.删除(插件标识)
        return {'ok':True,'wasRunning':曾在运行}

    @_远程('undefineFromPanel')
    def 从面板取消定义(自身,智能体,插件标识):
        """面板移除插件，并把状态变化注入模型下一步。"""
        结果=自身.取消定义(智能体,插件标识)
        if 结果['ok']:
            自身._注入用户上下文(
                智能体,
                f'用户移除了 Cordis 插件 {插件标识} 及其全部包。该插件已不存在。',
            )
        return 结果

    def 运行(自身,智能体,插件标识,包标识,模式,信号=None):
        """模型工具调用的启动或更新；未授权的客户端包等待审批。"""
        计划=自身._解析计划(智能体,插件标识,包标识,模式)
        if not 计划['ok']:
            return 计划['response']
        if 信号 is not None and 信号.is_set():
            return {
                'ok':False,
                'reason':'cancelled',
                'message':f'动态插件 "{插件标识}" 的运行请求在激活前被取消',
            }
        if 自身._注册表.待决请求(插件标识) is not None:
            return {
                'ok':False,
                'reason':'transition-in-flight',
                'message':f'动态插件 "{插件标识}" 已有待决运行请求',
            }
        尝试=自身._创建尝试(计划)
        计划['plugin']['nextPackageId']=包标识
        计划['plugin']['latestRun']=尝试
        if 'clientCode' not in 计划['definition']:
            已启动=自身._激活(计划,None,False,尝试)
            if 已启动['ok']:
                return 自身._运行回执(计划['plugin'],已启动)
            自身._失败尝试(计划['plugin'],尝试,'host-load',已启动)
            return {**已启动,'reason':'host-half-failed'}
        请求标识=审批请求标识(自身._注册表.铸造审批标识())
        需要审批=(
            not 计划['plugin']['clientVersionUpdatesApproved']
            and 包标识 not in 计划['plugin']['approvedClientPackages']
        )
        尝试['approvalRequestId']=请求标识
        尝试['requiresApproval']=需要审批
        尝试['status']='awaiting-approval' if 需要审批 else 'starting-host'
        自身._注册表.武装请求(请求标识,{
            'agentId':智能体.id,
            'pluginId':插件标识,
            'packageId':包标识,
            'pluginRunId':尝试['pluginRunId'],
            'mode':模式,
            'requiresApproval':需要审批,
        })
        自身.ctx.广播('cordis/request-run',{
            'requestId':请求标识,
            'agentId':智能体.id,
            'pluginId':插件标识,
            'packageId':包标识,
            'mode':模式,
            'name':计划['definition']['name'],
            'purpose':计划['definition']['purpose'],
            'requiresApproval':需要审批,
        })
        出={
            'ok':True,
            'status':'awaiting-approval' if 需要审批 else 'starting',
            'pluginId':插件标识,
            'packageId':包标识,
            'pluginRunId':尝试['pluginRunId'],
            'mode':模式,
            'waitingFor':[],
            'nextPackageId':包标识,
        }
        if 'currentPackageId' in 计划['plugin']:
            出['currentPackageId']=计划['plugin']['currentPackageId']
        return 出

    @_远程('runHostHalf')
    def 执行宿主半(自身,智能体,插件标识,包标识,模式,请求标识,批准后续版本):
        """为已批准请求或面板手势启动宿主代码。"""
        计划=自身._解析计划(智能体,插件标识,包标识,模式,请求标识 is None)
        if not 计划['ok']:
            return {'ok':False,'message':计划['response']['message']}
        if 请求标识 is not None:
            待决=自身._注册表.窥视请求(请求标识)
            if (
                待决 is None
                or 待决['pluginId']!=插件标识
                or 待决['packageId']!=包标识
                or 待决['mode']!=模式
            ):
                return {'ok':False,'message':f'运行请求 "{请求标识}" 未授权 {插件标识}/{包标识}'}
            最近=计划['plugin']['latestRun'] if 'latestRun' in 计划['plugin'] else None
            期望='awaiting-approval' if 待决['requiresApproval'] else 'starting-host'
            if (
                最近 is None
                or 最近['pluginRunId']!=待决['pluginRunId']
                or (最近['status']!=期望 and not (
                    not 待决['requiresApproval'] and 最近['status']=='client-pending'
                ))
            ):
                return {'ok':False,'message':f'运行请求 "{请求标识}" 已不再对应该 {插件标识} 的最近一次运行'}
            尝试=最近
            if 待决['requiresApproval']:
                计划['plugin']['approvedClientPackages'].add(包标识)
                if 批准后续版本:
                    计划['plugin']['clientVersionUpdatesApproved']=True
        else:
            待决标识=自身._注册表.待决请求(插件标识)
            if 待决标识 is not None:
                return {'ok':False,'message':f'动态插件 "{插件标识}" 有待决运行请求 {待决标识}'}
            运行=计划['plugin']['run'] if 'run' in 计划['plugin'] else None
            最近=计划['plugin']['latestRun'] if 'latestRun' in 计划['plugin'] else None
            if 运行 is not None and 运行['packageId']==包标识 and 最近 is not None and 最近['pluginRunId']==运行['pluginRunId']:
                尝试=最近
            else:
                尝试=自身._创建尝试(计划)
                计划['plugin']['nextPackageId']=包标识
                计划['plugin']['latestRun']=尝试
            if 'clientCode' in 计划['definition']:
                计划['plugin']['approvedClientPackages'].add(包标识)
        运行=计划['plugin']['run'] if 'run' in 计划['plugin'] else None
        附着=运行 is not None and 尝试['pluginRunId']==运行['pluginRunId']
        if not 附着:
            尝试['status']='starting-host'
            if 尝试['host']['status']!='absent':
                尝试['host']={'status':'pending','waitingFor':[]}
        已启动=自身._激活(计划,请求标识,附着,尝试)
        if not 已启动['ok']:
            自身._失败尝试(计划['plugin'],尝试,'host-load',已启动)
        return 已启动

    @_远程('getClientCode')
    def 获取客户端代码(自身,智能体,插件标识,运行标识):
        """读取精确活动运行的客户端源码。"""
        插件=自身._属下(智能体,插件标识)
        if 插件 is None:
            raise 宿主运行器错误(缺席插件消息(插件标识))
        if 'run' not in 插件 or 插件['run']['pluginRunId']!=运行标识:
            raise 宿主运行器错误(f'动态插件 "{插件标识}" 没有在运行激活 "{运行标识}"')
        运行=插件['run']
        定义=插件['packages'].get(运行['packageId'])
        if 定义 is None or 'clientCode' not in 定义:
            raise 宿主运行器错误(f'包 "{运行["packageId"]}" 没有客户端半')
        return {
            'code':定义['clientCode'],
            'name':定义['name'],
            'pluginId':插件标识,
            'packageId':运行['packageId'],
            'pluginRunId':运行标识,
        }

    @_远程('resolveRequestRun')
    def 结算请求运行(自身,请求标识,决议):
        """结算一次模型驱动的客户端激活请求。"""
        待决=自身._注册表.窥视请求(请求标识)
        if 待决 is None:
            return {'accepted':False}
        插件=自身._注册表.获取(待决['pluginId'])
        运行=插件['run'] if 插件 is not None and 'run' in 插件 else None
        if 决议['ok'] and (运行 is None or 运行['pluginRunId']!=决议['pluginRunId']):
            return {'accepted':False}
        if (
            not 决议['ok']
            and 'pluginRunId' in 决议
            and (运行 is None or 运行['pluginRunId']!=决议['pluginRunId'])
        ):
            return {'accepted':False}
        自身._注册表.认领请求(请求标识)
        已结算=自身._结算激活(插件,决议,请求标识)
        自身._宣布已结算(请求标识,决议,None if 待决['requiresApproval'] else 'completed')
        自身._转向运行结局(待决,已结算)
        return {'accepted':True}

    @_远程('settleUserRun')
    def 落定用户运行(自身,智能体,插件标识,决议):
        """面板运行在本页加载或失败客户端半之后落定。"""
        插件=自身._属下(智能体,插件标识)
        if 插件 is None:
            return {'ok':False,'reason':'plugin-missing','message':缺席插件消息(插件标识)}
        已结算=自身._结算激活(插件,决议)
        自身._注入用户运行结局(智能体,插件标识,已结算)
        return 已结算

    def 停止(自身,智能体,插件标识):
        """停止活动运行，保留全部包版本。"""
        插件=自身._属下(智能体,插件标识)
        if 插件 is None:
            return {'ok':False,'reason':'plugin-missing','message':缺席插件消息(插件标识)}
        待决=自身._注册表.待决请求(插件标识)
        if 'run' not in 插件 and 待决 is None:
            return {'ok':False,'reason':'not-running','message':f'动态插件 "{插件标识}" 未在运行'}
        if 待决 is not None:
            自身._取消待决(插件标识,f'动态插件 "{插件标识}" 在审批前被停止')
        if 'run' in 插件:
            自身._撤回(插件)
        if 'latestRun' in 插件:
            插件['latestRun']['status']='stopped'
            if 插件['latestRun']['host']['status']!='absent':
                插件['latestRun']['host']={'status':'stopped','waitingFor':[]}
            if 插件['latestRun']['client']['status']!='absent':
                插件['latestRun']['client']={'status':'stopped','waitingFor':[]}
        return {'ok':True}

    @_远程('stopFromPanel')
    def 从面板停止(自身,智能体,插件标识):
        """面板停止插件，并把状态变化注入模型下一步。"""
        结果=自身.停止(智能体,插件标识)
        if not 结果['ok']:
            return 结果
        插件=自身._属下(智能体,插件标识)
        当前=插件['currentPackageId'] if 插件 is not None and 'currentPackageId' in 插件 else 'none'
        自身._注入用户上下文(
            智能体,
            f'用户停止了 Cordis 插件 {插件标识}。其包定义仍在；currentPackageId 是 {当前}。',
        )
        return 结果

    @_远程('syncInspectManifest')
    def 同步巡检清单(自身,提供方列表):
        """替换客户端巡检提供方目录的宿主镜像。"""
        自身._巡检.同步客户端清单(提供方列表)
        return None

    @_远程('resolveInspectQuery')
    def 结算巡检查询(自身,智能体,请求标识,决议):
        """用现场结果认领一次待决客户端巡检查询。"""
        return 自身._巡检.结算客户端查询(智能体,请求标识,决议)

    @_远程('inventory')
    def 盘点(自身):
        """全进程存货，一行一个稳定插件。"""
        行列表=[]
        for 插件 in 自身._注册表.全部():
            行={
                'pluginId':插件['pluginId'],
                'agentId':插件['sessionId'],
                'packages':[{
                    'packageId':定义['packageId'],
                    'name':定义['name'],
                    'purpose':定义['purpose'],
                    'hasHostHalf':'hostCode' in 定义,
                    'hasClientHalf':'clientCode' in 定义,
                } for 定义 in 插件['packages'].values()],
            }
            if 'currentPackageId' in 插件:
                行['currentPackageId']=插件['currentPackageId']
            if 'nextPackageId' in 插件:
                行['nextPackageId']=插件['nextPackageId']
            if 'run' in 插件:
                行['activeRun']={
                    'pluginRunId':插件['run']['pluginRunId'],
                    'packageId':插件['run']['packageId'],
                }
            if 'latestRun' in 插件:
                行['latestRun']=克隆尝试(插件['latestRun'])
            行列表.append(行)
        return 行列表

    def 快照(自身,智能体):
        """读一个会话的宿主侧状态，供巡检与结果渲染。"""
        行列表=[]
        for 插件 in 自身._注册表.会话下(智能体.id):
            行={
                'pluginId':插件['pluginId'],
                'packages':[{
                    'packageId':定义['packageId'],
                    'name':定义['name'],
                    'purpose':定义['purpose'],
                    'hasHostHalf':'hostCode' in 定义,
                    'hasClientHalf':'clientCode' in 定义,
                } for 定义 in 插件['packages'].values()],
            }
            if 'currentPackageId' in 插件:
                行['currentPackageId']=插件['currentPackageId']
            if 'nextPackageId' in 插件:
                行['nextPackageId']=插件['nextPackageId']
            if 'run' in 插件:
                活动={
                    'pluginRunId':插件['run']['pluginRunId'],
                    'packageId':插件['run']['packageId'],
                    'handlers':list(插件['run']['handlers']),
                }
                if 'fiber' in 插件['run']:
                    活动['fiber']=插件['run']['fiber']
                if 'renderFailure' in 插件['run']:
                    活动['renderFailure']=插件['run']['renderFailure']
                行['activeRun']=活动
            if 'latestRun' in 插件:
                行['latestRun']=克隆尝试(插件['latestRun'])
            行列表.append(行)
        return 行列表

    def 引用(自身,智能体,插件标识):
        """显式 `@pluginId` 手势的无源码上下文。"""
        插件=自身._属下(智能体,插件标识)
        if 插件 is None:
            return None
        if 'nextPackageId' in 插件:
            包标识=插件['nextPackageId']
        elif 'currentPackageId' in 插件:
            包标识=插件['currentPackageId']
        else:
            键列表=list(插件['packages'])
            包标识=键列表[-1] if len(键列表)>0 else None
        if 包标识 is None:
            return None
        定义=插件['packages'].get(包标识)
        if 定义 is None:
            return None
        出={
            'pluginId':插件标识,
            'packageId':包标识,
            'name':定义['name'],
            'purpose':定义['purpose'],
        }
        if 'currentPackageId' in 插件:
            出['currentPackageId']=插件['currentPackageId']
        if 'nextPackageId' in 插件:
            出['nextPackageId']=插件['nextPackageId']
        if 'run' in 插件:
            出['activeRun']={
                'pluginRunId':插件['run']['pluginRunId'],
                'packageId':插件['run']['packageId'],
            }
        if 'latestRun' in 插件:
            出['latestRun']=克隆尝试(插件['latestRun'])
        return 出

    def 列出插件(自身,智能体):
        """一个会话拥有的无源码插件摘要，按创建顺序。"""
        return [自身.检视插件(智能体,插件['pluginId']) for 插件 in 自身._注册表.会话下(智能体.id)]

    def 检视插件(自身,智能体,插件标识):
        """检视一个插件，不返回包源码。"""
        插件=自身._属下(智能体,插件标识)
        if 插件 is None:
            raise 宿主运行器错误(缺席插件消息(插件标识))
        引用=自身.引用(智能体,插件标识)
        if 引用 is None:
            raise 宿主运行器错误(f'动态插件 "{插件标识}" 没有包')
        return {
            **引用,
            'packages':[{
                'packageId':定义['packageId'],
                'name':定义['name'],
                'purpose':定义['purpose'],
                'hasHostHalf':'hostCode' in 定义,
                'hasClientHalf':'clientCode' in 定义,
            } for 定义 in 插件['packages'].values()],
        }

    def 检视包(自身,智能体,插件标识,包标识):
        """读取一个不可变包及其宿主/客户端源码。"""
        插件=自身._属下(智能体,插件标识)
        if 插件 is None:
            raise 宿主运行器错误(缺席插件消息(插件标识))
        定义=插件['packages'].get(包标识)
        if 定义 is None:
            raise 宿主运行器错误(f'动态包 "{包标识}" 在插件 "{插件标识}" 上不存在')
        代码={}
        if 'hostCode' in 定义:
            代码['host']=定义['hostCode']
        if 'clientCode' in 定义:
            代码['client']=定义['clientCode']
        出={
            'pluginId':插件标识,
            'packageId':包标识,
            'name':定义['name'],
            'purpose':定义['purpose'],
            'code':代码,
        }
        if 'currentPackageId' in 插件:
            出['currentPackageId']=插件['currentPackageId']
        if 'nextPackageId' in 插件:
            出['nextPackageId']=插件['nextPackageId']
        if 'run' in 插件:
            出['activeRun']={
                'pluginRunId':插件['run']['pluginRunId'],
                'packageId':插件['run']['packageId'],
            }
        if 'latestRun' in 插件:
            出['latestRun']=克隆尝试(插件['latestRun'])
        return 出

    @_远程('reportRenderFailure')
    def 报告渲染失败(自身,智能体,插件标识,运行标识,失败):
        """记录精确活动运行的加载后渲染失败。"""
        插件=自身._属下(智能体,插件标识)
        if 插件 is not None and 'run' in 插件 and 插件['run']['pluginRunId']==运行标识:
            运行=插件['run']
            定义=插件['packages'].get(插件['run']['packageId'])
            应当转向='renderFailure' not in 运行
            运行['renderFailure']=失败
            尝试=插件['latestRun'] if 'latestRun' in 插件 else None
            if 尝试 is not None and 尝试['pluginRunId']==运行标识:
                尝试['error']=自身._诊断(插件,尝试,'client-render',失败)
                尝试['client']={
                    'status':'failed',
                    'waitingFor':尝试['client']['waitingFor'],
                    'error':失败['message'],
                }
                尝试['status']='failed'
            if 定义 is not None and 应当转向:
                自身._转向渲染失败(智能体,插件,定义,运行标识,失败)
        return None

    @_远程('reportClientGuardFailure')
    def 报告客户端门面失败(自身,智能体,插件标识,运行标识,失败):
        """报告包完成激活后的客户端门面拒绝。"""
        插件=自身._属下(智能体,插件标识)
        if 插件 is not None and 'run' in 插件 and 插件['run']['pluginRunId']==运行标识:
            自身._转向门面失败(插件,插件['run'],'Client',失败)
        return None

    @_远程('invoke')
    def 调用(自身,插件标识,运行标识,方法,参数):
        """调用活动宿主方法，拒绝陈旧客户端运行。"""
        插件=自身._注册表.获取(插件标识)
        if 插件 is None or 'run' not in 插件:
            return {'ok':False,'code':'plugin-not-running','message':f'动态插件 "{插件标识}" 未在运行'}
        运行=插件['run']
        if 运行['pluginRunId']!=运行标识:
            return {'ok':False,'code':'stale-run','message':f'激活 "{运行标识}" 已不再活动'}
        处理=运行['handlers'].get(方法)
        if 处理 is None:
            return {
                'ok':False,
                'code':'method-not-found',
                'message':f'动态插件 "{插件标识}" 没有登记宿主方法 "{方法}"',
            }
        try:
            return {'ok':True,'value':处理(参数)}
        except BaseException as 错误:
            失败=错误详情(错误)
            自身._转向宿主处理失败(插件,运行,方法,失败)
            return {'ok':False,'code':'handler-error',**失败}

    def _解析计划(自身,智能体,插件标识,包标识,模式,允许附着=False):
        """解析一次激活目标，或给出可操作拒绝。"""
        插件=自身._属下(智能体,插件标识)
        if 插件 is None:
            return {
                'ok':False,
                'response':{'ok':False,'reason':'plugin-missing','message':缺席插件消息(插件标识)},
            }
        定义=插件['packages'].get(包标识)
        if 定义 is None:
            return {
                'ok':False,
                'response':{
                    'ok':False,
                    'reason':'package-missing',
                    'message':f'插件 "{插件标识}" 没有包 "{包标识}"',
                },
            }
        当前=插件['currentPackageId'] if 'currentPackageId' in 插件 else None
        if 模式=='update' and (当前 is None or 当前==包标识):
            if 当前 is None:
                消息=f'插件 "{插件标识}" 还没有成功版本；请用 mode "run" 启动 "{包标识}"'
            else:
                消息=f'包 "{包标识}" 已是当前版本；请用 mode "run"'
            return {'ok':False,'response':{'ok':False,'reason':'invalid-mode','message':消息}}
        if 模式=='run' and 当前 is not None and 当前!=包标识:
            return {
                'ok':False,
                'response':{
                    'ok':False,
                    'reason':'invalid-mode',
                    'message':f'包 "{包标识}" 与当前 "{当前}" 不同；请用 mode "update"',
                },
            }
        if not 允许附着 and 插件标识 in 自身._启动中:
            return {
                'ok':False,
                'response':{
                    'ok':False,
                    'reason':'transition-in-flight',
                    'message':f'插件 "{插件标识}" 已在启动',
                },
            }
        return {'ok':True,'plugin':插件,'definition':定义,'mode':模式}

    def _激活(自身,计划,请求标识,允许附着,尝试):
        """同一插件的在途启动共用一个操作任务。"""
        插件标识=计划['plugin']['pluginId']
        在途=自身._启动中.get(插件标识)
        if 在途 is not None:
            return 在途.等待()
        任务=操作任务()
        自身._启动中[插件标识]=任务
        try:
            结果=自身._新启(计划,请求标识,允许附着,尝试)
            任务.兑现(结果)
            return 结果
        except BaseException as 错误:
            任务.拒绝(错误)
            raise
        finally:
            自身._启动中.pop(插件标识,None)

    def _新启(自身,计划,请求标识,允许附着,尝试):
        """撤回旧运行并启动新的宿主半。"""
        插件=计划['plugin']
        定义=计划['definition']
        模式=计划['mode']
        运行=插件['run'] if 'run' in 插件 else None
        if (
            允许附着
            and 运行 is not None
            and 运行['packageId']==定义['packageId']
            and 运行['pluginRunId']==尝试['pluginRunId']
        ):
            return {
                'ok':True,
                'pluginId':插件['pluginId'],
                'packageId':定义['packageId'],
                'pluginRunId':运行['pluginRunId'],
                'waitingFor':缺席于(自身.ctx,运行),
                'startedHere':False,
            }
        if 'run' in 插件:
            自身._撤回(插件)
        if 模式=='update' or 'currentPackageId' not in 插件:
            插件['nextPackageId']=定义['packageId']
        运行={
            'pluginRunId':尝试['pluginRunId'],
            'packageId':定义['packageId'],
            'handlers':{},
            'handlerDisposers':[],
            'reportedRuntimeErrors':set(),
        }
        if 请求标识 is not None:
            运行['startedForRequest']=请求标识
        if 'hostCode' in 定义:
            失败=自身._启动宿主(插件,定义['hostCode'],运行)
            if 失败 is not None:
                return {'ok':False,**失败}
        插件['run']=运行
        自身.ctx.广播('cordis/dynamic-package',{
            'pluginId':插件['pluginId'],
            'packageId':定义['packageId'],
            'pluginRunId':运行['pluginRunId'],
            'name':定义['name'],
        })
        缺席=缺席于(自身.ctx,运行)
        if 'fiber' not in 运行:
            宿主状态='absent'
        elif len(缺席)==0:
            宿主状态='running'
        else:
            宿主状态='waiting'
        尝试['host']={'status':宿主状态,'waitingFor':缺席}
        if 'clientCode' not in 定义:
            自身._提交激活(插件,运行)
        else:
            尝试['status']='client-pending'
            尝试['client']={'status':'pending','waitingFor':[]}
        return {
            'ok':True,
            'pluginId':插件['pluginId'],
            'packageId':定义['packageId'],
            'pluginRunId':运行['pluginRunId'],
            'waitingFor':缺席,
            'startedHere':True,
        }

    def _启动宿主(自身,插件,宿主码,运行):
        """求值宿主半并挂到动态组下。"""
        def 处理(方法,函数):
            """登记 harness.handle。"""
            规范化=规范化处理函数(方法,函数)
            运行['handlers'][规范化['method']]=规范化['handler']
            def 拆除():
                """只摘掉仍是本条的处理函数。"""
                if 运行['handlers'].get(规范化['method']) is 规范化['handler']:
                    运行['handlers'].pop(规范化['method'],None)
            运行['handlerDisposers'].append(拆除)
            return 拆除
        try:
            沙箱=创建沙箱(插件['pluginId'],{'handle':处理})
            求值=求值宿主代码(沙箱,宿主码,插件['pluginId'],自身._超时毫秒)
            if not 是否插件(求值):
                if 求值 is None:
                    raise 宿主运行器错误('宿主半返回了 `undefined` —— 是不是忘了 `return`？')
                raise 宿主运行器错误('宿主半必须返回插件函数，或带 apply(ctx) 的对象')
            def 报告门面失败(错误):
                """激活后门面拒绝。"""
                自身._转向门面失败(插件,运行,'Host',错误详情(错误))
            运行['fiber']=启动宿主半(自身._需要组(),求值,报告门面失败)
            return None
        except BaseException as 错误:
            for 拆除 in 运行['handlerDisposers'][:]:
                拆除()
            运行['handlerDisposers'].clear()
            return 错误详情(错误)

    def _结算激活(自身,插件,决议,请求标识=None):
        """按客户端决议提交或回退一次激活。"""
        if 插件 is None:
            return {'ok':False,'reason':'plugin-missing','message':'动态插件在激活期间被移除'}
        尝试=插件['latestRun'] if 'latestRun' in 插件 else None
        if not 决议['ok']:
            if 决议['reason']=='rejected':
                消息=决议['message'] if 'message' in 决议 else '运行请求被拒绝'
                if 尝试 is not None:
                    尝试['status']='rejected'
                    尝试['error']=自身._诊断(插件,尝试,'approval',消息)
                    尝试['client']={'status':'stopped','waitingFor':[]}
                return {'ok':False,'reason':'rejected','message':消息}
            运行=插件['run'] if 'run' in 插件 else None
            拥有运行=(
                运行 is not None
                and 决议.get('pluginRunId')==运行['pluginRunId']
                and (请求标识 is None or 运行.get('startedForRequest')==请求标识)
                and 决议.get('startedHere') is not False
            )
            if 拥有运行:
                自身._撤回(插件)
            if 尝试 is not None and ('pluginRunId' not in 决议 or 尝试['pluginRunId']==决议['pluginRunId']):
                阶段='host-apply' if 决议['reason']=='host-half-failed' else 'client-apply'
                失败={'message':决议['message'] if 'message' in 决议 else 决议['reason']}
                if 'stack' in 决议:
                    失败['stack']=决议['stack']
                自身._失败尝试(插件,尝试,阶段,失败)
            出={
                'ok':False,
                'reason':决议['reason'],
                'message':决议['message'] if 'message' in 决议 else 决议['reason'],
            }
            if 'stack' in 决议:
                出['stack']=决议['stack']
            return 出
        运行=插件['run'] if 'run' in 插件 else None
        if 运行 is None or 运行['pluginRunId']!=决议['pluginRunId']:
            return {'ok':False,'reason':'client-half-failed','message':f'激活 "{决议["pluginRunId"]}" 已不再活动'}
        if 尝试 is not None and 尝试['pluginRunId']==运行['pluginRunId']:
            等待=决议['waitingFor'] if 'waitingFor' in 决议 else []
            尝试['client']={
                'status':'running' if len(等待)==0 else 'waiting',
                'waitingFor':等待,
            }
        自身._提交激活(插件,运行)
        出=自身._运行回执(插件,{
            'ok':True,
            'pluginId':插件['pluginId'],
            'packageId':运行['packageId'],
            'pluginRunId':运行['pluginRunId'],
            'waitingFor':缺席于(自身.ctx,运行),
            'startedHere':False,
        })
        if 'waitingFor' in 决议:
            出['clientWaitingFor']=决议['waitingFor']
        return 出

    def _提交激活(自身,插件,运行):
        """把成功激活写成当前包。"""
        插件['currentPackageId']=运行['packageId']
        插件.pop('nextPackageId',None)
        运行.pop('startedForRequest',None)
        尝试=插件['latestRun'] if 'latestRun' in 插件 else None
        if 尝试 is not None and 尝试['pluginRunId']==运行['pluginRunId']:
            if 尝试['host']['status']=='waiting' or 尝试['client']['status']=='waiting':
                尝试['status']='waiting'
            else:
                尝试['status']='running'
            尝试.pop('approvalRequestId',None)
            尝试.pop('requiresApproval',None)
            尝试.pop('error',None)

    def _运行回执(自身,插件,已启动):
        """成功激活的模型回执。"""
        模式='run'
        if 'latestRun' in 插件 and 插件['latestRun']['pluginRunId']==已启动['pluginRunId']:
            模式=插件['latestRun']['mode']
        return {
            'ok':True,
            'status':'running',
            'pluginId':插件['pluginId'],
            'packageId':已启动['packageId'],
            'pluginRunId':已启动['pluginRunId'],
            'waitingFor':已启动['waitingFor'],
            'currentPackageId':已启动['packageId'],
            'mode':模式,
        }

    def _宣布已结算(自身,请求标识,决议,覆盖=None):
        """广播请求已离开可作答状态。"""
        if 覆盖 is not None:
            结局=覆盖
        elif 决议['ok']:
            结局='approved'
        elif 决议['reason']=='rejected':
            结局='rejected'
        else:
            结局='failed'
        自身.ctx.广播('cordis/request-run-resolved',{'requestId':请求标识,'outcome':结局})

    def _转向运行结局(自身,待决,已结算):
        """把运行结局转向所属会话。"""
        智能体表=自身._根上下文.获取服务('agents',False)
        if 智能体表 is None:
            return
        智能体=智能体表.获取(待决['agentId'])
        if 智能体 is None:
            return
        插件=自身._注册表.获取(待决['pluginId'])
        身份=f"{待决['pluginId']}/{待决['packageId']} ({待决['pluginRunId']})"
        if 已结算['ok']:
            当前=已结算['currentPackageId'] if 'currentPackageId' in 已结算 else 待决['packageId']
            文本=(
                f"Cordis {待决['mode']} {身份} 已成功完成。"
                f'currentPackageId 是 {当前}。请继续使用正在运行的插件。'
            )
        elif 已结算['reason']=='rejected':
            文本=(
                f"用户拒绝了 Cordis {待决['mode']} {身份}。"
                '除非用户要求，不要再次请求同一激活。'
            )
        else:
            已返回='awaiting-approval' if 待决['requiresApproval'] else 'starting'
            当前=插件['currentPackageId'] if 插件 is not None and 'currentPackageId' in 插件 else 'none'
            下一=插件['nextPackageId'] if 插件 is not None and 'nextPackageId' in 插件 else 待决['packageId']
            文本=(
                f"Cordis {待决['mode']} {身份} 在运行器返回 {已返回} 之后失败："
                f"{已结算['reason']}\n{格式化错误详情(已结算)}\n"
                f'currentPackageId: {当前}\n'
                f'nextPackageId: {下一}\n'
                '请把失败告知用户；定义可通过 Cordis 面板管理。'
            )
        智能体.转向(创建用户消息({
            'content':[{'type':'text','text':文本}],
            'source':{'kind':'cordis-host-runner'},
        }))

    def _转向渲染失败(自身,智能体,插件,定义,运行标识,失败):
        """把客户端渲染失败转向所属会话。"""
        智能体.转向(创建用户消息({
            'content':[{
                'type':'text',
                'text':(
                    f"Cordis 客户端 UI {插件['pluginId']}/{定义['packageId']} ({运行标识}) "
                    f"在激活后渲染槽 \"{失败['slot']}\" 时失败。\n"
                    f'{格式化错误详情(失败)}\n'
                    f"entryAbdicated: {失败['abdicated']}\n"
                    '请把客户端渲染失败告知用户；定义可通过 Cordis 面板停止。'
                ),
            }],
            'source':{'kind':'cordis-host-runner'},
        }))

    def _转向宿主处理失败(自身,插件,运行,方法,失败):
        """把宿主 handler 失败转向所属会话。"""
        键='Host\u0000handler\u0000'+方法+'\u0000'+失败['message']
        if not 自身._认领运行时失败(插件,运行,键):
            return
        智能体表=自身._根上下文.获取服务('agents',False)
        if 智能体表 is None:
            return
        智能体=智能体表.获取(插件['sessionId'])
        if 智能体 is None:
            return
        方法文=json.dumps(方法,ensure_ascii=False,separators=(',',':'),allow_nan=False)
        智能体.转向(创建用户消息({
            'content':[{
                'type':'text',
                'text':(
                    f"Cordis 宿主处理函数 {插件['pluginId']}/{运行['packageId']} ({运行['pluginRunId']}) "
                    f'在客户端调用 host.call({方法文}) 时失败。\n'
                    f'{格式化错误详情(失败)}\n'
                    '插件仍在运行。请把宿主处理失败告知用户。若处理函数需要某服务，'
                    '请在返回的插件 inject 列表里声明，或用 ctx.获取服务(name) 读取并处理缺席。'
                ),
            }],
            'source':{'kind':'cordis-host-runner'},
        }))

    def _转向门面失败(自身,插件,运行,平面,失败):
        """把激活后门面拒绝转向所属会话。"""
        键=平面+'\u0000guard\u0000'+失败['message']
        if not 自身._认领运行时失败(插件,运行,键):
            return
        智能体表=自身._根上下文.获取服务('agents',False)
        if 智能体表 is None:
            return
        智能体=智能体表.获取(插件['sessionId'])
        if 智能体 is None:
            return
        智能体.转向(创建用户消息({
            'content':[{
                'type':'text',
                'text':(
                    f"Cordis {平面} 门面在激活后拒绝了 {插件['pluginId']}/{运行['packageId']} "
                    f"({运行['pluginRunId']}) 的运行时代码。\n{格式化错误详情(失败)}\n"
                    '插件仍在运行。请把门面拒绝告知用户；可通过 Cordis 面板停止。'
                ),
            }],
            'source':{'kind':'cordis-host-runner'},
        }))

    def _认领运行时失败(自身,插件,运行,键):
        """同一激活同一失败只转向一次。"""
        尝试=插件['latestRun'] if 'latestRun' in 插件 else None
        if (
            'run' not in 插件 or 插件['run'] is not 运行
            or 尝试 is None
            or 尝试['pluginRunId']!=运行['pluginRunId']
            or (尝试['status']!='running' and 尝试['status']!='waiting')
        ):
            return False
        if 键 in 运行['reportedRuntimeErrors']:
            return False
        运行['reportedRuntimeErrors'].add(键)
        return True

    def _注入用户运行结局(自身,智能体,插件标识,已结算):
        """把面板运行结局注入下一步。"""
        插件=自身._属下(智能体,插件标识)
        if 已结算['ok']:
            文本=(
                f"用户手动运行了 Cordis 插件 {插件标识}，包 {已结算['packageId']}，"
                f"激活 {已结算['pluginRunId']}。激活成功；currentPackageId 是 {已结算['currentPackageId']}。"
            )
        else:
            尝试=插件['latestRun'] if 插件 is not None and 'latestRun' in 插件 else None
            片段=''
            if 尝试 is not None:
                片段=f"，包 {尝试['packageId']}，激活 {尝试['pluginRunId']}"
            当前=插件['currentPackageId'] if 插件 is not None and 'currentPackageId' in 插件 else 'none'
            下一=插件['nextPackageId'] if 插件 is not None and 'nextPackageId' in 插件 else 'none'
            文本=(
                f'用户手动运行了 Cordis 插件 {插件标识}{片段}，但失败了：'
                f"{已结算['reason']}\n{格式化错误详情(已结算)}\n"
                f'currentPackageId: {当前}\n'
                f'nextPackageId: {下一}'
            )
        自身._注入用户上下文(智能体,文本)

    def _注入用户上下文(自身,智能体,文本):
        """确认智能体仍在注册表后注入用户消息。"""
        智能体表=自身._根上下文.获取服务('agents',False)
        if 智能体表 is None:
            return
        if 智能体表.获取(智能体.id) is not 智能体:
            return
        智能体.注入(创建用户消息({
            'content':[{'type':'text','text':文本}],
            'source':{'kind':'cordis-host-runner'},
        }))

    def _取消待决(自身,插件标识,消息):
        """取消该插件上仍可作答的运行请求。"""
        请求标识=自身._注册表.待决请求(插件标识)
        if 请求标识 is None:
            return
        待决=自身._注册表.认领请求(请求标识)
        if 待决 is None:
            return
        插件=自身._注册表.获取(插件标识)
        if (
            插件 is not None
            and 'latestRun' in 插件
            and 插件['latestRun']['pluginRunId']==待决['pluginRunId']
        ):
            插件['latestRun']['status']='cancelled'
            插件['latestRun']['error']=自身._诊断(插件,插件['latestRun'],'approval',消息)
            插件['latestRun'].pop('approvalRequestId',None)
            插件['latestRun'].pop('requiresApproval',None)
        自身._宣布已结算(请求标识,{'ok':False,'reason':'rejected'},'cancelled')

    def _创建尝试(自身,计划):
        """铸造一次激活尝试。"""
        return {
            'pluginRunId':动态运行标识(自身._注册表.铸造运行标识()),
            'packageId':计划['definition']['packageId'],
            'mode':计划['mode'],
            'status':'starting-host',
            'host':{
                'status':'absent' if 'hostCode' not in 计划['definition'] else 'pending',
                'waitingFor':[],
            },
            'client':{
                'status':'absent' if 'clientCode' not in 计划['definition'] else 'pending',
                'waitingFor':[],
            },
        }

    def _失败尝试(自身,插件,尝试,阶段,失败):
        """把尝试标为失败并写下诊断。"""
        尝试['status']='failed'
        尝试['error']=自身._诊断(插件,尝试,阶段,失败)
        if 阶段.startswith('host'):
            尝试['host']={'status':'failed','waitingFor':[],'error':失败['message']}
        else:
            尝试['client']={'status':'failed','waitingFor':[],'error':失败['message']}

    def _诊断(自身,插件,尝试,阶段,失败):
        """结构化失败诊断。"""
        详情={'message':失败} if isinstance(失败,str) else 失败
        return {
            'phase':阶段,
            **详情,
            'pluginId':插件['pluginId'],
            'packageId':尝试['packageId'],
            'pluginRunId':尝试['pluginRunId'],
        }

    def _撤回(自身,插件):
        """拆除活动运行的处理函数与纤程。"""
        if 'run' not in 插件:
            return
        运行=插件.pop('run')
        for 拆除 in 运行['handlerDisposers'][:]:
            拆除()
        运行['handlerDisposers'].clear()
        if 'fiber' in 运行:
            运行['fiber'].拆除()
            运行['fiber'].等待()
        自身.ctx.广播('cordis/dynamic-retract',{
            'pluginId':插件['pluginId'],
            'packageId':运行['packageId'],
            'pluginRunId':运行['pluginRunId'],
        })

    def _属下(自身,智能体,插件标识):
        """仅当会话拥有该插件时返回记录。"""
        插件=自身._注册表.获取(插件标识)
        if 插件 is None or 插件['sessionId']!=智能体.id:
            return None
        return 插件

    def _需要组(自身):
        """懒创建 cordis-dynamic 组纤程。"""
        if 自身._组 is None:
            自身._组=自身._根上下文.启动插件(应用动态组)
        return 自身._组

默认=动态cordis运行器
Config=配置
name=名称
inject=依赖
default=默认
动态cordis运行器.inject=依赖
动态cordis运行器.Config=配置
