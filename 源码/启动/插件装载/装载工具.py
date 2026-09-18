"""智能体侧当前配置档装载工具；与 Web 控件共用同一服务。"""
import json#结果序列化
from ...模型后端.llm import 断言永不#封闭联合穷尽
from ...内核.工具 import 定义工具#定义面向模型的工具
from ...沙盒.沙盒.升级 import 批准升级#沙箱升级审批
from ...工具.超时 import 若已中止则抛出#中止检查

__all__=['注入','应用']#仅中文公开名

注入=['tools','pluginManager','sandboxPolicy']#依赖服务键（线协议）

def 应用(上下文):
    """登记一条装载工具：发现与四种持久动作。"""
    def 渲染(_参数,值):
        """文本块渲染。"""
        return [{'type':'text','text':值}]#单文本块
    def 执行(参数,执行上下文):
        """经危险完全放开审批后执行装载动作。"""
        智能体=执行上下文['agent'] if 'agent' in 执行上下文 else None#智能体
        会话={} if 智能体 is None else {'session':智能体.session}#会话作用域
        策略=上下文.sandboxPolicy.解析(会话)#解析策略
        生效=策略['mode'] if isinstance(策略,dict) else 策略.mode#生效模式
        批准升级({#升级请求
            'requestedMode':'danger-full-access',#目标
            'effectiveMode':生效,#生效
            'subject':'plugin management operation',#主语
            'justification':'plugin_manager '+json.dumps(参数,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'. Profile changes persist across sessions; installed Host code runs outside the workspace sandbox.',#理由
        },{#审批配料
            'approver':getattr(上下文,'approval',None),#审批方
            'agent':智能体,#智能体
            'callId':执行上下文['callId'],#调用 id
            'toolName':'plugin_manager',#工具名
            'signal':执行上下文['signal'] if 'signal' in 执行上下文 else None,#信号
        })#批准结束
        若已中止则抛出(执行上下文['signal'] if 'signal' in 执行上下文 else None)#再查中止
        装载=上下文.pluginManager#装载服务
        动作=参数['action']#动作
        if 动作=='list_plugins' or 动作=='list_bundles':#列表
            偏移=参数['offset'] if 'offset' in 参数 and 参数['offset'] is not None else 0#偏移
            限额=参数['limit'] if 'limit' in 参数 and 参数['limit'] is not None else 25#页大小
            if (isinstance(偏移,bool) or not isinstance(偏移,int) or 偏移<0 or
                    isinstance(限额,bool) or not isinstance(限额,int) or 限额<1 or 限额>100):#非法
                raise Exception('offset must be a non-negative integer and limit must be an integer from 1 to 100')#拒绝
            行表=装载.列出插件() if 动作=='list_plugins' else 装载.列出组合包()#行
            条目=行表[偏移:偏移+限额]#页
            下一=偏移+len(条目) if 偏移+len(条目)<len(行表) else None#下一偏移
            return json.dumps({'entries':条目,'total':len(行表),'nextOffset':下一},ensure_ascii=False,separators=(',',':'),allow_nan=False)#JSON
        if 动作=='set_plugin' or 动作=='set_bundle':#启停
            if 'target' not in 参数 or 参数['target'] is None or 'enabled' not in 参数 or 参数['enabled'] is None:#缺参
                raise Exception('target and enabled are required')#拒绝
            if 动作=='set_plugin':#插件
                结果=装载.设置插件启用(参数['target'],参数['enabled'])#设置
            else:#组合包
                结果=装载.设置组合包启用(参数['target'],参数['enabled'])#设置
            return json.dumps(结果,ensure_ascii=False,separators=(',',':'),allow_nan=False)#JSON
        if 动作=='install_bundle':#安装
            if 'target' not in 参数 or 参数['target'] is None:#缺规格
                raise Exception('target package spec is required')#拒绝
            选项={}#安装选项
            if 'enabled' in 参数 and 参数['enabled'] is not None:#有启用
                选项['enabled']=参数['enabled']#写入
            if 'approvedBuilds' in 参数 and 参数['approvedBuilds'] is not None:#有批准构建
                选项['approvedBuilds']=参数['approvedBuilds']#写入
            return json.dumps(装载.安装组合包(参数['target'],选项),ensure_ascii=False,separators=(',',':'),allow_nan=False)#JSON
        if 动作=='remove_bundle':#移除
            if 'target' not in 参数 or 参数['target'] is None:#缺名
                raise Exception('target bundle name is required')#拒绝
            return json.dumps(装载.移除组合包(参数['target']),ensure_ascii=False,separators=(',',':'),allow_nan=False)#JSON
        return 断言永不(动作,'plugin_manager action')#穷尽
    def 呈现调用(参数):
        """调用卡片。"""
        种类='read' if 参数['action'].startswith('list_') else 'other'#读或其它
        return {'card':'generic','title':'Manage profile plugins','kind':种类,'rawInput':参数}#卡片
    上下文.tools.登记(定义工具({#登记 plugin_manager
        'name':'plugin_manager',#工具名（线协议）
        'description':'List plugins or bundles in the current profile, enable or disable them, install a bundle, or remove an installed bundle. Every action requires danger-full-access permission or approval for this call. Approval does not change the session permission mode. Changes affect every session in this profile. List first to obtain exact identifiers. Package installation can execute allowed build scripts. Live profiles apply changes immediately; startup profiles require restart.',#描述字面量
        'parameters':{#参数
            'action':{'type':'string','required':True,'enum':['list_plugins','list_bundles','set_plugin','set_bundle','install_bundle','remove_bundle'],'description':'Management operation.'},#动作
            'target':{'type':'string','description':'Plugin entry id, bundle package name, or installation spec, according to action.'},#目标
            'enabled':{'type':'boolean','description':'Required for set operations; defaults to true for installation.'},#启用
            'approvedBuilds':{'type':'array','items':{'type':'string'},'description':'For install_bundle: pass names from pendingBuilds only after the user explicitly approves running their install scripts in the conversation. This grants persistent permission for this profile.'},#批准构建
            'offset':{'type':'number','description':'Zero-based list offset; defaults to 0.'},#偏移
            'limit':{'type':'number','description':'List page size, from 1 to 100; defaults to 25.'},#限额
        },#参数结束
        'output':{'schema':{'type':'string'},'render':渲染},#输出
        'execute':执行,#执行
        'presentCall':呈现调用,#呈现
    }))#登记结束

#框架槽
inject=注入#Cordis 依赖
apply=应用#Cordis 入口
default=应用#Cordis 默认导出
