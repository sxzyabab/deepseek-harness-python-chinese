"""由独立 Runtime、Console 与 Source 后端装配的 Client realm 定义。"""
#对齐上游 worker/realms/client/index.ts

import uuid#随机id
from ...inspection.realm import 检查器realm描述,检查器realm上下文#realm类型
from .桥接 import 创建Client_realm桥#桥
from .运行时 import Client运行时后端#Runtime
from .控制台 import Client控制台后端#Console
from .源 import Client源后端#源
from .脚本 import Client脚本身份#脚本身份
from .调试器 import Client调试器能力#调试器

__all__=['Client检查器realm']#仅中文公开名

Client_Runtime操作=(#Client Runtime操作
    'evaluate','get-properties','call-function','await-promise',#常用
    'release-object','release-object-group','global-lexical-scope-names',#释放与词法
)#常量

def _支持(目标,能力类型):#是否支持能力
    """检查源能力列表。"""
    return any(候['type']==能力类型 for 候 in 目标['source']['capabilities'])#检查

class Client检查器realm:#Client检查器realm
    """经公共 Worker realm 模型暴露的活动 Client realm。"""
    def __init__(自身,目标,运行时路由,源路由):#构造
        """装配桥、描述与能力。"""
        自身._桥=创建Client_realm桥(目标,运行时路由,源路由)#桥
        自身.descriptor=检查器realm描述(#描述
            realmId=str(uuid.uuid4()),#realm id
            sourceId=目标['source']['sourceId'],#源id
            generation=目标['source']['generation'],#代数
            kind='client',#种类
            label=目标['source']['label'],#标签
        )#descriptor结束
        自身.context=检查器realm上下文(#合成上下文
            kind='synthetic',#种类
            id=目标['contextId'],#数字id
            uniqueId=目标['uniqueContextId'],#唯一id
            origin=目标['capability']['origin'],#origin
        )#context结束
        自身._脚本身份=Client脚本身份(目标['contextId'])#脚本身份
        自身.capabilities={#能力
            'runtime':list(Client_Runtime操作),#Runtime
            'console':['events','exceptions','clear'] if _支持(目标,'client-console') else [],#Console
            'sources':['catalog','content','source-map'] if _支持(目标,'client-sources') else [],#源
            'debugger':[],#调试器空
        }#capabilities结束

    @property
    def 目标(自身):#目标
        """本 realm 代表的活动源代数。"""
        return 自身._桥['target']#桥目标

    def 打开会话(自身):#打开会话
        """为一个 DevTools 连接打开一套隔离的 Client 后端。"""
        运行时会话id=str(uuid.uuid4())#Runtime会话
        运行时=Client运行时后端(自身.目标,运行时会话id,自身._桥['runtime'],自身._脚本身份)#Runtime
        控制台=Client控制台后端(自身.目标,运行时会话id,自身._桥['runtime'],自身._脚本身份) if _支持(自身.目标,'client-console') else None#Console
        源=Client源后端(自身.目标,str(uuid.uuid4()),自身._桥['sources'],自身._脚本身份) if _支持(自身.目标,'client-sources') else None#源
        def 关闭():#关闭
            """关闭会话后端。"""
            if 控制台 is not None:#有Console
                控制台.关闭()#关Console
            if 源 is not None:#有源
                源.关闭()#关源
            运行时.关闭()#关Runtime
        return {#会话
            'descriptor':自身.descriptor,#描述
            'context':自身.context,#上下文
            'runtime':{'state':'supported','backend':运行时},#Runtime
            'console':{'state':'unsupported','reason':'Client source does not provide Console events'} if 控制台 is None else {'state':'supported','backend':控制台},#Console
            'sources':{'state':'unsupported','reason':'Client source does not provide a script catalog'} if 源 is None else {'state':'supported','backend':源},#源
            'debugger':Client调试器能力(),#调试器
            'nativeDomains':{'state':'unsupported','reason':'Client realm has no native CDP transport'},#无原生
            'close':关闭,#关闭
        }#return结束
