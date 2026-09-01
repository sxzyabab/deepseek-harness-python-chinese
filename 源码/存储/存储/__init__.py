"""存储枢纽（`ctx.storage`）：具名后端注册表加上已挂载的数据形态设施。

枢纽自身不做 IO——后端拥有介质，数据形态（首先是域层）拥有语义。公开面仅中文名。
"""
from ...依赖 import cordis#外部依赖胶水
服务=cordis.服务#Cordis 服务基类
from .错误 import 存储错误,存储错误码#存储错误与码表
from .注册表 import 后端注册表#后端注册表
from .后端 import 单元名正则,存储后端,键值面,键值单元,键值单元描述符#后端词汇
__all__=[#仅中文公开名
    '后端注册表','存储错误','存储错误码','单元名正则',
    '存储后端','键值面','键值单元','键值单元描述符',
    '存储后端服务键','存储','默认',
]#公开面结束

def 存储后端服务键(名称):#推导后端生命周期服务键
    """推导一个具名后端插件提供的 Cordis 生命周期服务键。"""
    return f'storage.backend.{名称}'#按后端名拼服务键

class 存储(服务):#存储枢纽
    """存储枢纽服务。后端在 `backend` 下注册；数据形态挂在各自的形态键下。"""
    def __init__(自身,上下文对象):#安装为 ctx.storage
        super().__init__(上下文对象,'storage')#登记服务名
        自身.backend=后端注册表()#具名后端表
        自身._形态={}#已挂载形态

    def mount(自身,形态,设施):#挂载一个数据形态设施
        """在枢纽上挂载一个数据形态设施。挂载是 effect：返回的 disposer 卸载该形态。"""
        if 形态 in 自身._形态:#该形态已挂载
            raise 存储错误('duplicate-mount',f"storage form '{形态}' is already mounted")#重复挂载
        自身._形态[形态]=设施#记下设施
        def 卸载():#卸载 disposer
            if 自身._形态.get(形态) is 设施:#仍是本次挂载
                del 自身._形态[形态]#卸下该形态
        return 卸载#返回 disposer

    def form(自身,形态):#解析一个已挂载的数据形态
        """解析一个已挂载的数据形态。"""
        if 形态 not in 自身._形态:#未挂载
            raise 存储错误('form-not-mounted',f"storage form '{形态}' is not mounted")#未挂载
        return 自身._形态[形态]#返回设施

    @property
    def domain(自身):#便捷访问 domain 形态
        """域数据形态；域层插件加载后才存在。"""
        return 自身.form('domain')#按 domain 键解析

默认=存储#默认导出枢纽类
