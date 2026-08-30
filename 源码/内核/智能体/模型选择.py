"""运行时入口共享的 Agent 作用域模型选择。

对齐上游 `agent/src/model-selection.ts`。公开面仅中文名；选择／组装／请求字段键保持上游 wire 名。
"""
from typing import NotRequired,TypedDict#可选字段与结构类型
from ...依赖 import cordis#外部依赖胶水

__all__=('模型选择','模型选择引用','安装模型选择')#仅中文公开名

class 模型选择(TypedDict):#一个在线智能体选定的完整提供方、模型与可选推理力度
    """一个在线智能体选定的完整提供方、模型与可选推理力度。"""
    provider:str#已注册的提供方路由
    model:str#提供方拥有的模型 id
    reasoningEffort:NotRequired[str]#适配器拥有的推理力度；缺省则用提供方/默认行为

class 模型选择引用(TypedDict):#可变模型选择，外加当前步骤捕获的值
    """可变模型选择，外加当前步骤捕获的值。"""
    current:object#下一进入提示词组装的步骤所选用的模型；可为 None
    assembled:object#当前步骤进入提示词组装时捕获的选择；可为 None

def 读(对象,名):#从映射或对象读取字段
    """从映射或对象读取字段。"""
    if isinstance(对象,dict):#映射
        return 对象[名]#映射键
    return getattr(对象,名)#对象属性

def 读可选(对象,名):#从映射或对象读取可选字段
    """从映射或对象读取可选字段。"""
    if isinstance(对象,dict):#映射
        return 对象.get(名)#映射键
    return getattr(对象,名,None)#对象属性

def 写(对象,名,值):#向映射或对象写入字段
    """向映射或对象写入字段。"""
    if isinstance(对象,dict):#映射
        对象[名]=值#映射键
        return#写完
    setattr(对象,名,值)#对象属性

def 拷贝记录(对象):#浅拷贝映射或对象的可枚举字段
    """浅拷贝映射或对象的可枚举字段。"""
    if isinstance(对象,dict):#映射
        return dict(对象)#映射拷贝
    结果={}#可枚举字段
    if hasattr(对象,'__dict__'):#实例
        结果.update(对象.__dict__)#实例字段
        return 结果#拷贝
    for 名 in dir(对象):#可见字段
        if 名.startswith('_'):#私有
            continue#跳过私有
        结果[名]=getattr(对象,名)#拷贝可见字段
    return 结果#拷贝

def 安装模型选择(智能体上下文,选择):#把可变选择接到组装与请求
    """把一份可变选择接到 Agent 作用域的提示词组装与请求路由。"""
    def 组装监听(_组装,_上下文,下一步):#组装时快照所选模型
        """组装时快照所选模型。"""
        所选=读可选(选择,'current')#读取当前选择
        组装结果=下一步()#继续组装
        if 是否thenable(组装结果):#返回承诺
            组装结果=组装结果.等待()#等待组装
        写(选择,'assembled',所选)#记下本步捕获
        if 所选 is None:#无选择
            return 组装结果#无选择则原样返回
        结果=拷贝记录(组装结果)#保留其余组装字段
        变量=拷贝记录(结果.get('variables') or {})#保留其余变量
        变量['provider']=读(所选,'provider')#写入提供方
        变量['model']=读(所选,'model')#写入模型
        结果['variables']=变量#覆盖变量
        return 结果#组装结果
    拆除组装=智能体上下文.on('system-prompt/assemble',组装监听)#组装监听
    def 请求监听(_载体,_载荷,下一步):#请求时套用已捕获选择
        """请求时套用已捕获选择。"""
        已解析=下一步()#先得到机器原配置
        if 是否thenable(已解析):#返回承诺
            已解析=已解析.等待()#等待配置
        所选=读可选(选择,'assembled')#使用组装时捕获的选择
        if 所选 is None:#无捕获
            return 已解析#无捕获则原样返回
        去掉=拷贝记录(已解析)#剥掉继承力度前先拷贝
        去掉.pop('reasoningEffort',None)#剥掉继承力度
        去掉['provider']=读(所选,'provider')#覆盖提供方
        去掉['model']=读(所选,'model')#覆盖模型
        力度=读可选(所选,'reasoningEffort')#捕获力度
        if 力度 is not None:#有力度
            去掉['reasoningEffort']=力度#有力度则带上
        return 去掉#套用后的配置
    拆除请求=智能体上下文.on('agent/request',请求监听)#请求监听
    def 拆除():#一并拆除两个监听器
        """一并拆除两个监听器。"""
        拆除组装()#拆除组装监听
        拆除请求()#拆除请求监听
    return 拆除#拆除器
