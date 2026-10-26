'一个委派工具为每个任务选择已配置的外部提供方'
from ...依赖.schemastery import 字典字段,字符串字段
from ...内核.工具 import 定义工具
from ...基础设施.js特性 import PromiseEX as 期约

__all__=['名称','依赖','配置','应用']

名称='experimental-tool-subagent-oar'
依赖=['tools','subagents']

def 归一配置(数据):
    '补上工具名默认值。providers 必须是非空别名表'
    if not isinstance(数据,dict):
        raise TypeError('subagent_oar config must be an object')
    内层=字典字段(字典结构={
        'providers':字典字段(键值结构=(字符串字段(),字符串字段(最小长度=1))),
        'toolName':字符串字段(最小长度=1,默认值='subagent_oar'),
    })
    内层.校验数据(数据)
    if 'providers' not in 数据 or not isinstance(数据['providers'],dict):
        raise TypeError('subagent_oar: providers must contain at least one non-empty runtime alias')
    提供方表=dict(数据['providers'])
    if len(提供方表)==0 or any((not isinstance(别名,str)) or len(别名.strip())==0 for 别名 in 提供方表):
        raise TypeError('subagent_oar: providers must contain at least one non-empty runtime alias')
    for 值 in 提供方表.values():
        if not isinstance(值,str) or len(值)==0:
            raise TypeError('subagent_oar: providers must contain at least one non-empty runtime alias')
    工具名=数据['toolName'] if 'toolName' in 数据 and 数据['toolName'] is not None else 'subagent_oar'
    if not isinstance(工具名,str) or len(工具名)==0:
        raise TypeError('subagent_oar: toolName must be a non-empty string')
    return {'providers':提供方表,'toolName':工具名}

class 配置模式:
    '部署方持有的运行时别名与面向模型的工具名'
    def 校验数据(自身,数据=None):
        '加载前归一化。缺省工具名是 subagent_oar'
        if 数据 is None:
            数据={}
        return 归一配置(数据)

配置=配置模式()

def 取(对象,键):
    '执行上下文和激活回执都可能是字典'
    if isinstance(对象,dict):
        return 对象[键] if 键 in 对象 else None
    return getattr(对象,键,None)

def 提供方可续或继承(提供方):
    '一次性且上下文独立才允许。中文提供方用中文属性'
    if 提供方 is None:
        return False
    准备=getattr(提供方,'准备可续运行',None)
    if 准备 is None:
        准备=getattr(提供方,'prepareContinuable',None)
    if 准备 is not None:
        return True
    if hasattr(提供方,'继承父上下文'):
        return bool(提供方.继承父上下文)
    return bool(getattr(提供方,'inheritsParentContext',False))

def 应用(上下文,配置值):
    '注册一个工具，每次调用选择一个已配置的外部提供方'
    已解析=配置值 if isinstance(配置值,dict) and 'toolName' in 配置值 else 归一配置(配置值 or {})
    提供方表=dict(已解析['providers'])
    if len(提供方表)==0 or any(len(别名.strip())==0 for 别名 in 提供方表):
        raise ValueError('subagent_oar: providers must contain at least one non-empty runtime alias')
    工具名=已解析['toolName']
    def 执行(参数,执行):
        '启动一次父投递的激活，返回子标识'
        盒=期约()
        父=取(执行,'agent')
        if 父 is None:
            盒.拒绝(ValueError('subagent_oar requires a calling agent'))
            return 盒
        提供方名=提供方表[参数['runtime']]
        提供方=上下文.subagents.取提供方(提供方名)
        if 提供方可续或继承(提供方):
            盒.拒绝(ValueError('subagent_oar requires a one-shot provider with independent conversation context'))
            return 盒
        请求={'parent':父,'prompt':[{'type':'text','text':参数['prompt']}]}
        if 'cwd' in 参数 and 参数['cwd'] is not None:
            请求['cwd']=参数['cwd']
        def 已启动(激活):
            '回执里的 childId 就是面向模型的子标识'
            盒.解决({'kind':'activation','subagentId':取(激活,'childId')})
        上下文.subagents.启动激活({
            'provider':提供方名,
            'label':参数['description'],
            'request':请求,
            'signal':取(执行,'signal'),
            'delivery':'parent',
        }).然后(已启动,盒.拒绝)
        return 盒
    def 呈现调用(参数):
        '待处理卡片用任务描述'
        return {'card':'generic','title':参数['description'],'rawInput':参数}
    def 渲染启动(_参数,值):
        '面向模型的启动回执保持英文'
        return [{'type':'text','text':'started subagent '+str(值['subagentId'])}]
    def 并发安全():
        '各次委派互不占用同一子上下文'
        return True
    上下文.tools.登记(定义工具({
        'name':工具名,
        'description':'Delegate a self-contained task to a configured external agent. Choose its runtime for each call. '
            +'The child works in its own context and does not see this conversation. '
            +'This tool returns a child id; a later completion notice includes its final answer. '
            +'The child does not accept follow-up messages. Start independent tasks together and continue useful work while they run. '
            +'When only waiting for their results remains, end your turn instead of polling.',
        'parameters':{
            'runtime':{
                'type':'string',
                'required':True,
                'enum':list(提供方表.keys()),
                'description':'Configured external runtime for this task.',
            },
            'description':{
                'type':'string',
                'required':True,
                'description':'A short description of the delegated task, for display.',
            },
            'prompt':{
                'type':'string',
                'required':True,
                'description':'The complete, self-contained task. Include all context the external agent needs.',
            },
            'cwd':{
                'type':'string',
                'description':'Initial child working directory. Relative paths use your current directory; omission inherits it.',
            },
        },
        'output':{
            'schema':{
                'type':'object',
                'additionalProperties':False,
                'properties':{
                    'kind':{'type':'string','required':True,'const':'activation'},
                    'subagentId':{'type':'string','required':True},
                },
            },
            'render':渲染启动,
        },
        'isConcurrencySafe':并发安全,
        'execute':执行,
        'presentCall':呈现调用,
    }))

name=名称
inject=依赖
Config=配置
apply=应用
