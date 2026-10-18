'模型选择的浏览器面：/model 弹出和撰写器座位共用一份目录'
from . import 代际目录
from . import 文案
from . import 服务
from . import 槽位
from . import 提供方顺序
from . import 模型选择
from . import 目录

__all__=[
    '代际目录','文案','服务','槽位','提供方顺序','模型选择','目录',
    '命名空间','依赖','应用','行标识','会话标识',
]

命名空间='model'
依赖=['commandUi','locale','sessions','slots','remote','remote.session']

def 行标识(提供方,模型):
    '不透明行键。只用来对回已经加载的分组，不解析它'
    return str(提供方)+'/'+str(模型)

def 会话标识(会话):
    '命令界面传来的会话可能是对象，也可能是字典'
    if isinstance(会话,dict):
        return 会话['sessionId']
    return 会话.sessionId

def 应用(上下文,配置=None):
    '登记中英文案表和目录解析器，再挂上 /model 与撰写器座位'
    def 登记词典():
        '登记 model 的中英文案表。页面上的字不走英文表'
        return 上下文.locale.register(命名空间,{'zh':文案.中文,'en':文案.英文})
    上下文.副作用(登记词典,'ui-model-selection: dictionaries')
    上下文.启动插件(服务.模型目录解析器)
    def 弹出就绪(作用域,配置=None):
        '目录服务就绪后登记 /model'
        命令=作用域.commandUi
        模型目录服务=作用域.modelDirectories
        会话面=作用域.sessions
        def 登记():
            '把 model 命令交到命令界面'
            def 标签():
                '命令名'
                return '模型'
            def 说明():
                '命令说明'
                return '选择本会话使用的模型'
            def 可用(会话):
                '子智能体不提供这条命令'
                return 会话面.subagentAddress(会话标识(会话)) is None
            def 搜索文案():
                '弹出搜索框上的中文'
                return {
                    'placeholder':'搜索模型…',
                    'empty':'暂无可用模型',
                    'noResults':'没有匹配的模型。',
                }
            def 选项(会话,信号=None):
                '把目录展成弹出行。失败行看得见，但不能选'
                if 会话面.subagentAddress(会话标识(会话)) is not None:
                    raise Exception('model selection is unavailable for addressed subagent sessions')
                目录快照=模型目录服务.directoryFor(会话标识(会话)).load()
                行=[]
                for 组 in 提供方顺序.排列模型提供方(list(目录快照.get('groups') or [])):
                    组名='DeepSeek 账号' if 组.get('id')=='deepseek-account' else 组.get('name')
                    当前=目录快照.get('current')
                    for 模型 in 组.get('models') or []:
                        项={
                            'id':行标识(组.get('id'),模型.get('id')),
                            'label':模型.get('name'),
                            'group':{'name':组.get('id'),'label':组名},
                        }
                        if (当前 is not None and 当前.get('provider')==组.get('id')
                                and 当前.get('model')==模型.get('id')):
                            项['active']=True
                        行.append(项)
                for 失败 in 目录快照.get('failures') or []:
                    失败名='DeepSeek 账号' if 失败.get('id')=='deepseek-account' else 失败.get('name')
                    行.append({
                        'id':'failure/'+str(失败.get('id')),
                        'label':失败名,
                        'detail':'目录加载失败：'+str(失败.get('message')),
                    })
                return 行
            def 选定(选项行,会话):
                '把点中的行对回模型并提交'
                if 会话面.subagentAddress(会话标识(会话)) is not None:
                    raise Exception('model selection is unavailable for addressed subagent sessions')
                目录对象=模型目录服务.directoryFor(会话标识(会话))
                快照=目录对象.存储.getSnapshot()
                标识=选项行.get('id') if isinstance(选项行,dict) else None
                选定值=None
                for 组 in 快照.get('groups') or []:
                    for 模型 in 组.get('models') or []:
                        if 行标识(组.get('id'),模型.get('id'))!=标识:
                            continue
                        当前=快照.get('current')
                        同路由=(当前 is not None and 当前.get('provider')==组.get('id')
                            and 当前.get('model')==模型.get('id'))
                        if 同路由 and 当前.get('reasoningEffort') is not None:
                            力度=当前.get('reasoningEffort')
                        else:
                            推理=模型.get('reasoning')
                            力度=推理.get('defaultEffort') if isinstance(推理,dict) else None
                        选定值={'provider':组.get('id'),'model':模型.get('id')}
                        if 力度 is not None:
                            选定值['reasoningEffort']=力度
                        break
                    if 选定值 is not None:
                        break
                if 选定值 is None:
                    raise Exception("this provider's catalog failed to load — pick a model from a loaded group")
                结果=目录对象.select(选定值)
                if 结果.get('ok') is not True:
                    错=结果.get('error') or {}
                    if 错.get('code')=='session/writer-held':
                        raise Exception('当前会话已被占用，可能是其他正在运行的 DSH 导致的（如其他 dsh web、桌面端），请退出其他正在运行的 DSH 后重试。')
                    raise Exception(str(错.get('code'))+': '+str(错.get('message')))
            return 命令.register({
                'name':'model',
                'label':标签,
                'description':说明,
                'icon':模型选择.数据图标,
                'available':可用,
                'ui':{
                    'kind':'popupSelect',
                    'searchMode':'fuzzy-label',
                    'searchLabels':搜索文案,
                    'options':选项,
                    'onSelect':选定,
                },
            })
        作用域.副作用(登记,'ui-model-selection: /model contribution')
    上下文.依赖启动(['commandUi','modelDirectories'],弹出就绪)
    def 座位就绪(作用域,配置=None):
        '槽位声明之后挂上撰写器模型座位'
        模型目录服务=作用域.modelDirectories
        会话面=作用域.sessions
        def 登记座位():
            '登记 conversation.input.model'
            def 注入(会话标识值):
                '这场会话的目录、能否使用、加载和选定'
                目录对象=模型目录服务.directoryFor(会话标识值)
                能用=会话面.subagentAddress(会话标识值) is None
                def 加载():
                    '能选模型才加载。失败留在目录快照上'
                    if 能用 is not True:
                        return
                    try:
                        目录对象.load()
                    except Exception as 加载错误:
                        return
                def 选定模型(选择):
                    '不能选模型时不提交'
                    if 能用:
                        return 目录对象.select(选择)
                    return None
                return {
                    'available':能用,
                    'directory':目录对象.存储,
                    'load':加载,
                    'select':选定模型,
                }
            return 作用域.slots.register({
                'name':'conversation.input.model',
                'locale':命名空间,
                'inject':注入,
            },模型选择.渲染模型选择)
        作用域.slots.inject('conversation.input.model',登记座位)
    上下文.依赖启动(['slots','modelDirectories'],座位就绪)

inject=依赖
apply=应用
