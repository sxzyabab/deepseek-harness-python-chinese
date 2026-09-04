"""由连接本地 Node inspector 会话支撑的 Host realm 适配器。"""
#对齐上游 worker/realms/host/index.ts

import uuid#随机id
from ...inspection.realm import 检查器realm描述,检查器realm上下文#realm类型
from .桥接 import Host检查器会话#原生会话
from .运行时 import Host运行时后端#Runtime
from .控制台 import Host控制台后端#Console
from .源 import Host源后端#源
from .调试器 import Host调试器后端#调试器

__all__=['Host检查器realm']#仅中文公开名

Host_Runtime操作=(#Host Runtime操作
    'evaluate','get-properties','call-function','await-promise',#常用
    'release-object','release-object-group','global-lexical-scope-names',#释放与词法
)#常量

class Host检查器realm:#Host检查器realm
    """为每个 DevTools 连接打开一个原生 V8 会话的 Host realm 定义。"""
    def __init__(自身,标签):#构造
        """分配稳定描述与能力。"""
        自身.descriptor=检查器realm描述(#描述
            realmId=str(uuid.uuid4()),#realm id
            sourceId='host-runtime',#源id
            generation=str(uuid.uuid4()),#代数
            kind='host',#种类
            label=标签,#标签
        )#descriptor结束
        自身.context=检查器realm上下文(kind='native')#原生上下文
        自身.capabilities={#能力
            'runtime':list(Host_Runtime操作),#Runtime
            'console':['events','exceptions','clear'],#Console
            'sources':['catalog','content','source-map'],#源
            'debugger':['breakpoint','pause','resume','step','call-frame'],#调试器
        }#capabilities结束

    def 打开会话(自身):#打开会话
        """为一个 DevTools 连接打开原生 Host inspector 会话。"""
        目标=Host检查器会话(自身.descriptor.label)#原生会话
        运行时=Host运行时后端(目标)#Runtime
        控制台=Host控制台后端(目标,运行时)#Console
        源=Host源后端(目标)#源
        调试=Host调试器后端(目标,运行时)#调试器
        def 关闭():#关闭
            """按依赖逆序关闭。"""
            源.关闭()#关源
            调试.关闭()#关调试
            控制台.关闭()#关Console
            运行时.关闭()#关Runtime
            目标.关闭()#关会话
        return {#会话
            'descriptor':自身.descriptor,#描述
            'context':自身.context,#上下文
            'runtime':{'state':'supported','backend':运行时},#Runtime
            'console':{'state':'supported','backend':控制台},#Console
            'sources':{'state':'supported','backend':源},#源
            'debugger':{'state':'supported','backend':调试},#调试器
            'nativeDomains':{'state':'supported','backend':目标},#原生域
            'close':关闭,#关闭
        }#return结束
