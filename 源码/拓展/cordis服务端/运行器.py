"""动态 Cordis 插件服务：不可变包定义、每个插件一条活动运行、人工批准的客户端激活，以及宿主/客户端调用。

对齐上游 `拓展/cordis-host-runner/src/index.ts`。公开面仅中文名；Remote 导出名与事件名保持上游字面量。
"""
import re#前缀校验
from ...依赖 import cordis#外部依赖胶水
from ...依赖.schemastery import 整数字段#配置字段
from ...模型后端.llm import 创建用户消息#用户消息构造
from ...typert.协议 import 远程服务,远程#Remote 服务基类与装饰器
from .类型 import 动态插件标识,动态包标识,动态运行标识,审批请求标识#品牌构造
from .守卫 import 是否插件,归一处理器#插件判定与处理器归一
from .巡检注册表 import 巡检注册表服务#巡检注册表
from .生命周期 import 缺失服务,启动宿主半#缺失服务与宿主半启动
from .注册表 import 动态插件注册表#动态插件注册表
from .沙箱 import 创建沙箱,求值宿主代码,预检代码,宿主内置巡检#沙箱、求值、预检

__all__=[#仅中文公开名
    '动态插件运行器服务','巡检注册表服务','宿主内置巡检',
    '动态插件标识','动态包标识','动态运行标识','审批请求标识',
]#公开面结束

配置={#运行器配置
    'vmTimeoutMs':整数字段(最小=1,默认值=5000),#虚拟机超时，默认 5000ms
}#配置结束

前缀模式=re.compile(r'^[a-z]{3,6}$')#插件前缀 3–6 小写字母

def 解开(值):#承诺则等待
    """承诺则等待，否则原样。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待
    return 值#同步

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 插件缺失文案(标识):#插件缺失文案
    """可能已删或重启丢失。"""
    return 'no dynamic plugin "'+标识+'" in this process — it may have been removed or lost on DSH restart'#文案

def 错误细节(错误):#从未知抛出抽出细节
    """抽出消息与可选栈。"""
    if not isinstance(错误,BaseException):#非异常
        return {'message':str(错误)}#字符串化
    细节={'message':str(错误)}#消息
    栈=getattr(错误,'__traceback__',None)#栈
    if 栈 is not None:#有栈
        import traceback#栈格式化
        细节['stack']=''.join(traceback.format_exception(type(错误),错误,栈))#栈文本
    return 细节#细节

def 格式错误细节(失败):#把细节格式成文本
    """消息行加可选栈。"""
    文本='message: '+str(取字段(失败,'message'))#消息行
    栈=取字段(失败,'stack')#可选栈
    if 栈 is not None:#有栈
        文本+='\nstack:\n'+栈#附上
    return 文本#文本

def 克隆尝试(尝试):#浅克隆一次尝试供快照
    """克隆宿主/客户端等待列表与诊断。"""
    宿主=dict(尝试['host'])#宿主半
    宿主['waitingFor']=list(尝试['host']['waitingFor'])#等待列表
    客户端=dict(尝试['client'])#客户端半
    客户端['waitingFor']=list(尝试['client']['waitingFor'])#等待列表
    克隆={**尝试,'host':宿主,'client':客户端}#其余字段
    if 尝试.get('error') is not None:#有诊断
        克隆['error']=dict(尝试['error'])#克隆诊断
    return 克隆#克隆

def 仍缺(上下文,运行):#活动运行仍缺的服务名
    """无纤维则空。"""
    光纤=运行.get('fiber')#纤维
    return [] if 光纤 is None else 缺失服务(上下文,光纤)#缺失服务

class 动态插件运行器服务(远程服务):#动态运行器服务
    """动态插件注册表与宿主半生命周期。"""
    inject=['tools']#依赖 tools 服务
    注入=['tools']#中文别名
    Config=配置#配置模式
    配置=配置#中文别名

    def __init__(自身,上下文,配置值):#构造
        """在宿主组合下创建该服务。"""
        super().__init__(上下文,'dynamicCordisRunner')#登记远程服务名
        自身.根上下文=上下文#记下根上下文
        自身.已解析=配置值#配置已由模式填默认
        自身.注册表=动态插件注册表()#插件注册表
        自身.巡检注册表=巡检注册表服务(上下文)#新建巡检注册表
        自身.启动中={}#进行中的宿主半启动 pluginId → 承诺
        自身.组=None#动态插件纤维组

    def 定义(自身,请求):#定义或追加包
        """定义新插件的第一个包，或向已有插件追加一个包。"""
        名称=请求['name'].strip()#去掉名称两端空白
        用途=请求['purpose'].strip()#去掉用途两端空白
        if len(名称)==0:#名称为空
            raise Exception('cordis_define needs a non-empty `name`')#拒绝
        if len(用途)==0:#用途为空
            raise Exception('cordis_define needs a non-empty `purpose`')#拒绝
        代码=请求['code']#源码
        if 代码.get('host') is None and 代码.get('client') is None:#两侧都缺
            raise Exception('cordis_define needs `code.host`, `code.client`, or both')#至少要一侧
        if 代码.get('host') is not None:#有宿主源码
            预检代码(代码['host'],'code.host')#预检
        if 代码.get('client') is not None:#有客户端源码
            预检代码(代码['client'],'code.client')#预检
        插件选择=请求['plugin']#新建或已有
        if 插件选择['kind']=='new':#新建插件
            前缀=插件选择['idPrefix'].strip()#去掉前缀空白
            if 前缀模式.match(前缀) is None:#前缀非法
                raise Exception('cordis_define `plugin.idPrefix` must contain 3–6 lowercase English letters')#拒绝
            插件标识=动态插件标识(自身.注册表.铸造插件标识(前缀))#铸造并品牌化
            插件={#新插件记录
                'pluginId':插件标识,#插件 id
                'sessionId':请求['sessionId'],#所属会话
                'packages':{},#空包表——用 dict 保序
                'approvedClientPackages':set(),#已批准的客户端包
                'clientVersionUpdatesApproved':False,#尚未批准后续版本
            }#新插件
            自身.注册表.加入(插件)#登记
        else:#已有插件
            找到=自身.注册表.获取(插件选择['pluginId'])#按 id 查找
            if 找到 is None or 找到['sessionId']!=请求['sessionId']:#不存在或不属于本会话
                raise Exception(插件缺失文案(插件选择['pluginId']))#报缺失
            插件=找到#沿用
        包标识=动态包标识(自身.注册表.铸造包标识())#铸造包 id
        定义记录={'packageId':包标识,'name':名称,'purpose':用途}#不可变包定义
        if 代码.get('host') is not None:#有宿主源码
            定义记录['hostCode']=代码['host']#写入
        if 代码.get('client') is not None:#有客户端源码
            定义记录['clientCode']=代码['client']#写入
        插件['packages'][包标识]=定义记录#挂到插件
        return {#定义回执
            'pluginId':插件['pluginId'],#插件 id
            'packageId':包标识,#包 id
            'name':名称,#名称
            'purpose':用途,#用途
            'hasHostHalf':定义记录.get('hostCode') is not None,#是否有宿主半
            'hasClientHalf':定义记录.get('clientCode') is not None,#是否有客户端半
        }#回执

    def 取消定义(自身,智能体,插件标识):#取消定义
        """移除一个插件、其活动运行，以及全部不可变包。"""
        插件=自身.本会话插件(智能体,插件标识)#本会话拥有的插件
        if 插件 is None:#不存在
            return {'ok':False,'reason':'plugin-missing','message':插件缺失文案(插件标识)}#失败
        曾在跑=插件.get('run') is not None#移除前是否在跑
        自身.取消挂起(插件标识,'dynamic plugin "'+插件标识+'" was removed before approval')#取消挂起审批
        if 插件.get('run') is not None:#有活动运行
            自身.收回(插件)#收回
        自身.注册表.删除(插件标识)#从注册表删掉
        return {'ok':True,'wasRunning':曾在跑}#成功回执

    @远程('undefineFromPanel')
    def 面板取消定义(自身,智能体,插件标识):#面板移除
        """从用户面板移除插件，并把状态变化排入模型下一步上下文。"""
        结果=自身.取消定义(智能体,插件标识)#走同一条移除路径
        if 结果.get('ok'):#移除成功才注入上下文
            自身.注入用户上下文(智能体,'The user removed Cordis Plugin '+插件标识+' and all of its Packages. The Plugin no longer exists.')#告知模型
        return 结果#原样返回

    def 运行(自身,智能体,插件标识,包标识,模式,信号=None):#启动或更新一个包
        """为一次模型工具调用启动或更新一个包。"""
        计划=自身.解析计划(智能体,插件标识,包标识,模式)#解析激活计划
        if not 计划.get('ok'):#计划失败
            return 计划['response']#原样拒绝
        if 信号 is not None and getattr(信号,'aborted',False):#请求已取消
            return {'ok':False,'reason':'cancelled','message':'the run request for dynamic plugin "'+插件标识+'" was cancelled before activation'}#取消
        if 自身.注册表.插件挂起请求(插件标识) is not None:#已有挂起运行请求
            return {'ok':False,'reason':'transition-in-flight','message':'dynamic plugin "'+插件标识+'" already has a pending run request'}#转换进行中
        尝试=自身.新建尝试(计划)#新建运行尝试
        计划['plugin']['nextPackageId']=包标识#记下即将激活的包
        计划['plugin']['latestRun']=尝试#记下最近尝试
        if 计划['definition'].get('clientCode') is None:#没有客户端半
            已启=自身.激活(计划,None,False,尝试)#启动宿主半
            if 已启.get('ok'):#成功
                return 自身.运行响应(计划['plugin'],已启)#拼运行响应
            自身.失败尝试(计划['plugin'],尝试,'host-load',已启)#标记宿主加载失败
            return {**已启,'reason':'host-half-failed'}#带失败原因
        请求标识=审批请求标识(自身.注册表.铸造审批标识())#铸造审批请求 id
        需要审批=(not 计划['plugin']['clientVersionUpdatesApproved']) and (包标识 not in 计划['plugin']['approvedClientPackages'])#是否需批
        尝试['approvalRequestId']=请求标识#挂上审批请求
        尝试['requiresApproval']=需要审批#是否需要审批
        尝试['status']='awaiting-approval' if 需要审批 else 'starting-host'#待批或直接启宿主
        自身.注册表.武装请求(请求标识,{#武装挂起请求
            'agentId':智能体.id,#智能体 id
            'pluginId':插件标识,#插件 id
            'packageId':包标识,#包 id
            'pluginRunId':尝试['pluginRunId'],#运行 id
            'mode':模式,#运行模式
            'requiresApproval':需要审批,#是否需批
        })#武装结束
        自身.ctx.emit('cordis/request-run',{#发出运行请求事件
            'requestId':请求标识,#请求 id
            'agentId':智能体.id,#智能体 id
            'pluginId':插件标识,#插件 id
            'packageId':包标识,#包 id
            'mode':模式,#运行模式
            'name':计划['definition']['name'],#包名
            'purpose':计划['definition']['purpose'],#用途
            'requiresApproval':需要审批,#是否需批
        })#emit结束
        回执={#挂起或启动中的成功形
            'ok':True,#已受理
            'status':'awaiting-approval' if 需要审批 else 'starting',#待批或启动中
            'pluginId':插件标识,#插件 id
            'packageId':包标识,#包 id
            'pluginRunId':尝试['pluginRunId'],#运行 id
            'mode':模式,#运行模式
            'waitingFor':[],#尚无等待的服务
            'nextPackageId':包标识,#下一包
        }#回执
        if 计划['plugin'].get('currentPackageId') is not None:#有当前包
            回执['currentPackageId']=计划['plugin']['currentPackageId']#带上
        return 回执#受理回执

    @远程('runHostHalf')
    def 运行宿主半(自身,智能体,插件标识,包标识,模式,请求标识,批准后续版本):#启动宿主半
        """为已批准的请求或直接的面板手势启动宿主代码。"""
        计划=自身.解析计划(智能体,插件标识,包标识,模式,请求标识 is None)#面板手势允许挂到活动运行
        if not 计划.get('ok'):#计划失败
            return {'ok':False,'message':计划['response']['message']}#失败
        if 请求标识 is not None:#模型驱动的请求
            挂起=自身.注册表.窥视请求(请求标识)#窥视挂起请求
            if 挂起 is None or 挂起['pluginId']!=插件标识 or 挂起['packageId']!=包标识 or 挂起['mode']!=模式:#对不上
                return {'ok':False,'message':'run request "'+请求标识+'" does not authorize '+插件标识+'/'+包标识}#未授权
            最近=计划['plugin'].get('latestRun')#最近尝试
            期望='awaiting-approval' if 挂起['requiresApproval'] else 'starting-host'#期望状态
            if 最近 is None or 最近['pluginRunId']!=挂起['pluginRunId'] or (最近['status']!=期望 and (挂起['requiresApproval'] or 最近['status']!='client-pending')):#状态不对
                return {'ok':False,'message':'run request "'+请求标识+'" no longer identifies the latest run of '+插件标识}#已不是最新
            尝试=最近#沿用
            if 挂起['requiresApproval']:#本次需要审批
                计划['plugin']['approvedClientPackages'].add(包标识)#记下本包已批准
                if 批准后续版本:#批准后续版本
                    计划['plugin']['clientVersionUpdatesApproved']=True#记下
        else:#直接面板手势
            挂起标识=自身.注册表.插件挂起请求(插件标识)#是否另有挂起
            if 挂起标识 is not None:#有挂起则拒绝
                return {'ok':False,'message':'dynamic plugin "'+插件标识+'" has pending run request '+挂起标识}#拒绝
            活动=计划['plugin'].get('run')#活动运行
            最近=计划['plugin'].get('latestRun')#最近尝试
            挂接=活动 is not None and 活动['packageId']==包标识 and 最近 is not None and 最近['pluginRunId']==活动['pluginRunId']#是否挂到已有
            尝试=最近 if 挂接 else 自身.新建尝试(计划)#沿用或新建
            if not 挂接:#新建尝试才改指针
                计划['plugin']['nextPackageId']=包标识#记下下一包
                计划['plugin']['latestRun']=尝试#记下最近尝试
            if 计划['definition'].get('clientCode') is not None:#有客户端半
                计划['plugin']['approvedClientPackages'].add(包标识)#视为已批准
        活动运行=计划['plugin'].get('run')#活动运行
        正在挂接=活动运行 is not None and 尝试['pluginRunId']==活动运行['pluginRunId']#是否挂到已有活动运行
        if not 正在挂接:#不是挂接则进入启宿主
            尝试['status']='starting-host'#状态改为启宿主
            if 尝试['host']['status']!='absent':#非缺席则重置
                尝试['host']={'status':'pending','waitingFor':[]}#待启动
        已启=自身.激活(计划,请求标识,正在挂接,尝试)#启动或挂接
        if not 已启.get('ok'):#失败
            自身.失败尝试(计划['plugin'],尝试,'host-load',已启)#记账
        return 已启#返回宿主半结果

    @远程('getClientCode')
    def 取客户端代码(自身,智能体,插件标识,运行标识):#取客户端源码
        """为精确的活动运行取回客户端代码。"""
        插件=自身.本会话插件(智能体,插件标识)#本会话拥有的插件
        if 插件 is None:#不存在
            raise Exception(插件缺失文案(插件标识))#不存在
        运行=插件.get('run')#活动运行
        if 运行 is None or 运行['pluginRunId']!=运行标识:#没有运行或不匹配
            raise Exception('dynamic plugin "'+插件标识+'" is not running activation "'+运行标识+'"')#该激活未在跑
        定义=插件['packages'].get(运行['packageId'])#当前包定义
        if 定义 is None or 定义.get('clientCode') is None:#没有客户端半
            raise Exception('package "'+运行['packageId']+'" has no Client half')#没有客户端半
        return {#客户端源
            'code':定义['clientCode'],#源码
            'name':定义['name'],#包名
            'pluginId':插件标识,#插件 id
            'packageId':运行['packageId'],#包 id
            'pluginRunId':运行标识,#运行 id
        }#源

    @远程('resolveRequestRun')
    def 结算运行请求(自身,请求标识,决议):#结算客户端激活请求
        """结算一次模型驱动的客户端激活请求。"""
        挂起=自身.注册表.窥视请求(请求标识)#窥视
        if 挂起 is None:#没有
            return {'accepted':False}#不受理
        插件=自身.注册表.获取(挂起['pluginId'])#对应插件
        活动=插件.get('run') if 插件 is not None else None#活动运行
        if 决议.get('ok') and (活动 is None or 活动['pluginRunId']!=决议['pluginRunId']):#成功决议对不上
            return {'accepted':False}#不受理
        if (not 决议.get('ok')) and 决议.get('pluginRunId') is not None and (活动 is None or 活动['pluginRunId']!=决议['pluginRunId']):#失败也对不上
            return {'accepted':False}#不受理
        自身.注册表.认领请求(请求标识)#认领
        已结算=自身.结算激活(插件,决议,请求标识)#结算激活
        自身.宣布已决议(请求标识,决议,None if 挂起['requiresApproval'] else 'completed')#宣布
        自身.引导运行结局(挂起,已结算)#steer 给模型
        return {'accepted':True}#已受理

    @远程('settleUserRun')
    def 结算用户运行(自身,智能体,插件标识,决议):#结算面板运行
        """在本页加载或失败其客户端半之后，结算一次直接面板运行。"""
        插件=自身.本会话插件(智能体,插件标识)#本会话拥有的插件
        if 插件 is None:#不存在
            return {'ok':False,'reason':'plugin-missing','message':插件缺失文案(插件标识)}#失败
        已结算=自身.结算激活(插件,决议)#结算激活
        自身.注入用户运行结局(智能体,插件标识,已结算)#把结局注入用户上下文
        return 已结算#返回

    def 停止(自身,智能体,插件标识):#停止运行
        """停止活动运行，但保留每一个包版本。"""
        插件=自身.本会话插件(智能体,插件标识)#本会话拥有的插件
        if 插件 is None:#不存在
            return {'ok':False,'reason':'plugin-missing','message':插件缺失文案(插件标识)}#失败
        挂起=自身.注册表.插件挂起请求(插件标识)#挂起请求
        if 插件.get('run') is None and 挂起 is None:#既没在跑也没挂起
            return {'ok':False,'reason':'not-running','message':'dynamic plugin "'+插件标识+'" is not running'}#无从停止
        if 挂起 is not None:#取消挂起审批
            自身.取消挂起(插件标识,'dynamic plugin "'+插件标识+'" was stopped before approval')#取消
        if 插件.get('run') is not None:#收回活动运行
            自身.收回(插件)#收回
        最近=插件.get('latestRun')#最近尝试
        if 最近 is not None:#有最近尝试则标停止
            最近['status']='stopped'#状态停止
            if 最近['host']['status']!='absent':#宿主非缺席
                最近['host']={'status':'stopped','waitingFor':[]}#标停止
            if 最近['client']['status']!='absent':#客户端非缺席
                最近['client']={'status':'stopped','waitingFor':[]}#标停止
        return {'ok':True}#停止成功

    @远程('stopFromPanel')
    def 面板停止(自身,智能体,插件标识):#面板停止
        """从用户面板停止插件。"""
        结果=自身.停止(智能体,插件标识)#走同一条停止路径
        if not 结果.get('ok'):#失败
            return 结果#原样
        插件=自身.本会话插件(智能体,插件标识)#停止后仍在的插件
        当前=插件.get('currentPackageId') if 插件 is not None else None#当前包
        自身.注入用户上下文(智能体,'The user stopped Cordis Plugin '+插件标识+'. Its Packages remain defined; currentPackageId is '+(当前 or 'none')+'.')#注入
        return 结果#成功

    @远程('syncInspectManifest')
    def 同步巡检清单(自身,提供方们):#同步客户端清单
        """用客户端巡检提供方目录替换宿主镜像。"""
        自身.巡检注册表.同步客户端清单(提供方们)#写入镜像
        return None#约定返回 null

    @远程('resolveInspectQuery')
    def 结算巡检查询(自身,智能体,请求标识,决议):#结算客户端巡检查询
        """用现场结果认领一条挂起的客户端巡检查询。"""
        return 自身.巡检注册表.结算客户端查询(智能体,请求标识,决议)#交给巡检注册表

    @远程('inventory')
    def 清单(自身):#帧级清单
        """整帧清单，按稳定插件一行分组。"""
        行们=[]#结果
        for 插件 in 自身.注册表.全部():#每个插件一行
            行={#清单行
                'pluginId':插件['pluginId'],#插件 id
                'agentId':插件['sessionId'],#所属会话当智能体 id
                'packages':[{#各包摘要
                    'packageId':定义['packageId'],#包 id
                    'name':定义['name'],#名称
                    'purpose':定义['purpose'],#用途
                    'hasHostHalf':定义.get('hostCode') is not None,#是否有宿主半
                    'hasClientHalf':定义.get('clientCode') is not None,#是否有客户端半
                } for 定义 in 插件['packages'].values()],#包摘要
            }#行
            if 插件.get('currentPackageId') is not None:#有当前包
                行['currentPackageId']=插件['currentPackageId']#带上
            if 插件.get('nextPackageId') is not None:#有下一包
                行['nextPackageId']=插件['nextPackageId']#带上
            if 插件.get('run') is not None:#有活动运行
                行['activeRun']={'pluginRunId':插件['run']['pluginRunId'],'packageId':插件['run']['packageId']}#活动运行指针
            if 插件.get('latestRun') is not None:#有最近尝试
                行['latestRun']=克隆尝试(插件['latestRun'])#克隆
            行们.append(行)#收入
        return 行们#清单

    def 快照(自身,智能体):#会话快照
        """读取一个会话的宿主丰富状态。"""
        行们=[]#结果
        for 插件 in 自身.注册表.按会话(智能体.id):#本会话每个插件
            行={'pluginId':插件['pluginId'],'packages':[{#各包摘要
                'packageId':定义['packageId'],'name':定义['name'],'purpose':定义['purpose'],
                'hasHostHalf':定义.get('hostCode') is not None,'hasClientHalf':定义.get('clientCode') is not None,
            } for 定义 in 插件['packages'].values()]}#行
            if 插件.get('currentPackageId') is not None:#当前包
                行['currentPackageId']=插件['currentPackageId']#带上
            if 插件.get('nextPackageId') is not None:#下一包
                行['nextPackageId']=插件['nextPackageId']#带上
            if 插件.get('run') is not None:#活动运行
                运行=插件['run']#运行
                活动={'pluginRunId':运行['pluginRunId'],'packageId':运行['packageId'],'handlers':list(运行['handlers'].keys())}#活动
                if 运行.get('fiber') is not None:#有纤维
                    活动['fiber']=运行['fiber']#带上
                if 运行.get('renderFailure') is not None:#有渲染失败
                    活动['renderFailure']=运行['renderFailure']#带上
                行['activeRun']=活动#挂上
            if 插件.get('latestRun') is not None:#最近尝试
                行['latestRun']=克隆尝试(插件['latestRun'])#克隆
            行们.append(行)#收入
        return 行们#快照

    def 引用(自身,智能体,插件标识):#引用上下文
        """读取一次显式 @pluginId 用户手势的无源码上下文。"""
        插件=自身.本会话插件(智能体,插件标识)#本会话拥有的插件
        if 插件 is None:#不存在
            return None#无
        包标识=插件.get('nextPackageId') or 插件.get('currentPackageId')#优先下一包否则当前
        if 包标识 is None:#否则最后一个包
            键们=list(插件['packages'].keys())#包键
            包标识=键们[-1] if len(键们)>0 else None#最后一个
        if 包标识 is None:#一个包都没有
            return None#无
        定义=插件['packages'].get(包标识)#取定义
        if 定义 is None:#定义丢失
            return None#无
        引用={'pluginId':插件标识,'packageId':包标识,'name':定义['name'],'purpose':定义['purpose']}#引用快照
        if 插件.get('currentPackageId') is not None:#当前包
            引用['currentPackageId']=插件['currentPackageId']#带上
        if 插件.get('nextPackageId') is not None:#下一包
            引用['nextPackageId']=插件['nextPackageId']#带上
        if 插件.get('run') is not None:#活动运行
            引用['activeRun']={'pluginRunId':插件['run']['pluginRunId'],'packageId':插件['run']['packageId']}#指针
        if 插件.get('latestRun') is not None:#最近尝试
            引用['latestRun']=克隆尝试(插件['latestRun'])#克隆
        return 引用#引用

    def 列插件(自身,智能体):#列插件
        """列出一个会话所拥有插件的无源码摘要。"""
        return [自身.巡检插件(智能体,插件['pluginId']) for 插件 in 自身.注册表.按会话(智能体.id)]#逐个巡检

    def 巡检插件(自身,智能体,插件标识):#巡检插件
        """巡检一个插件，不返回包源码。"""
        插件=自身.本会话插件(智能体,插件标识)#本会话拥有的插件
        if 插件 is None:#不存在
            raise Exception(插件缺失文案(插件标识))#不存在
        引用=自身.引用(智能体,插件标识)#引用上下文
        if 引用 is None:#没有包
            raise Exception('dynamic plugin "'+插件标识+'" has no package')#没有包
        return {**引用,'packages':[{#各包摘要
            'packageId':定义['packageId'],'name':定义['name'],'purpose':定义['purpose'],
            'hasHostHalf':定义.get('hostCode') is not None,'hasClientHalf':定义.get('clientCode') is not None,
        } for 定义 in 插件['packages'].values()]}#巡检

    def 巡检包(自身,智能体,插件标识,包标识):#巡检一个包
        """读取一个精确的不可变包及其宿主与客户端源码。"""
        插件=自身.本会话插件(智能体,插件标识)#本会话拥有的插件
        if 插件 is None:#不存在
            raise Exception(插件缺失文案(插件标识))#不存在
        定义=插件['packages'].get(包标识)#取包定义
        if 定义 is None:#没有该包
            raise Exception('dynamic package "'+包标识+'" does not exist on plugin "'+插件标识+'"')#包不存在
        代码={}#源码
        if 定义.get('hostCode') is not None:#有宿主源码
            代码['host']=定义['hostCode']#带上
        if 定义.get('clientCode') is not None:#有客户端源码
            代码['client']=定义['clientCode']#带上
        结果={'pluginId':插件标识,'packageId':包标识,'name':定义['name'],'purpose':定义['purpose'],'code':代码}#包巡检
        if 插件.get('currentPackageId') is not None:#当前包
            结果['currentPackageId']=插件['currentPackageId']#带上
        if 插件.get('nextPackageId') is not None:#下一包
            结果['nextPackageId']=插件['nextPackageId']#带上
        if 插件.get('run') is not None:#活动运行
            结果['activeRun']={'pluginRunId':插件['run']['pluginRunId'],'packageId':插件['run']['packageId']}#指针
        if 插件.get('latestRun') is not None:#最近尝试
            结果['latestRun']=克隆尝试(插件['latestRun'])#克隆
        return 结果#巡检

    @远程('reportRenderFailure')
    def 报告渲染失败(自身,智能体,插件标识,运行标识,失败):#记录渲染失败
        """为精确的活动运行记录一次加载后的渲染失败。"""
        插件=自身.本会话插件(智能体,插件标识)#本会话拥有的插件
        运行=插件.get('run') if 插件 is not None else None#活动运行
        if 运行 is not None and 运行['pluginRunId']==运行标识:#仍是该活动运行
            定义=插件['packages'].get(运行['packageId'])#当前包定义
            应引导=运行.get('renderFailure') is None#首次失败才steer
            运行['renderFailure']=失败#记下失败
            尝试=插件.get('latestRun')#最近尝试
            if 尝试 is not None and 尝试['pluginRunId']==运行标识:#尝试仍对应本运行
                尝试['error']=自身.诊断(插件,尝试,'client-render',失败)#诊断
                尝试['client']={'status':'failed','waitingFor':尝试['client']['waitingFor'],'error':失败['message']}#客户端失败
                尝试['status']='failed'#尝试失败
            if 定义 is not None and 应引导:#有定义且首次
                自身.引导渲染失败(智能体,插件,定义,运行标识,失败)#steer
        return None#约定返回 null

    @远程('reportClientGuardFailure')
    def 报告客户端守卫失败(自身,智能体,插件标识,运行标识,失败):#报告客户端守卫拒绝
        """报告包完成激活之后发生的客户端守卫拒绝。"""
        插件=自身.本会话插件(智能体,插件标识)#本会话拥有的插件
        运行=插件.get('run') if 插件 is not None else None#活动运行
        if 插件 is not None and 运行 is not None and 运行['pluginRunId']==运行标识:#仍是该活动运行
            自身.引导守卫失败(插件,运行,'Client',失败)#steer
        return None#约定返回 null

    @远程('invoke')
    def 调用(自身,插件标识,运行标识,方法,参数):#调用活动宿主方法
        """调用活动宿主方法，同时拒绝过期的客户端运行。"""
        插件=自身.注册表.获取(插件标识)#按 id 取插件
        if 插件 is None or 插件.get('run') is None:#不存在或没在跑
            return {'ok':False,'code':'plugin-not-running','message':'dynamic plugin "'+插件标识+'" is not running'}#未运行
        运行=插件['run']#活动运行
        if 运行['pluginRunId']!=运行标识:#运行 id 对不上
            return {'ok':False,'code':'stale-run','message':'activation "'+运行标识+'" is no longer active'}#过期运行
        处理器=运行['handlers'].get(方法)#按名取处理器
        if 处理器 is None:#未登记
            return {'ok':False,'code':'method-not-found','message':'dynamic plugin "'+插件标识+'" registered no Host method "'+方法+'"'}#没有该方法
        try:#处理器约定可能抛
            return {'ok':True,'value':解开(处理器(参数))}#成功则装箱 JSON
        except Exception as 错误:#处理器抛错
            失败=错误细节(错误)#抽出消息与栈
            自身.引导宿主处理器失败(插件,运行,方法,失败)#steer
            return {'ok':False,'code':'handler-error',**失败}#处理器错误

    # —— 私有辅助 —— #

    def 解析计划(自身,智能体,插件标识,包标识,模式,允许挂接=False):#解析激活计划
        """计划或拒绝。"""
        插件=自身.本会话插件(智能体,插件标识)#本会话拥有的插件
        if 插件 is None:#插件缺失
            return {'ok':False,'response':{'ok':False,'reason':'plugin-missing','message':插件缺失文案(插件标识)}}#失败
        定义=插件['packages'].get(包标识)#取包定义
        if 定义 is None:#没有该包
            return {'ok':False,'response':{'ok':False,'reason':'package-missing','message':'plugin "'+插件标识+'" has no package "'+包标识+'"'}}#包缺失
        当前=插件.get('currentPackageId')#当前成功版本
        if 模式=='update' and (当前 is None or 当前==包标识):#update 却没有可切换的不同版本
            消息=('plugin "'+插件标识+'" has no successful version yet; start "'+包标识+'" with mode "run"') if 当前 is None else ('package "'+包标识+'" is already current; use mode "run"')#应改用 run
            return {'ok':False,'response':{'ok':False,'reason':'invalid-mode','message':消息}}#非法 update
        if 模式=='run' and 当前 is not None and 当前!=包标识:#run 却指向另一个已成功版本
            return {'ok':False,'response':{'ok':False,'reason':'invalid-mode','message':'package "'+包标识+'" differs from current "'+当前+'"; use mode "update"'}}#应改用 update
        if (not 允许挂接) and 插件标识 in 自身.启动中:#不允许挂接且已在启动
            return {'ok':False,'response':{'ok':False,'reason':'transition-in-flight','message':'plugin "'+插件标识+'" is already starting'}}#转换进行中
        return {'ok':True,'plugin':插件,'definition':定义,'mode':模式}#合法计划

    def 激活(自身,计划,请求标识,允许挂接,尝试):#启动或去重挂接
        """去重返回同一承诺。"""
        在飞=自身.启动中.get(计划['plugin']['pluginId'])#已在飞的启动
        if 在飞 is not None:#去重
            return 解开(在飞)#返回同一结果
        def 执行():#新启一次
            """真正启动。"""
            try:#启动
                return 自身.全新启动(计划,请求标识,允许挂接,尝试)#新启
            finally:#结束后清掉
                自身.启动中.pop(计划['plugin']['pluginId'],None)#清掉
        承诺=已兑现(执行())#同步包装为已兑现——全新启动内部已同步
        自身.启动中[计划['plugin']['pluginId']]=承诺#记下进行中
        try:#取结果
            return 解开(承诺)#结果
        finally:#确保清除
            自身.启动中.pop(计划['plugin']['pluginId'],None)#清掉

    def 全新启动(自身,计划,请求标识,允许挂接,尝试):#真正启动一次新运行
        """宿主半结果。"""
        插件=计划['plugin']#插件
        定义=计划['definition']#定义
        模式=计划['mode']#模式
        活动=插件.get('run')#活动运行
        if 允许挂接 and 活动 is not None and 活动['packageId']==定义['packageId'] and 活动['pluginRunId']==尝试['pluginRunId']:#挂接成功
            return {'ok':True,'pluginId':插件['pluginId'],'packageId':定义['packageId'],'pluginRunId':活动['pluginRunId'],'waitingFor':仍缺(自身.ctx,活动),'startedHere':False}#挂接回执
        if 活动 is not None:#先收回旧运行
            自身.收回(插件)#收回
        if 模式=='update' or 插件.get('currentPackageId') is None:#记下下一包
            插件['nextPackageId']=定义['packageId']#下一包
        运行={#新运行记录
            'pluginRunId':尝试['pluginRunId'],#运行 id
            'packageId':定义['packageId'],#包 id
            'handlers':{},#空处理器表
            'handlerDisposers':[],#拆除器
            'reportedRuntimeErrors':set(),#已报告的运行时错误
        }#运行
        if 请求标识 is not None:#有请求
            运行['startedForRequest']=请求标识#记下
        if 定义.get('hostCode') is not None:#有宿主源码
            失败=自身.启动宿主(插件,定义['hostCode'],运行)#求值并启动宿主半
            if 失败 is not None:#启动失败
                return {'ok':False,**失败}#失败
        插件['run']=运行#挂上活动运行
        自身.ctx.emit('cordis/dynamic-package',{#发出动态包事件
            'pluginId':插件['pluginId'],#插件 id
            'packageId':定义['packageId'],#包 id
            'pluginRunId':运行['pluginRunId'],#运行 id
            'name':定义['name'],#包名
        })#emit
        等待=仍缺(自身.ctx,运行)#仍缺的服务
        尝试['host']={#更新宿主半状态
            'status':'absent' if 运行.get('fiber') is None else ('running' if len(等待)==0 else 'waiting'),#缺席、运行中或等待
            'waitingFor':等待,#仍缺
        }#host
        if 定义.get('clientCode') is None:#没有客户端半
            自身.提交激活(插件,运行)#直接提交激活
        else:#有客户端半
            尝试['status']='client-pending'#等待客户端
            尝试['client']={'status':'pending','waitingFor':[]}#客户端待启动
        return {'ok':True,'pluginId':插件['pluginId'],'packageId':定义['packageId'],'pluginRunId':运行['pluginRunId'],'waitingFor':等待,'startedHere':True}#新启回执

    def 启动宿主(自身,插件,宿主代码,运行):#求值并挂上宿主半
        """失败细节或成功 None。"""
        def 登记(方法,函数):#登记宿主方法
            """归一方法名与函数。"""
            归一=归一处理器(方法,函数)#归一
            运行['handlers'][归一['method']]=归一['handler']#写入表
            def 拆除():#拆除该登记
                """仍是自己才删。"""
                if 运行['handlers'].get(归一['method']) is 归一['handler']:#仍是自己
                    del 运行['handlers'][归一['method']]#删
            运行['handlerDisposers'].append(拆除)#记下拆除器
            return 拆除#交给调用方
        try:#求值与启动可能抛
            沙箱=创建沙箱(插件['pluginId'],{'handle':登记})#带 handle 的沙箱
            超时=取字段(自身.已解析,'vmTimeoutMs',5000)#超时
            已求值=求值宿主代码(沙箱,宿主代码,插件['pluginId'],超时)#求值宿主源码
            if not 是否插件(已求值):#不是合法插件
                raise Exception('the Host half returned `None` — did you forget `return`?' if 已求值 is None else 'the Host half must return a Plugin function or an object with apply(ctx)')#必须是插件
            def 报告守卫(错误):#守卫失败回调
                """steer 宿主守卫失败。"""
                自身.引导守卫失败(插件,运行,'Host',错误细节(错误))#steer
            运行['fiber']=启动宿主半(自身.需要组(),已求值,报告守卫)#启动宿主半纤维
            return None#成功
        except Exception as 错误:#求值或启动失败
            for 拆除 in 运行['handlerDisposers'][:]:#清掉已登记处理器
                拆除()#拆除
            运行['handlerDisposers'].clear()#清空
            return 错误细节(错误)#抽出失败细节

    def 结算激活(自身,插件,决议,请求标识=None):#按客户端决议提交或回滚
        """激活或失败。"""
        if 插件 is None:#激活中被移除
            return {'ok':False,'reason':'plugin-missing','message':'the dynamic plugin was removed during activation'}#失败
        尝试=插件.get('latestRun')#最近尝试
        if not 决议.get('ok'):#决议失败
            if 决议.get('reason')=='rejected':#用户拒绝
                if 尝试 is not None:#有尝试则记账
                    尝试['status']='rejected'#标拒绝
                    尝试['error']=自身.诊断(插件,尝试,'approval',决议.get('message') or 'the run request was declined')#审批诊断
                    尝试['client']={'status':'stopped','waitingFor':[]}#客户端停止
                return {'ok':False,'reason':'rejected','message':决议.get('message') or 'the run request was declined'}#拒绝回执
            运行=插件.get('run')#活动运行
            拥有=(运行 is not None and 决议.get('pluginRunId')==运行['pluginRunId']
                and (请求标识 is None or 运行.get('startedForRequest')==请求标识)
                and 决议.get('startedHere') is not False)#本运行的失败
            if 拥有:#本运行的失败则收回
                自身.收回(插件)#收回
            if 尝试 is not None and (决议.get('pluginRunId') is None or 尝试['pluginRunId']==决议.get('pluginRunId')):#尝试对应本决议
                阶段='host-apply' if 决议.get('reason')=='host-half-failed' else 'client-apply'#宿主或客户端应用阶段
                失败={'message':决议.get('message') or 决议.get('reason')}#失败细节
                if 决议.get('stack') is not None:#有栈
                    失败['stack']=决议['stack']#带上
                自身.失败尝试(插件,尝试,阶段,失败)#标记尝试失败
            回执={'ok':False,'reason':决议.get('reason'),'message':决议.get('message') or 决议.get('reason')}#失败回执
            if 决议.get('stack') is not None:#有栈
                回执['stack']=决议['stack']#带上
            return 回执#失败
        运行=插件.get('run')#活动运行
        if 运行 is None or 运行['pluginRunId']!=决议['pluginRunId']:#运行已不在
            return {'ok':False,'reason':'client-half-failed','message':'activation "'+决议['pluginRunId']+'" is no longer active'}#激活已失效
        if 尝试 is not None and 尝试['pluginRunId']==运行['pluginRunId']:#尝试对应本运行
            等待=决议.get('waitingFor') or []#等待的服务
            尝试['client']={'status':'running' if len(等待)==0 else 'waiting','waitingFor':等待}#更新客户端状态
        自身.提交激活(插件,运行)#提交激活
        成功=自身.运行响应(插件,{#宿主半成功形
            'ok':True,'pluginId':插件['pluginId'],'packageId':运行['packageId'],
            'pluginRunId':运行['pluginRunId'],'waitingFor':仍缺(自身.ctx,运行),'startedHere':False,
        })#成功
        if 决议.get('waitingFor') is not None:#有客户端等待
            成功['clientWaitingFor']=决议['waitingFor']#带上
        return 成功#成功回执

    def 提交激活(自身,插件,运行):#提交激活指针
        """当前包切到本运行。"""
        插件['currentPackageId']=运行['packageId']#当前包
        插件.pop('nextPackageId',None)#清掉下一包
        运行.pop('startedForRequest',None)#清掉启动来源请求
        尝试=插件.get('latestRun')#最近尝试
        if 尝试 is not None and 尝试['pluginRunId']==运行['pluginRunId']:#尝试对应本运行
            尝试['status']='waiting' if 尝试['host']['status']=='waiting' or 尝试['client']['status']=='waiting' else 'running'#等待或运行中
            尝试.pop('approvalRequestId',None)#清掉审批请求
            尝试.pop('requiresApproval',None)#清掉是否需批
            尝试.pop('error',None)#清掉错误

    def 运行响应(自身,插件,已启):#把宿主半成功结果拼成运行成功响应
        """运行成功形。"""
        最近=插件.get('latestRun')#最近尝试
        模式=最近['mode'] if 最近 is not None and 最近['pluginRunId']==已启['pluginRunId'] else 'run'#沿用尝试模式或默认 run
        return {'ok':True,'status':'running','pluginId':插件['pluginId'],'packageId':已启['packageId'],'pluginRunId':已启['pluginRunId'],'waitingFor':已启['waitingFor'],'currentPackageId':已启['packageId'],'mode':模式}#成功响应

    def 宣布已决议(自身,请求标识,决议,覆盖=None):#宣布运行请求已决议
        """发出已决议事件。"""
        if 覆盖 is not None:#覆盖
            结局=覆盖#用覆盖
        elif 决议.get('ok'):#成功
            结局='approved'#批准
        elif 决议.get('reason')=='rejected':#拒绝
            结局='rejected'#拒绝
        else:#其它失败
            结局='failed'#失败
        自身.ctx.emit('cordis/request-run-resolved',{'requestId':请求标识,'outcome':结局})#发出事件

    def 引导运行结局(自身,挂起,已结算):#把运行结局steer给模型
        """steer 文本。"""
        智能体们=自身.根上下文.get('agents')#智能体表
        智能体=智能体们.获取(挂起['agentId']) if 智能体们 is not None and hasattr(智能体们,'获取') else (智能体们.get(挂起['agentId']) if 智能体们 is not None else None)#原请求的智能体
        if 智能体 is None:#智能体已不在
            return#返回
        插件=自身.注册表.获取(挂起['pluginId'])#对应插件
        身份=挂起['pluginId']+'/'+挂起['packageId']+' ('+挂起['pluginRunId']+')'#身份串
        if 已结算.get('ok'):#激活成功
            文本='Cordis '+挂起['mode']+' '+身份+' completed successfully. currentPackageId is '+str(已结算.get('currentPackageId') or 挂起['packageId'])+'. Continue using the running Plugin.'#成功
        elif 已结算.get('reason')=='rejected':#用户拒绝
            文本='The user rejected Cordis '+挂起['mode']+' '+身份+'. Do not request the same activation again unless the user asks.'#拒绝
        else:#其它失败
            当时='awaiting-approval' if 挂起['requiresApproval'] else 'starting'#当时返回给工具的状态
            当前=插件.get('currentPackageId') if 插件 is not None else None#当前包
            下一=插件.get('nextPackageId') if 插件 is not None else 挂起['packageId']#下一包
            文本=('Cordis '+挂起['mode']+' '+身份+' failed after cordis_run returned '+当时+': '
                +str(已结算.get('reason'))+'\n'+格式错误细节(已结算)+'\n'
                +'currentPackageId: '+str(当前 or 'none')+'\n'
                +'nextPackageId: '+str(下一 or 挂起['packageId'])+'\n'
                +'Inspect the failed Package, correct it on the same Plugin when needed, and retry the activation autonomously.')#失败
        智能体.steer(创建用户消息({'content':[{'type':'text','text':文本}],'source':{'kind':'plugin','plugin':'cordis-host-runner'}}))#steer

    def 引导渲染失败(自身,智能体,插件,定义,运行标识,失败):#把渲染失败steer给模型
        """steer 文本。"""
        文本=('Cordis Client UI '+插件['pluginId']+'/'+定义['packageId']+' ('+运行标识+') failed while rendering '
            +'Slot "'+失败['slot']+'" after activation.\n'+格式错误细节(失败)+'\n'
            +'entryAbdicated: '+str(失败.get('abdicated'))+'\n'
            +'Inspect the failed Package, fix the Client code by defining a new Package on the same Plugin, and '
            +'activate that Package autonomously with cordis_run mode:"update".')#渲染失败
        智能体.steer(创建用户消息({'content':[{'type':'text','text':文本}],'source':{'kind':'plugin','plugin':'cordis-host-runner'}}))#steer

    def 引导宿主处理器失败(自身,插件,运行,方法,失败):#把宿主处理器失败steer给模型
        """steer 文本。"""
        报告键='Host\x00handler\x00'+方法+'\x00'+失败['message']#去重键
        if not 自身.认领运行时失败(插件,运行,报告键):#已报告过
            return#跳过
        智能体们=自身.根上下文.get('agents')#智能体表
        智能体=None if 智能体们 is None else (智能体们.获取(插件['sessionId']) if hasattr(智能体们,'获取') else 智能体们.get(插件['sessionId']))#所属会话智能体
        if 智能体 is None:#智能体已不在
            return#返回
        import json#序列化方法名
        文本=('Cordis Host handler '+插件['pluginId']+'/'+运行['packageId']+' ('+运行['pluginRunId']+') failed when the Client called '
            +'host.call('+json.dumps(方法)+').\n'+格式错误细节(失败)+'\n'
            +'The Plugin remains running. Inspect this Package, correct the Host code on the same Plugin, and activate '
            +'the new Package autonomously with cordis_run mode:"update". If the handler needs a Service, either declare '
            +'that Service in the returned Plugin inject list or read it with ctx.get(name) and handle undefined.')#处理器失败
        智能体.steer(创建用户消息({'content':[{'type':'text','text':文本}],'source':{'kind':'plugin','plugin':'cordis-host-runner'}}))#steer

    def 引导守卫失败(自身,插件,运行,平面,失败):#把守卫拒绝steer给模型
        """steer 文本。"""
        报告键=平面+'\x00guard\x00'+失败['message']#去重键
        if not 自身.认领运行时失败(插件,运行,报告键):#已报告过
            return#跳过
        智能体们=自身.根上下文.get('agents')#智能体表
        智能体=None if 智能体们 is None else (智能体们.获取(插件['sessionId']) if hasattr(智能体们,'获取') else 智能体们.get(插件['sessionId']))#所属
        if 智能体 is None:#智能体已不在
            return#返回
        文本=('Cordis '+平面+' guard rejected runtime code in '+插件['pluginId']+'/'+运行['packageId']+' '
            +'('+运行['pluginRunId']+') after activation.\n'+格式错误细节(失败)+'\n'
            +'The Plugin remains running. Inspect this Package, define a corrected Package on the same Plugin, and '
            +'activate it autonomously with cordis_run mode:"update".')#守卫拒绝
        智能体.steer(创建用户消息({'content':[{'type':'text','text':文本}],'source':{'kind':'plugin','plugin':'cordis-host-runner'}}))#steer

    def 认领运行时失败(自身,插件,运行,键):#认领一次运行时失败报告
        """已报告过则 False。"""
        尝试=插件.get('latestRun')#最近尝试
        if 插件.get('run') is not 运行 or 尝试 is None or 尝试['pluginRunId']!=运行['pluginRunId']:#不是当前活动运行
            return False#跳过
        if 尝试['status'] not in ('running','waiting'):#或不在运行/等待
            return False#跳过
        if 键 in 运行['reportedRuntimeErrors']:#已经报告过
            return False#跳过
        运行['reportedRuntimeErrors'].add(键)#记下键
        return True#本次赢得报告

    def 注入用户运行结局(自身,智能体,插件标识,已结算):#把用户手势运行结局注入上下文
        """注入文本。"""
        插件=自身.本会话插件(智能体,插件标识)#本会话拥有的插件
        if 已结算.get('ok'):#手势成功
            文本='The user manually ran Cordis Plugin '+插件标识+', Package '+已结算['packageId']+', as '+已结算['pluginRunId']+'. The activation succeeded; currentPackageId is '+str(已结算.get('currentPackageId'))+'.'#成功
        else:#手势失败
            尝试=插件.get('latestRun') if 插件 is not None else None#最近尝试
            段='' if 尝试 is None else ', Package '+尝试['packageId']+', as '+尝试['pluginRunId']#包与运行
            当前=插件.get('currentPackageId') if 插件 is not None else None#当前包
            下一=插件.get('nextPackageId') if 插件 is not None else None#下一包
            文本=('The user manually ran Cordis Plugin '+插件标识+段+', but it failed: '
                +str(已结算.get('reason'))+'\n'+格式错误细节(已结算)+'\n'
                +'currentPackageId: '+str(当前 or 'none')+'\n'
                +'nextPackageId: '+str(下一 or 'none'))#失败
        自身.注入用户上下文(智能体,文本)#注入

    def 注入用户上下文(自身,智能体,文本):#把文本注入用户上下文
        """注入用户消息。"""
        智能体们=自身.根上下文.get('agents')#智能体表
        if 智能体们 is None:#无表
            return#返回
        当前=智能体们.获取(智能体.id) if hasattr(智能体们,'获取') else 智能体们.get(智能体.id)#该智能体
        if 当前 is not 智能体:#已不在表里
            return#返回
        智能体.inject(创建用户消息({'content':[{'type':'text','text':文本}],'source':{'kind':'plugin','plugin':'cordis-host-runner'}}))#注入

    def 取消挂起(自身,插件标识,消息):#取消挂起的运行请求
        """取消并宣布。"""
        请求标识=自身.注册表.插件挂起请求(插件标识)#挂起请求 id
        if 请求标识 is None:#没有
            return#返回
        挂起=自身.注册表.认领请求(请求标识)#认领
        if 挂起 is None:#已被别人认领
            return#返回
        插件=自身.注册表.获取(插件标识)#对应插件
        最近=插件.get('latestRun') if 插件 is not None else None#最近尝试
        if 最近 is not None and 最近['pluginRunId']==挂起['pluginRunId']:#最近尝试就是该请求
            最近['status']='cancelled'#标取消
            最近['error']=自身.诊断(插件,最近,'approval',消息)#审批诊断
            最近.pop('approvalRequestId',None)#清掉审批请求
            最近.pop('requiresApproval',None)#清掉是否需批
        自身.宣布已决议(请求标识,{'ok':False,'reason':'rejected'},'cancelled')#宣布已取消

    def 新建尝试(自身,计划):#按计划新建一次尝试
        """尝试记录。"""
        return {#尝试
            'pluginRunId':动态运行标识(自身.注册表.铸造运行标识()),#铸造运行 id
            'packageId':计划['definition']['packageId'],#包 id
            'mode':计划['mode'],#运行模式
            'status':'starting-host',#先启宿主
            'host':{'status':'absent' if 计划['definition'].get('hostCode') is None else 'pending','waitingFor':[]},#宿主半
            'client':{'status':'absent' if 计划['definition'].get('clientCode') is None else 'pending','waitingFor':[]},#客户端半
        }#尝试

    def 失败尝试(自身,插件,尝试,阶段,失败):#把尝试标为失败
        """记账。"""
        尝试['status']='failed'#状态失败
        尝试['error']=自身.诊断(插件,尝试,阶段,失败)#诊断
        if 阶段.startswith('host'):#宿主阶段
            尝试['host']={'status':'failed','waitingFor':[],'error':取字段(失败,'message')}#宿主失败
        else:#客户端阶段
            尝试['client']={'status':'failed','waitingFor':[],'error':取字段(失败,'message')}#客户端失败

    def 诊断(自身,插件,尝试,阶段,失败):#拼一条尝试诊断
        """诊断对象。"""
        细节={'message':失败} if isinstance(失败,str) else dict(失败)#统一成细节
        return {'phase':阶段,**细节,'pluginId':插件['pluginId'],'packageId':尝试['packageId'],'pluginRunId':尝试['pluginRunId']}#诊断

    def 收回(自身,插件):#收回活动运行
        """拆除处理器与宿主纤维。"""
        运行=插件.get('run')#活动运行
        if 运行 is None:#没有
            return#返回
        插件.pop('run',None)#摘掉指针
        for 拆除 in 运行['handlerDisposers'][:]:#拆除全部处理器
            拆除()#拆除
        运行['handlerDisposers'].clear()#清空
        if 运行.get('fiber') is not None:#有纤维
            解开(运行['fiber'].dispose())#拆除宿主纤维
        自身.ctx.emit('cordis/dynamic-retract',{#发出收回事件
            'pluginId':插件['pluginId'],#插件 id
            'packageId':运行['packageId'],#包 id
            'pluginRunId':运行['pluginRunId'],#运行 id
        })#emit

    def 本会话插件(自身,智能体,插件标识):#本会话拥有的插件
        """会话对得上才返回。"""
        插件=自身.注册表.获取(插件标识)#按 id 取
        return 插件 if 插件 is not None and 插件['sessionId']==智能体.id else None#会话对得上

    def 需要组(自身):#取或建动态插件纤维组
        """惰性挂一个空插件当组。"""
        if 自身.组 is None:#尚未创建
            def 空应用(*_位置参数,**_关键字参数):#空插件体
                return None#无贡献
            自身.组=自身.根上下文.plugin({'name':'cordis-dynamic','apply':空应用})#空插件当组
        return 自身.组#返回组

#工具面与上游 Remote 方法名对照（tool_cordis 经 ctx.dynamicCordisRunner.* 调用）
动态插件运行器服务.define=动态插件运行器服务.定义#define
动态插件运行器服务.undefine=动态插件运行器服务.取消定义#undefine
动态插件运行器服务.run=动态插件运行器服务.运行#run
动态插件运行器服务.stop=动态插件运行器服务.停止#stop
动态插件运行器服务.inventory=动态插件运行器服务.清单#inventory
动态插件运行器服务.snapshot=动态插件运行器服务.快照#snapshot
动态插件运行器服务.reference=动态插件运行器服务.引用#reference
动态插件运行器服务.listPlugins=动态插件运行器服务.列插件#listPlugins
动态插件运行器服务.inspectPlugin=动态插件运行器服务.巡检插件#inspectPlugin
动态插件运行器服务.inspectPackage=动态插件运行器服务.巡检包#inspectPackage
动态插件运行器服务.invoke=动态插件运行器服务.调用#invoke
DynamicCordisRunnerService=动态插件运行器服务#上游类名
