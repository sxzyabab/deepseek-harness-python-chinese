from .文案 import 命名空间,中文,英文#词典
from .服务 import 模型目录解析器#目录解析器
from .模型选择 import 模型选择#座位组件
from .目录 import 模型选择错误#本包异常

__all__=['依赖','应用','模型选择','模型目录解析器','命名空间','中文','英文','行键','描述于','选项于','选定于']#仅中文公开名

依赖=['commandUi','connection','locale','sessions','slots','remote']#依赖

def 行键(提供方,模型):#提供方/模型拼行键
    """不透明行键。"""
    return 提供方+'/'+模型#拼接

内置描述键={#内置模型描述键
    'deepseek-official/deepseek-v4-flash':'option.deepseekV4Flash.description',#flash
    'deepseek-official/deepseek-v4-pro':'option.deepseekV4Pro.description',#pro
}

def 描述于(提供方,模型,翻译):#内置描述本地化
    """线上描述仍是英文权威文案时才本地化。"""
    键名=行键(提供方,模型['id'] if 'id' in 模型 else '')#行键
    键=内置描述键[键名] if 键名 in 内置描述键 else None#内置键
    描述=模型['description'] if 'description' in 模型 else None#原描述
    if 键 is not None and 描述==英文[键]:#匹配英文权威
        return 翻译(键)#本地化
    return 描述#原样

def 选项于(目录,翻译):#目录 → 弹出选项
    """失败行列出但永不可选。"""
    行列表=[]#累积
    组列表=目录['groups'] if 'groups' in 目录 and 目录['groups'] is not None else []
    for 组 in 组列表:
        模型列表=组['models'] if 'models' in 组 and 组['models'] is not None else []
        组名=组['name'] if 'name' in 组 else None#组名
        for 模型 in 模型列表:
            描述=描述于(组['id'],模型,翻译)#本地化描述
            详=组名#组名
            if 描述 is not None:#有描述
                详=str(组名)+' · '+str(描述)#组名加描述
            项={'id':行键(组['id'],模型['id']),'label':模型['name'] if 'name' in 模型 else None,'detail':详}#行
            当前=目录['current'] if 'current' in 目录 and 目录['current'] is not None else {}#当前
            if ('provider' in 当前 and 当前['provider']==组['id']
                and 'model' in 当前 and 当前['model']==模型['id']):#当前
                项['active']=True#标 active
            行列表.append(项)#加
    失败列表=目录['failures'] if 'failures' in 目录 and 目录['failures'] is not None else []#失败提供方
    for 失败 in 失败列表:#失败提供方
        行列表.append({#失败行
            'id':'failure/'+str(失败['id'] if 'id' in 失败 else None),#失败键
            'label':失败['name'] if 'name' in 失败 else None,#名
            'detail':翻译('option.loadError',{'message':失败['message'] if 'message' in 失败 else None}),#错误文
        })
    return 行列表#全部

def 选定于(状态,标识):#行键 → 模型选定
    """失败行或过期 id 则为 None。"""
    组列表=状态['groups'] if 'groups' in 状态 and 状态['groups'] is not None else []
    for 组 in 组列表:
        模型列表=组['models'] if 'models' in 组 and 组['models'] is not None else []
        for 模型 in 模型列表:
            if 行键(组['id'],模型['id'])!=标识:#不匹配
                continue#跳过
            当前=状态['current'] if 'current' in 状态 else None#当前
            同路由=当前 is not None and 当前['provider']==组['id'] and 当前['model']==模型['id']#同路由
            推理=模型['reasoning'] if 'reasoning' in 模型 and 模型['reasoning'] is not None else {}#推理
            力度=当前['reasoningEffort'] if 同路由 and 当前 is not None and 'reasoningEffort' in 当前 else None#沿用
            if 力度 is None and 'defaultEffort' in 推理:#无
                力度=推理['defaultEffort']#默认
            选={'provider':组['id'],'model':模型['id']}#选定
            if 力度 is not None:#有力度
                选['reasoningEffort']=力度#带上
            return 选#还原
    return None#无效

def 应用(上下文):#安装模型选择浏览器半边
    """挂目录解析器、词典、/model 贡献与撰写器座位。"""
    def 登记词典():#登记中英文案
        """把模型选择词表写进 locale。"""
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})#词典
    上下文.副作用(登记词典,'ui-model-selection: dictionaries')#词典
    翻译=上下文.locale.bind(命名空间)#绑定词表
    def 阻断文案():#阻断原因
        """撰写器阻断文案。"""
        return 翻译('blocked.composer')#文案
    上下文.启动插件(模型目录解析器,{'blockReason':阻断文案})#目录服务
    def 挂模型命令(作用域):#等 commandUi 与目录
        """登记 /model popupSelect。"""
        命令=作用域.获取服务('commandUi')#命令 UI
        模型目录=作用域.modelDirectories#目录解析
        会话面=作用域.sessions#会话
        def 命令可用(会话):#是否可用
            """非子智能体。"""
            return 会话面.subagentAddress(会话.sessionId) is None#可用
        def 命令选项(会话):#弹出选项
            """拉目录展平。"""
            return _模型选项(模型目录,会话面,会话,翻译)#选项
        def 命令选定(选项,会话):#选定一行
            """提交选定。"""
            return _模型选定(模型目录,会话面,选项,会话,翻译)#选定
        def 登记():#登记贡献
            """/model 弹出选择。"""
            return 命令.register({#登记
                'name':'model',#命令名
                'label':lambda:翻译('command.label'),#命令标签
                'description':lambda:翻译('command.description'),#请求候选时解析描述
                'icon':'IconDataOutline16',#数据轮廓图标（primitives 组件名）
                'available':命令可用,#非子智能体
                'ui':{#弹出 UI
                    'kind':'popupSelect',#种类
                    'options':命令选项,#选项
                    'onSelect':命令选定,#选定
                },#ui 结束
            })#登记结束
        作用域.副作用(登记,'ui-model-selection: /model contribution')#贡献
    上下文.依赖启动(['commandUi','modelDirectories'],挂模型命令)#注入
    def 挂座位(作用域):#等槽位与目录
        """撰写器模型座位。"""
        模型目录=作用域.modelDirectories#目录
        会话面=作用域.sessions#会话
        def 登记():#登记座位
            """conversation.input.model。"""
            def 注入面(会话标识):#按会话解析
                """座位注入面。"""
                目录=模型目录.directoryFor(会话标识)#共享目录
                可用=会话面.subagentAddress(会话标识) is None#可用
                def 加载():#触发加载
                    """可用才拉。"""
                    if 可用:#可用
                        try:#拉
                            目录.load()#加载
                        except 模型选择错误:#失败反映在 store
                            pass
                def 选定(选):#提交选定
                    """可用才提交；成功 True。"""
                    if not 可用:#不可用
                        return False#立刻 false
                    try:#提交
                        目录.select(选)#选
                        return True#成功
                    except 模型选择错误:#失败
                        return False#失败
                return {'available':可用,'directory':目录.存储,'load':加载,'select':选定}#注入面
            return 作用域.slots.register({#登记
                'name':'conversation.input.model',#座位名
                'locale':命名空间,#词表
                'inject':注入面,#注入
            },模型选择)#组件
        作用域.slots.inject('conversation.input.model',登记)#等槽
    上下文.依赖启动(['slots','modelDirectories'],挂座位)#注入

def _模型选项(模型目录,会话面,会话,翻译):#拉选项行
    """子智能体禁止；否则目录展平。"""
    if 会话面.subagentAddress(会话.sessionId) is not None:#子智能体
        raise 模型选择错误('model selection is unavailable for addressed subagent sessions')#禁
    目录=模型目录.directoryFor(会话.sessionId).load()#加载已等待
    return 选项于(目录,翻译)#展平

def _模型选定(模型目录,会话面,选项,会话,翻译):#选定一行
    """行键还原后经同一目录提交。"""
    if 会话面.subagentAddress(会话.sessionId) is not None:#子智能体
        raise 模型选择错误('model selection is unavailable for addressed subagent sessions')#禁
    目录=模型目录.directoryFor(会话.sessionId)#共享目录
    选=选定于(目录.存储.getSnapshot(),选项['id'])#还原
    if 选 is None:#无效
        raise 模型选择错误("this provider's catalog failed to load — pick a model from a loaded group")#须已加载
    结果=目录.select(选)#提交已等待，交回 RemoteResult 形
    if 'ok' in 结果 and 结果['ok']:#成功
        return
    错=结果['error'] if 'error' in 结果 and 结果['error'] is not None else {}#错误
    码=错['code'] if 'code' in 错 else None#错误码
    if 码=='session/writer-held':#会话占用
        raise 模型选择错误(翻译('error.sessionInUse'))#占用文案
    raise 模型选择错误(str(码)+': '+str(错['message'] if 'message' in 错 else None))#其它失败

inject=依赖#框架槽
apply=应用#框架槽
