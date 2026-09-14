import re#正则
from .DeepSeek模型编辑器 import 校验DeepSeek模型#模型门闩
from .密钥判定 import 密钥失败#密钥门闩
from .编辑器页脚 import 编辑器页脚#页脚
from .模型列表编辑器 import 模型列表编辑器#模型列表
from .存储 import 推导密钥引用,错误文案#存储辅助

__all__=['命名空间','路由模式','自定义提供方卡片','校验路由']#仅中文公开名

命名空间='llm-pi-ai'#手声明写入的设置 ns
路由模式=re.compile(r'^[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z',re.ASCII)#可作设置键与凭证词干

def 校验路由(路由,已占):
    """返回阻挡键；可提交则为 None。"""
    if 路由=='':#空
        return 'routeRequired'#必填
    if 路由模式.match(路由) is None:#不合规则
        return 'routeInvalid'#非法
    占用=已占 if 已占 is not None else []#占用表
    if 路由 in 占用:#碰撞
        return 'routeTaken'#占用
    return None#可提交

class 自定义提供方卡片:#自定义提供方创建卡
    """选路由 id；档案不存在直至提交。"""
    def __init__(自身,属性):#构造
        """记下打开时修订与本地草稿。"""
        自身.属性=属性#合成 props
        自身.打开于=属性['revision'] if 'revision' in 属性 else None#打开时修订
        自身.路由=''#路由 id
        自身.显示名=''#显示名
        自身.基址=''#端点
        协议列表=list(属性['protocols']) if 'protocols' in 属性 and 属性['protocols'] is not None else []#协议选项
        自身.协议=协议列表[0] if len(协议列表)>0 else ''#默认协议
        自身.密钥草稿=''#只写密钥
        自身.模型列表=[]#模型草稿
        自身.忙=False#在飞
        自身.失败=None#失败文案
        自身.已提交=False#档案已落地
        自身.列表编辑器=None#内嵌列表
        自身.页脚=None#页脚

    def 更新(自身,属性):#props 变更
        """刷新 props；打开修订不变。"""
        自身.属性=属性#最新

    def 改模型列表(自身,下一):#列表变更
        """写入模型草稿。"""
        自身.模型列表=list(下一)#覆盖

    def 改路由(自身,文):#改路由
        """写入路由草稿。"""
        自身.路由=文#覆盖

    def 改显示名(自身,文):#改显示名
        """写入显示名草稿。"""
        自身.显示名=文#覆盖

    def 改基址(自身,文):#改端点
        """写入端点草稿。"""
        自身.基址=文#覆盖

    def 改协议(自身,文):#改协议
        """写入协议草稿。"""
        自身.协议=文#覆盖

    def 改密钥(自身,文):#改密钥
        """写入密钥草稿。"""
        自身.密钥草稿=文#覆盖

    def 点取消(自身):#取消创建
        """关闭；已提交则视为已变更。"""
        关闭=自身.属性['onClose'] if 'onClose' in 自身.属性 else None#关闭
        if 关闭 is not None:#有
            关闭(自身.已提交)#通知

    def 提示(自身):#表单级提示
        """就绪或已有失败/密钥/路由门闩则不提示。"""
        翻译=自身.属性['t']#文案
        占用=list(自身.属性['taken']) if 'taken' in 自身.属性 and 自身.属性['taken'] is not None else []#已占
        路由非法=len(自身.路由)>0 and 路由模式.search(自身.路由) is None#非法
        路由占用=自身.路由 in 占用#占用
        模型失败=校验DeepSeek模型(自身.模型列表)#模型
        密钥错=密钥失败(自身.密钥草稿)#密钥
        就绪=(len(自身.路由)>0 and not 路由非法 and not 路由占用
            and len(自身.基址)>0 and len(自身.模型列表)>0 and 模型失败 is None
            and 密钥错 is None)#就绪
        if (自身.失败 is not None or 就绪 or 密钥错 is not None
            or len(自身.路由)==0 or 路由非法 or 路由占用):#无提示
            return None#无
        if len(自身.基址)==0:#缺端点
            return 翻译('customNeedsBaseUrl')#提示
        if 模型失败 is not None:#坏行
            return f"{翻译('model')} {模型失败['index']+1}: {翻译(模型失败['key'])}"#行文案
        return 翻译('customNeedsModels')#缺模型

    def 创建一次(自身):#写线一次
        """返回失败文案或 None。"""
        接口=自身.属性['api']#API
        密钥值=自身.密钥草稿.strip()#去空白
        引用=推导密钥引用(自身.路由)#凭证引用
        存密钥=len(密钥值)>0#是否存密钥
        if not 自身.已提交:#尚未落地档案
            档={#档案
                'api':自身.协议,'baseURL':自身.基址,
                'models':[dict(模) for 模 in 自身.模型列表],
            }#基础
            if len(自身.显示名)>0:#有显示名
                档['displayName']=自身.显示名#带上
            if 存密钥:#记引用
                档['apiKeyEnv']=引用#带上
            响应=接口.settings.mutate({#创建
                'ns':命名空间,
                'ops':[{'op':'set','path':['providers',自身.路由],'value':档}],
                'expectedRevision':自身.打开于,
            }).等待()#变更
            结果=响应['result']#结果
            if 结果['ok'] is not True:#失败
                错=结果['error'] if 'error' in 结果 else None#错误
                return 错['message'] if 错 is not None and 'message' in 错 else None#文案
            自身.已提交=True#档案落地
        if 存密钥:#存密钥
            存=接口.credentials.set({'ref':引用,'value':密钥值}).等待()#set
            存结果=存['result']#结果
            if 存结果['ok'] is not True:#失败
                错=存结果['error'] if 'error' in 存结果 else None#错误
                return 错['message'] if 错 is not None and 'message' in 错 else None#文案
        return None#成功

    def 创建(自身):#提交创建
        """成功则 onClose(True)。"""
        自身.忙=True#在飞
        自身.失败=None#清错
        try:#写线
            结果=自身.创建一次()#一次
            if 结果 is not None:#失败
                自身.失败=结果#挂文案
                return#停
            关闭=自身.属性['onClose'] if 'onClose' in 自身.属性 else None#关闭
            if 关闭 is not None:#有
                关闭(True)#已变更
        except Exception as 错误:#传输拒绝；RPC 异常契约未定
            自身.失败=错误文案(错误)#文案
        finally:#收尾
            自身.忙=False#闲

    def 渲染(自身):#结构化视图
        """创建表单投影。"""
        翻译=自身.属性['t']#文案
        占用=list(自身.属性['taken']) if 'taken' in 自身.属性 and 自身.属性['taken'] is not None else []#已占
        协议列表=list(自身.属性['protocols']) if 'protocols' in 自身.属性 and 自身.属性['protocols'] is not None else []#协议
        只读=bool(自身.属性['readOnly']) if 'readOnly' in 自身.属性 else False#只读
        禁用=只读 or 自身.忙#禁用
        档案禁用=禁用 or 自身.已提交#档案字段锁
        路由非法=len(自身.路由)>0 and 路由模式.search(自身.路由) is None#非法
        路由占用=自身.路由 in 占用#占用
        模型失败=校验DeepSeek模型(自身.模型列表)#模型
        密钥错=密钥失败(自身.密钥草稿)#密钥
        密钥值=自身.密钥草稿.strip()#去空白
        就绪=(len(自身.路由)>0 and not 路由非法 and not 路由占用
            and len(自身.基址)>0 and len(自身.模型列表)>0 and 模型失败 is None
            and 密钥错 is None)#就绪
        探测={#列表探询
            'settingsNs':命名空间,'baseURL':自身.基址,'api':自身.协议,
        }#基础
        if len(密钥值)>0:#有密钥
            探测['apiKey']=密钥值#带上
        自身.列表编辑器=模型列表编辑器({#内嵌列表
            'models':自身.模型列表,
            'onChange':自身.改模型列表,
            'probe':探测,
            'probeBlocked':'keyBlankNew' if 密钥错=='keyBlank' else 密钥错,
            'api':自身.属性['api'] if 'api' in 自身.属性 else None,
            't':翻译,
            'disabled':档案禁用,
        })#列表结束
        自身.页脚=编辑器页脚({#页脚
            't':翻译,'busy':自身.忙,'submitDisabled':禁用 or not 就绪,
            'submitLabel':'create','submitBusyLabel':'creating',
            'onCancel':自身.点取消,
            'onSubmit':自身.创建,
        })#页脚结束
        if 路由非法 or 路由占用:#路由错误
            路由提示={'kind':'error','text':翻译('customRouteInvalid' if 路由非法 else 'customRouteTaken')}#错误
        else:#引导
            路由提示={'kind':'hint','text':翻译('customRouteHint')}#提示
        密钥失败文案=None#密钥下错误
        if 密钥错 is not None:#有错
            密钥失败文案=翻译('keyBlankNew' if 密钥错=='keyBlank' else 密钥错)#文案
        显示占位=翻译('customDisplayName') if len(自身.路由)==0 else 自身.路由#显示名占位
        return {#视图
            'type':'custom-provider-card',#类型
            'title':翻译('customTitle'),#标题
            'route':{'label':翻译('customRoute'),'value':自身.路由,'placeholder':'acme-gateway','disabled':档案禁用,'onChange':自身.改路由,'hint':路由提示},#路由
            'displayName':{'label':翻译('customDisplayName'),'value':自身.显示名,'placeholder':显示占位,'disabled':档案禁用,'onChange':自身.改显示名},#显示名
            'baseURL':{'label':翻译('baseUrl'),'value':自身.基址,'placeholder':'https://gateway.example/v1','disabled':档案禁用,'onChange':自身.改基址},#端点
            'api':{'label':翻译('customApi'),'value':自身.协议,'choices':协议列表,'disabled':档案禁用,'onChange':自身.改协议},#协议
            'key':{'label':翻译('keyInput'),'value':自身.密钥草稿,'placeholder':翻译('keyPlaceholder'),'disabled':禁用,'failure':密钥失败文案,'onChange':自身.改密钥},#密钥
            'models':自身.列表编辑器(),#模型列表
            'failure':自身.失败,#失败
            'hint':自身.提示(),#表单提示
            'footer':自身.页脚(),#页脚
            'cssModule':'模型分区.module.css',#样式
        }#视图结束

    def __call__(自身,属性=None):#组件调用形
        """对齐 React 调用。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
