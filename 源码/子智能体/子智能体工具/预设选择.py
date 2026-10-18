'一条委托工具上、由部署方拥有的预设选择'

class 预设选择:
    '校验配置里的预设，并把模型输入收成允许的标识'
    def __init__(自身,配置):
        '允许清单有重复，或默认预设不在清单里，加载时失败'
        自身.配置=配置#部署配置
        自身.说明列表=[]#模型可见的预设说明
        允许=配置.get('allowedAgentPresets')#允许清单
        if 允许 is None:#不开放模型选择
            return#只保留默认
        if len(set(允许))!=len(允许):#有重复
            raise RuntimeError('tool-subagent: allowedAgentPresets contains duplicate preset ids')#拒绝
        默认=配置.get('agentPreset')#默认预设
        if 默认 is not None and 默认 not in 允许:#默认不在清单里
            raise RuntimeError('tool-subagent: agentPreset must be included in allowedAgentPresets')#拒绝

    @property
    def 已配置(自身):
        '是否需要预设服务，以及不继承父对话的提供方'
        return 自身.配置.get('agentPreset') is not None or 自身.配置.get('allowedAgentPresets') is not None#任一有值

    @property
    def 选项(自身):
        '模型参数里公布的预设标识'
        return 自身.配置.get('allowedAgentPresets')#没有则不开放

    @property
    def 描述(自身):
        '模型可见的选择说明'
        if 自身.配置.get('agentPreset') is None:#没有默认
            回退='Omit to inherit the parent agent\'s current preset.'#继承父预设
        else:#有默认
            回退='Omit to use '+自身.配置['agentPreset']+'.'#用这个默认
        后缀='' if len(自身.说明列表)==0 else ' Available presets: '+'; '.join(自身.说明列表)#已读到的说明
        return 'Agent preset for this child. '+回退+后缀#整段

    def 校验(自身,上下文):
        '发布工具前读取已配置的预设。激活是否合法由挂载时再验'
        预设服务=上下文.get('agentPresets')#预设服务
        if 预设服务 is None:#没有
            raise RuntimeError('tool-subagent: agent preset selection requires the agent-presets service')#拒绝
        标识集=[]#要读的标识
        if 自身.配置.get('agentPreset') is not None:#默认
            标识集.append(自身.配置['agentPreset'])#加上
        if 自身.配置.get('allowedAgentPresets') is not None:#清单
            标识集.extend(自身.配置['allowedAgentPresets'])#加上
        说明=[]#模型可见
        for 标识 in dict.fromkeys(标识集):#去重且保持顺序
            预设=预设服务.读取文档(标识)#文档
            if 自身.选项 is not None and 标识 in 自身.选项 and 预设.get('description') is not None:#清单里且有说明
                说明.append(标识+': '+预设['description'])#一条
        自身.说明列表=说明#记下

    def 断言提供方(自身,提供方):
        '继承父对话或不支持预设的提供方不能做独立选择'
        能力=提供方['capabilities'] if isinstance(提供方,dict) else 提供方.capabilities#能力
        继承=提供方['inheritsParentContext'] if isinstance(提供方,dict) else 提供方.inheritsParentContext#是否继承
        名称=提供方['name'] if isinstance(提供方,dict) else 提供方.name#提供方名
        支持=能力.get('agentPreset') if isinstance(能力,dict) else getattr(能力,'agentPreset',False)#是否支持
        if 自身.已配置 and (not 支持 or 继承):#配了但不能独立选
            raise RuntimeError('tool-subagent: provider "'+名称+'" does not support independent agent preset selection')#拒绝

    def 解析(自身,请求):
        '校验模型输入并套上部署默认。省略则继承父预设'
        标识=请求.get('agent_preset')#模型给的
        if 标识 is None:#省略
            return 自身.配置.get('agentPreset')#默认或继承
        if 自身.选项 is None:#没开放选择
            raise RuntimeError('agent_preset selection is disabled for this tool instance')#拒绝
        if not isinstance(标识,str) or 标识 not in 自身.选项:#不在清单
            raise RuntimeError('agent_preset must be one of: '+', '.join(自身.选项))#拒绝
        return 标识#选中的
