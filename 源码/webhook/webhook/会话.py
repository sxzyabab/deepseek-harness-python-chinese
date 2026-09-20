"""按已结算的 webhook 规则结果，在工作区侧创建会话。"""
import os,uuid#绝对路径与会话 id
from ...内核.会话 import 会话标识#会话 id 品牌
from ...模型后端.llm import 创建用户消息,错误链#用户消息与错误链

class 会话错误(Exception):
    """webhook 会话创建路径上的失败。"""

class 会话查询错误中止(会话错误):
    """webhook 创建路径上的取消。"""

def 已中止(信号):
    """信号是否已中止。无信号视为未中止。"""
    if 信号 is None:
        return False
    return 信号.is_set()#Event 置位即中止

def 若已中止则抛出(信号):
    """已中止则抛出会话创建取消。"""
    if 已中止(信号):
        raise 会话查询错误中止()

def 必填字符串(记录,字段):
    """从规则结果读取一个非空字符串字段。记录为 dict。"""
    if 字段 not in 记录:
        raise TypeError(f'webhook Session request {字段} must be a non-empty string')
    值=记录[字段]
    if (not isinstance(值,str)) or 值.strip()=='':
        raise TypeError(f'webhook Session request {字段} must be a non-empty string')
    return 值

def 解析请求(上下文,输入):
    """快照并校验同进程规则结果，再跨调用边界使用。输入为 dict。"""
    if 输入 is None or not isinstance(输入,dict):
        raise TypeError('webhook rule result must be null or a Session request object')
    工作区路径=必填字符串(输入,'workspacePath')
    if not os.path.isabs(工作区路径):
        raise TypeError(f'webhook Session request workspacePath must be absolute, got {repr(工作区路径)}')
    标题=必填字符串(输入,'title')
    提示=必填字符串(输入,'prompt')
    智能体预设=必填字符串(输入,'agentPreset')
    权限预设=必填字符串(输入,'permissionPreset')
    模型=输入['model'] if 'model' in 输入 else None
    if 模型 is not None and (not isinstance(模型,dict)):
        raise TypeError('webhook Session request model must be an object')
    if 模型 is None:
        已选=上下文.agentDefaultModel.currentSelection()
        智能体选项={'provider':已选['provider'],'model':已选['model']}
        模型选择=dict(已选)
    else:
        提供方=必填字符串(模型,'provider')
        模型号=必填字符串(模型,'model')
        最大token=模型['maxTokens'] if 'maxTokens' in 模型 else None
        if 最大token is not None and (isinstance(最大token,bool) or (not isinstance(最大token,int)) or 最大token<=0):
            raise TypeError('webhook Session request model.maxTokens must be a positive safe integer')
        智能体选项={'provider':提供方,'model':模型号}
        if 最大token is not None:
            智能体选项['maxTokens']=最大token
        模型选择={'provider':提供方,'model':模型号}
    return {
        'workspacePath':工作区路径,'title':标题,'prompt':提示,
        'agentPreset':智能体预设,'permissionPreset':权限预设,
        'modelSelection':模型选择,'agentOptions':智能体选项,
    }

def 报告回滚失败(上下文,主题,错误):
    """记录回滚失败，不替换原始失败。"""
    上下文.日志.警告(f'webhook: {主题} rollback failed: {错误链(错误)}')

def 安装初始模型选择(智能体上下文,选择):
    """在首次耐久请求头出现前应用创建时选择。选择为 dict。"""
    def 请求钩子(载荷,下一步):
        """首条请求前覆盖 provider/model；路由已变则不覆盖。"""
        已解析=下一步(载荷)
        智能体=载荷.get('agent') if isinstance(载荷,dict) else None
        if 智能体 is None:
            raise 会话错误('webhook Session setup has no Agent on agent/request')
        if 智能体.session.requestHeader() is not None:
            return 已解析
        if 'provider' not in 已解析 or 'model' not in 已解析 or 已解析['provider']!=选择['provider'] or 已解析['model']!=选择['model']:
            return 已解析
        下一=dict(已解析)
        下一.pop('reasoningEffort',None)#去掉继承的推理力度
        if 'reasoningEffort' in 选择 and 选择['reasoningEffort'] is not None:
            下一['reasoningEffort']=选择['reasoningEffort']
        return 下一
    智能体上下文.监听('agent/request',请求钩子)

def 创建Webhook会话(上下文,投递,规则号,请求,信号):
    """创建、附着、命名、配置并提示一条普通根会话。投递为 dict。"""
    已解析=解析请求(上下文,请求)
    上下文.permissionPresets.resolve(已解析['permissionPreset'])
    预设=上下文.agentPresets.resolve(已解析['agentPreset'])
    上下文.agentPresets.standingKeyFor(预设['id'])
    若已中止则抛出(信号)
    工作区=上下文.workspaceRegistry.create(已解析['workspacePath'])
    若已中止则抛出(信号)
    会话号=会话标识(f'webhook-{uuid.uuid4()}')
    def 安装预设(智能体上下文):
        """setup 回调：挂载预设并安装模型选择。"""
        安装预设与模型(上下文,智能体上下文,预设['id'],已解析['modelSelection'])
    句柄=上下文.agents.创建({
        'sessionId':会话号,'signal':信号,
        'meta':{'cwd':工作区.path,'agentPreset':预设['id']},
        'agentOptions':已解析['agentOptions'],
        'setup':安装预设,
    })
    已附着=False
    try:
        若已中止则抛出(信号)
        工作区.attachSession(会话号)
        已附着=True
        若已中止则抛出(信号)
        上下文.permissionPresets.set(句柄.智能体.session,已解析['permissionPreset'])
        上下文.sessionTitle.rename(句柄.智能体.session,已解析['title'])
        句柄.智能体.后续(创建用户消息({
            'content':[{'type':'text','text':已解析['prompt']}],
            'source':{
                'kind':'webhook',
                'provider':投递['kind'],
                'source':投递['source'],
                'deliveryId':投递['deliveryId'],
                'ruleId':规则号,
                'form':'notice',
                'summary':f"{投递['kind']} webhook handled by {规则号}",
            },
        }))
    except (会话错误,TypeError,OSError) as 错误:
        if 已附着:
            try:
                工作区.detachSession(会话号)
            except (会话错误,TypeError,OSError) as 回滚错误:
                报告回滚失败(上下文,f'Workspace detach for Session "{会话号}"',回滚错误)
        try:
            句柄.拆除()
        except (会话错误,TypeError,OSError) as 回滚错误:
            报告回滚失败(上下文,f'Agent disposal for Session "{会话号}"',回滚错误)
        raise 错误

def 安装预设与模型(上下文,智能体上下文,预设号,模型选择):
    """挂载智能体预设并安装初始模型选择。"""
    上下文.agentPresets.mount(智能体上下文,预设号)
    安装初始模型选择(智能体上下文,模型选择)
