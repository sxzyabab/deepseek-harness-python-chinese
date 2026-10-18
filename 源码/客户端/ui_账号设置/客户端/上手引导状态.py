'桌面上手引导的进度，以及完成时写回的显示偏好'
from ....基础设施.js特性 import PromiseEX as 期约
from ...存储 import 创建快照存储,浅相等
from ..上手引导设置 import 新进度
from .上手引导余额 import 有上手引导额度

__all__=['桌面上手引导控制器']

def 接上(结果,成功,失败=None):
    '配置表单的写入返回期约。浏览器桥的密钥查询也可能返回期约'
    if hasattr(结果,'然后'):
        结果.然后(成功,失败)
        return True
    然后=getattr(结果,'then',None)
    if callable(然后):
        if 失败 is None:
            然后(成功)
        else:
            然后(成功,失败)
        return True
    return False

def 视图状态(快照):
    '账号视图上的 status。还没有视图时是 None'
    视图=快照.get('view') if isinstance(快照,dict) else None
    if isinstance(视图,dict):
        return 视图.get('status')
    return None

class 桌面上手引导控制器:
    '宿主设置上的可恢复进度。完成时先写偏好，再写 done'
    def __init__(自身,进度,聊天,设开发者工具,账号,读密钥,设置):
        '订上进度、聊天、账号和设置镜像，马上推导一次'
        自身.进度=进度
        自身.聊天=聊天
        自身.设开发者工具=设开发者工具
        自身.账号=账号
        自身.读密钥=读密钥
        自身.设置=设置
        自身.状态=创建快照存储({
            'status':'loading',
            'visible':False,
            'progress':新进度(),
            'error':None,
            'creditFunded':False,
        })
        自身.保存中=False
        自身.完成中=False
        自身.草稿=None
        自身.写链=期约()
        自身.写链.解决(True)
        自身.已拆除=False
        自身.凭据代=0
        自身.有密钥=None
        自身.正在查密钥=False
        自身.错误=None
        自身.失败写入=None
        自身.已有额度=None
        def 推导(_值=None):
            '任一来源变化都重新推导'
            自身.推导()
        自身.拆除器=[
            设置.subscribe(推导),
            进度.subscribe(推导),
            聊天.subscribe(推导),
            账号.subscribe(推导),
        ]
        自身.推导()

    def 作废凭据(自身):
        '提供方或凭据变了就重新查。上次按密钥完成的失败写也丢掉'
        自身.凭据代+=1
        自身.正在查密钥=False
        自身.有密钥=None
        if isinstance(自身.失败写入,dict) and 自身.失败写入['next'].get('completion')=='api-key':
            自身.错误=None
            自身.失败写入=None
        自身.推导()

    def 更新(自身,变更):
        '先把选择显示出来，再串行写入。最后一次被拒绝的写入会回到已保存的进度'
        结果=期约()
        快照=自身.账号.getSnapshot()
        if 自身.完成中 or (自身.保存中 and 自身.草稿 is None) or 自身.已拆除 or 视图状态(快照)!='credential-stored':
            结果.解决(False)
            return 结果
        当前=自身.草稿 if 自身.草稿 is not None else 自身.读进度()
        if 当前 is None or 当前.get('step')=='done':
            结果.解决(False)
            return 结果
        下一=dict(当前)
        下一.update(变更)
        自身.草稿=下一
        自身.错误=None
        下一链=期约()
        先前链=自身.写链
        自身.写链=下一链
        def 写完(成功):
            '这次草稿还在时清掉，再推导'
            if 自身.草稿 is 下一:
                自身.草稿=None
            自身.推导()
            落定=成功 is True
            下一链.解决(落定)
            结果.解决(落定)
        def 去写(_先前=None):
            '写入时账号必须仍是已登录'
            if 自身.已拆除 or 视图状态(自身.账号.getSnapshot())!='credential-stored':
                写完(False)
                return
            保存结果=自身.保存(下一,False)
            if 接上(保存结果,写完) is not True:
                写完(保存结果)
        自身.推导()
        if 接上(先前链,去写) is not True:
            去写(True)
        return 结果

    def 完成(自身,原因):
        '写上选择的显示和开发者工具，再标完这一次安装'
        结果=期约()
        if 自身.完成中 or 自身.已拆除 or 视图状态(自身.账号.getSnapshot())!='credential-stored':
            结果.解决(False)
            return 结果
        自身.完成中=True
        自身.推导()
        def 收尾(成功):
            '无论成败都结束完成中'
            自身.完成中=False
            自身.推导()
            结果.解决(成功 is True)
        def 去完成(先前成功):
            '前面的更新没写上就不完成'
            if 先前成功 is not True:
                收尾(False)
                return
            完成结果=自身.收尾完成(原因)
            if 接上(完成结果,收尾) is not True:
                收尾(完成结果)
        if 接上(自身.写链,去完成) is not True:
            去完成(True)
        return 结果

    def 收尾完成(自身,原因):
        '办公完成用紧凑过程。跳过用标准过程。开发必须已经选了过程'
        if 自身.保存中 or 自身.已拆除 or 视图状态(自身.账号.getSnapshot())!='credential-stored':
            结果=期约()
            结果.解决(False)
            return 结果
        当前=自身.读进度()
        if 当前 is None or 当前.get('step') in ('done','welcome'):
            结果=期约()
            结果.解决(False)
            return 结果
        办公=原因=='completed' and 当前.get('purpose')=='office'
        开发=原因=='completed' and 办公 is not True
        if 开发 and 当前.get('process') is None:
            结果=期约()
            结果.解决(False)
            return 结果
        下一=dict(当前)
        下一['step']='done'
        下一['completion']=原因
        if 办公:
            下一['process']='compact'
        elif 原因=='skipped':
            下一['process']='standard'
        下一['usage']='detailed' if 开发 else 'compact'
        下一['developerTools']=开发
        return 自身.保存(下一,True)

    def 重试(自身):
        '重试最初的设置读取，或上一次没写上的选择'
        结果=期约()
        if 自身.保存中 or 自身.完成中 or 自身.草稿 is not None or 自身.已拆除 or 视图状态(自身.账号.getSnapshot())!='credential-stored':
            结果.解决(False)
            return 结果
        设置快照=自身.设置.getSnapshot()
        if 设置快照.get('error') is not None and 自身.进度.getSnapshot().get('status')=='loading':
            自身.设置.确保()
            结果.解决(自身.进度.getSnapshot().get('status')=='ready')
            return 结果
        待写=自身.失败写入
        if 待写 is None:
            结果.解决(False)
            return 结果
        def 已写(成功):
            '重试的结果就是下一次更新要等的结果'
            结果.解决(成功 is True)
        保存结果=自身.保存(待写['next'],待写['applyPreferences'])
        if 接上(保存结果,已写) is not True:
            已写(保存结果)
        return 结果

    def 拆除(自身):
        '卸下订阅。迟到的密钥读取不能再写进度'
        自身.已拆除=True
        自身.凭据代+=1
        for 拆 in 自身.拆除器:
            拆()

    def 读进度(自身):
        '把宿主还没存过的选择补成 null'
        值=自身.进度.getSnapshot().get('value')
        if 值 is None:
            return None
        进度=dict(值)
        if 'purpose' not in 进度 or 进度['purpose'] is None:
            进度['purpose']=None
        if 'process' not in 进度 or 进度['process'] is None:
            进度['process']=None
        if 'completion' not in 进度 or 进度['completion'] is None:
            进度['completion']=None
        return 进度

    def 保存(自身,下一,应用偏好):
        '先写聊天偏好和开发者工具，再写引导进度。失败记下来供重试'
        账号状态=视图状态(自身.账号.getSnapshot())
        自身.保存中=True
        自身.错误=None
        自身.推导()
        结果=期约()
        def 失败():
            '设置拒绝或传输失败都记成 settings'
            自身.错误='settings'
            自身.失败写入={'next':下一,'applyPreferences':应用偏好}
            自身.保存中=False
            自身.推导()
            结果.解决(False)
        def 成功():
            '写上了就清掉失败记录'
            自身.失败写入=None
            自身.保存中=False
            自身.推导()
            结果.解决(True)
        def 账号已变():
            '写的过程中登录状态变了就停，不算失败'
            return 自身.已拆除 or 视图状态(自身.账号.getSnapshot())!=账号状态
        def 写进度():
            '把下一份进度的每个字段都 set 进去'
            if 账号已变():
                自身.保存中=False
                自身.推导()
                结果.解决(False)
                return
            操作=[]
            for 字段,值 in 下一.items():
                操作.append({'op':'set','path':[字段],'value':值})
            def 已写(接受):
                '宿主快照必须和要写的每个字段一致'
                已存=自身.读进度()
                相符=接受 is True and 已存 is not None
                if 相符:
                    for 字段,值 in 下一.items():
                        if 已存.get(字段)!=值:
                            相符=False
                            break
                if 相符:
                    成功()
                else:
                    失败()
            try:
                写=自身.进度.mutate(操作)
            except Exception:
                失败()
                return
            if 接上(写,已写,lambda _错误:失败()) is not True:
                已写(写 is True)
        def 写偏好():
            '聊天的过程展示和用量，以及开发者工具开关'
            if 账号已变():
                自身.保存中=False
                自身.推导()
                结果.解决(False)
                return
            模式=下一['process']
            def 偏好已写(接受):
                '聊天快照必须已经是这次要的模式和用量'
                if 账号已变():
                    自身.保存中=False
                    自身.推导()
                    结果.解决(False)
                    return
                已存=自身.聊天.getSnapshot().get('value')
                if 接受 is not True or not isinstance(已存,dict) or 已存.get('transcriptView')!=模式 or 已存.get('performanceUsage')!=下一['usage']:
                    失败()
                    return
                try:
                    自身.设开发者工具(下一['developerTools'])
                except Exception:
                    失败()
                    return
                写进度()
            try:
                写=自身.聊天.mutate([
                    {'op':'set','path':['transcriptView'],'value':模式},
                    {'op':'set','path':['performanceUsage'],'value':下一['usage']},
                ])
            except Exception:
                失败()
                return
            if 接上(写,偏好已写,lambda _错误:失败()) is not True:
                偏好已写(写 is True)
        try:
            if 应用偏好:
                写偏好()
            else:
                写进度()
        except Exception:
            失败()
        return 结果

    def 推导(自身):
        '从宿主进度、账号和草稿算出覆盖层要显示的状态'
        if 自身.已拆除:
            return
        宿主=自身.进度.getSnapshot()
        快照=自身.账号.getSnapshot()
        已登录=视图状态(快照)=='credential-stored'
        进度=自身.草稿 if 自身.草稿 is not None else 自身.读进度()
        if 进度 is None:
            进度=新进度()
        if 已登录 is not True:
            自身.已有额度=None
        elif 自身.已有额度 is None and 宿主.get('status')=='ready' and 进度.get('step')=='credit':
            细节=快照.get('details') if isinstance(快照,dict) else None
            余额=细节.get('balance') if isinstance(细节,dict) else None
            自身.已有额度=有上手引导额度(余额)
        if 已登录 and isinstance(自身.失败写入,dict) and 自身.失败写入['next'].get('completion')=='api-key':
            自身.失败写入=None
            自身.错误=None
        已完成=进度.get('step')=='done'
        不可用=宿主.get('status')=='unavailable' or (宿主.get('status')=='ready' and 宿主.get('writable') is not True)
        读失败=宿主.get('status')=='loading' and 自身.设置.getSnapshot().get('error') is not None
        账号失败=快照.get('view') is None and 快照.get('failed') is True
        先前=自身.状态.getSnapshot()
        进度对象=先前['progress'] if 自身.进度相同(先前['progress'],进度) else 进度
        if 自身.完成中 or (自身.保存中 and 自身.草稿 is None):
            状态名='saving'
        elif 不可用 or 读失败 or 账号失败 or 自身.错误 is not None:
            状态名='error'
        elif 宿主.get('status')=='loading' or 快照.get('view') is None:
            状态名='loading'
        else:
            状态名='ready'
        下一={
            'progress':进度对象,
            'creditFunded':自身.已有额度 is True,
            'visible':已完成 is not True and 已登录 and 不可用 is not True,
            'status':状态名,
            'error':'settings' if 不可用 or 读失败 else 自身.错误,
        }
        if 浅相等(先前,下一) is not True:
            自身.状态.set(下一)
        if 已完成 or 自身.保存中 or 自身.完成中 or 自身.草稿 is not None or 不可用 or 宿主.get('status')!='ready' or 自身.聊天.getSnapshot().get('status')!='ready' or 视图状态(快照)!='signed-out':
            return
        if 自身.有密钥 is True and 自身.错误 is None:
            密钥完成=dict(进度)
            密钥完成['step']='done'
            密钥完成['process']='standard'
            密钥完成['usage']='detailed'
            密钥完成['developerTools']=True
            密钥完成['completion']='api-key'
            自身.保存(密钥完成,True)
        elif 自身.有密钥 is None and 自身.正在查密钥 is not True:
            自身.正在查密钥=True
            代=自身.凭据代
            def 已到(有):
                '过期的查询丢掉'
                if 自身.已拆除 or 代!=自身.凭据代:
                    return
                自身.有密钥=有 is True
                自身.正在查密钥=False
                自身.推导()
            def 失败(_错误=None):
                '桥不可用就当成没有密钥'
                if 自身.已拆除 or 代!=自身.凭据代:
                    return
                自身.正在查密钥=False
                自身.有密钥=False
            try:
                查询=自身.读密钥()
            except Exception as 错误:
                失败(错误)
                return
            if 接上(查询,已到,失败) is not True:
                if isinstance(查询,dict) and 'ok' in 查询:
                    if 查询['ok'] is True:
                        已到(查询.get('value'))
                    else:
                        失败()
                else:
                    已到(查询)

    def 进度相同(自身,甲,乙):
        '字符串和布尔按值比较，好复用上一份进度对象'
        if 甲 is 乙:
            return True
        if isinstance(甲,dict) is False or isinstance(乙,dict) is False or len(甲)!=len(乙):
            return False
        for 键,值 in 甲.items():
            if 键 not in 乙 or 乙[键]!=值:
                return False
        return True
