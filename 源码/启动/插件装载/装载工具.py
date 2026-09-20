"""智能体侧当前配置档装载工具；与 Web 控件共用同一服务。"""
import json
from ...模型后端.llm import 断言永不
from ...内核.工具 import 定义工具
from ...沙盒.沙盒.升级 import 批准升级
from ...工具.超时 import 若已中止则抛出

__all__=['依赖','应用']

依赖=['tools','pluginManager','sandboxPolicy']

def 应用(上下文):
    """登记一条装载工具：发现与四种持久动作。"""
    def 渲染(_参数,值):
        """文本块渲染。"""
        return [{'type':'text','text':值}]
    def 执行(参数,执行上下文):
        """经危险完全放开审批后执行装载动作。"""
        智能体=执行上下文['agent'] if 'agent' in 执行上下文 else None
        会话={} if 智能体 is None else {'session':智能体.session}
        策略=上下文.sandboxPolicy.解析(会话)
        生效=策略['mode'] if isinstance(策略,dict) else 策略.mode
        批准升级({
            'requestedMode':'danger-full-access',
            'effectiveMode':生效,
            'subject':'plugin management operation',
            'justification':'plugin_manager '+json.dumps(参数,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'. Profile changes persist across sessions; installed Host code runs outside the workspace sandbox.',
        },{
            'approver':getattr(上下文,'approval',None),
            'agent':智能体,
            'callId':执行上下文['callId'],
            'toolName':'plugin_manager',
            'signal':执行上下文['signal'] if 'signal' in 执行上下文 else None,
        })
        若已中止则抛出(执行上下文['signal'] if 'signal' in 执行上下文 else None)
        装载=上下文.pluginManager
        动作=参数['action']
        if 动作=='list_plugins' or 动作=='list_bundles':
            偏移=参数['offset'] if 'offset' in 参数 and 参数['offset'] is not None else 0
            限额=参数['limit'] if 'limit' in 参数 and 参数['limit'] is not None else 25
            if (isinstance(偏移,bool) or not isinstance(偏移,int) or 偏移<0 or
                    isinstance(限额,bool) or not isinstance(限额,int) or 限额<1 or 限额>100):
                raise ValueError('offset 必须是非负整数，limit 必须是 1 到 100 的整数')
            行表=装载.列出插件() if 动作=='list_plugins' else 装载.列出组合包()
            条目=行表[偏移:偏移+限额]
            下一=偏移+len(条目) if 偏移+len(条目)<len(行表) else None
            return json.dumps({'entries':条目,'total':len(行表),'nextOffset':下一},ensure_ascii=False,separators=(',',':'),allow_nan=False)
        if 动作=='set_plugin' or 动作=='set_bundle':
            if 'target' not in 参数 or 参数['target'] is None or 'enabled' not in 参数 or 参数['enabled'] is None:
                raise ValueError('必须提供 target 与 enabled')
            if 动作=='set_plugin':
                结果=装载.设置插件启用(参数['target'],参数['enabled'])
            else:
                结果=装载.设置组合包启用(参数['target'],参数['enabled'])
            return json.dumps(结果,ensure_ascii=False,separators=(',',':'),allow_nan=False)
        if 动作=='install_bundle':
            if 'target' not in 参数 or 参数['target'] is None:
                raise ValueError('必须提供目标包规格')
            选项={}
            if 'enabled' in 参数 and 参数['enabled'] is not None:
                选项['enabled']=参数['enabled']
            if 'approvedBuilds' in 参数 and 参数['approvedBuilds'] is not None:
                选项['approvedBuilds']=参数['approvedBuilds']
            return json.dumps(装载.安装组合包(参数['target'],选项),ensure_ascii=False,separators=(',',':'),allow_nan=False)
        if 动作=='remove_bundle':
            if 'target' not in 参数 or 参数['target'] is None:
                raise ValueError('必须提供目标组合包名')
            return json.dumps(装载.移除组合包(参数['target']),ensure_ascii=False,separators=(',',':'),allow_nan=False)
        return 断言永不(动作,'plugin_manager action')
    def 呈现调用(参数):
        """调用卡片。"""
        种类='read' if 参数['action'].startswith('list_') else 'other'
        return {'card':'generic','title':'Manage profile plugins','kind':种类,'rawInput':参数}
    上下文.tools.登记(定义工具({
        'name':'plugin_manager',#工具名（线协议）
        'description':'List plugins or bundles in the current profile, enable or disable them, install a bundle, or remove an installed bundle. Every action requires danger-full-access permission or approval for this call. Approval does not change the session permission mode. Changes affect every session in this profile. List first to obtain exact identifiers. Package installation can execute allowed build scripts. Live profiles apply changes immediately; startup profiles require restart.',#描述字面量
        'parameters':{
            'action':{'type':'string','required':True,'enum':['list_plugins','list_bundles','set_plugin','set_bundle','install_bundle','remove_bundle'],'description':'Management operation.'},
            'target':{'type':'string','description':'Plugin entry id, bundle package name, or installation spec, according to action.'},
            'enabled':{'type':'boolean','description':'Required for set operations; defaults to true for installation.'},
            'approvedBuilds':{'type':'array','items':{'type':'string'},'description':'For install_bundle: pass names from pendingBuilds only after the user explicitly approves running their install scripts in the conversation. This grants persistent permission for this profile.'},
            'offset':{'type':'number','description':'Zero-based list offset; defaults to 0.'},
            'limit':{'type':'number','description':'List page size, from 1 to 100; defaults to 25.'},
        },
        'output':{'schema':{'type':'string'},'render':渲染},
        'execute':执行,
        'presentCall':呈现调用,
    }))

#框架槽
inject=依赖
apply=应用
default=应用
