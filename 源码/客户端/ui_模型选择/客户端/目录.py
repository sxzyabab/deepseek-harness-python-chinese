'每个会话一份模型目录。两条入口共用它'

from ...存储 import 创建快照存储

__all__=['模型目录']

class 模型目录:
    '共享 Host 目录和持久选定投影，经同一次 selectModel 提交'
    def __init__(自身,会话线,会话标识,可用,目录账本,投影源,是空白,记录=None):
        '订上目录和投影，并立刻按它们算一版快照'
        自身.会话线=会话线
        自身.会话标识=会话标识
        自身.可用=可用
        自身.目录账本=目录账本
        自身.投影源=投影源
        自身.是空白=是空白
        自身.记录=记录
        自身.存储=创建快照存储({
            'current':None,
            'routable':None,
            'groups':[],
            'failures':[],
            'status':'idle',
            'pending':None,
            'error':None,
        })
        自身.世代=0
        自身.已拆除=False
        自身.卸目录=目录账本.存储.subscribe(自身.同步输入)
        自身.卸投影=投影源.subscribe(自身.同步输入)
        自身.同步输入()

    def load(自身):
        '确保共享目录已加载，并交出重算后的快照'
        自身.断言可用()
        自身.目录账本.load()
        自身.同步输入()
        return 自身.存储.getSnapshot()

    def select(自身,选定):
        '提交完整选定。过期应答不再改存储，失败写在快照上也原样返回'
        自身.断言可用()
        先前=自身.存储.getSnapshot()['current']
        先前力度=None
        if 先前 is not None:
            if 先前.get('reasoningEffort') is not None:
                先前力度=先前['reasoningEffort']
            else:
                先前推理=自身.目录账本.reasoningFor(先前)
                if isinstance(先前推理,dict):
                    先前力度=先前推理.get('defaultEffort')
        下一推理=自身.目录账本.reasoningFor(选定)
        下一力度=选定.get('reasoningEffort')
        if 下一力度 is None and isinstance(下一推理,dict):
            下一力度=下一推理.get('defaultEffort')
        自身.世代+=1
        本轮=自身.世代
        def 标选定(态):
            '标成正在选定'
            态['status']='selecting'
            态['pending']=选定
            态['error']=None
        自身.存储.update(标选定)
        载荷={
            'sessionId':自身.会话标识,
            'provider':选定['provider'],
            'model':选定['model'],
        }
        if 选定.get('reasoningEffort') is not None:
            载荷['reasoningEffort']=选定['reasoningEffort']
        结果=自身.会话线.selectModel(载荷)
        if 自身.已拆除 or 本轮!=自身.世代:
            if 结果.get('ok') is True:
                return {'ok':True,'value':None}
            return 结果
        if 结果.get('ok') is not True:
            错=结果.get('error') or {}
            文=str(错.get('code'))+': '+str(错.get('message'))
            def 写错(态):
                '标成选定失败'
                态['status']='error'
                态['pending']=None
                态['error']=文
            自身.存储.update(写错)
            return 结果
        if 先前 is not None and 自身.记录 is not None:
            从处=str(先前['provider'])+'/'+str(先前['model'])
            到处=str(选定['provider'])+'/'+str(选定['model'])
            空白=自身.是空白() is True
            if 从处!=到处:
                属性={'switch_from':从处,'switch_to':到处}
                if 空白 is not True:
                    属性['session_id']=自身.会话标识
                自身.记录('model_switch',属性)
            if 从处==到处 and 先前力度!=下一力度:
                属性={
                    'model_name':到处,
                    'switch_from':'default' if 先前力度 is None else 先前力度,
                    'switch_to':'default' if 下一力度 is None else 下一力度,
                }
                if 空白 is not True:
                    属性['session_id']=自身.会话标识
                自身.记录('thinking_level_switch',属性)
        def 写好(态):
            '选定成功，清掉在飞标记'
            态['status']='ready'
            态['pending']=None
            态['error']=None
        自身.存储.update(写好)
        自身.同步输入()
        return {'ok':True,'value':None}

    def resetConnected(自身):
        '作废上一代 Host 还在飞的选定，再按当前目录和投影重算'
        if 自身.已拆除:
            return
        自身.世代+=1
        def 清选定中(态):
            '选定中回到空闲'
            if 态['status']=='selecting':
                态['status']='idle'
            态['pending']=None
            态['error']=None
        自身.存储.update(清选定中)
        自身.同步输入()

    def dispose(自身):
        '会话拆掉之后，迟到的应答不能再写快照'
        自身.已拆除=True
        自身.卸投影()
        自身.卸目录()

    def 断言可用(自身):
        '子智能体会话不能走模型 RPC'
        if 自身.可用() is not True:
            raise Exception('model selection is unavailable for addressed subagent sessions')

    def 同步输入(自身):
        '按共享目录和持久投影重算这份快照'
        if 自身.已拆除:
            return
        目录态=自身.目录账本.存储.getSnapshot()
        投影值=自身.投影源.getSnapshot()
        投影=None if 投影值 is None else 投影值
        目录值=目录态.get('value')
        打算=None
        if isinstance(投影,dict) and 投影.get('next') is not None:
            打算=投影['next']
        elif isinstance(目录值,dict):
            打算=目录值.get('default')
        推理=None if 打算 is None else 自身.目录账本.reasoningFor(打算)
        力度=None
        if isinstance(打算,dict) and 打算.get('reasoningEffort') is not None:
            力度=打算['reasoningEffort']
        elif isinstance(推理,dict):
            力度=推理.get('defaultEffort')
        留下力度=None
        if 力度 is not None:
            留下力度=力度
            if isinstance(推理,dict):
                for 级 in 推理.get('efforts') or []:
                    if 级.get('id')==力度:
                        留下力度=级.get('name')
                        break
        现态=自身.存储.getSnapshot()
        if 目录态.get('status')!='ready' or 目录值 is None or 投影 is None:
            下一={
                'current':None if 目录值 is None else 现态.get('current'),
                'routable':None,
                'groups':[] if not isinstance(目录值,dict) else 目录值.get('groups') or [],
                'failures':[] if not isinstance(目录值,dict) else 目录值.get('failures') or [],
                'status':'error' if 目录态.get('status')=='error' else 'loading',
                'pending':现态.get('pending'),
                'error':目录态.get('error'),
            }
            if 留下力度 is not None:
                下一['retainedEffort']=留下力度
            自身.存储.set(下一)
            return
        选定=投影.get('next') if 投影.get('next') is not None else 目录值.get('default')
        可路由=False
        if isinstance(选定,dict):
            for 组 in 目录值.get('groups') or []:
                if 组.get('id')!=选定.get('provider'):
                    continue
                for 模型 in 组.get('models') or []:
                    if 模型.get('id')==选定.get('model'):
                        可路由=True
        下一={
            'current':选定,
            'routable':可路由,
            'groups':目录值.get('groups') or [],
            'failures':目录值.get('failures') or [],
            'status':'selecting' if 现态.get('status')=='selecting' else 'ready',
            'pending':现态.get('pending'),
            'error':None,
        }
        if 留下力度 is not None:
            下一['retainedEffort']=留下力度
        自身.存储.set(下一)
