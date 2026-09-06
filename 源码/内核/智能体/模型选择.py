"""运行时入口共享的 Agent 作用域模型选择。

对齐上游 `agent/src/model-selection.ts`。选择／组装／请求字段键保持上游 wire 名。
"""
from typing import NotRequired,TypedDict#可选字段与结构类型

__all__=('模型选择','模型选择引用','安装模型选择')#仅中文公开名

class 模型选择(TypedDict):
    """一个在线智能体选定的完整提供方、模型与可选推理力度。"""
    provider:str#已注册的提供方路由
    model:str#提供方拥有的模型 id
    reasoningEffort:NotRequired[str]#适配器拥有的推理力度

class 模型选择引用(TypedDict):
    """可变模型选择，外加当前步骤捕获的值。"""
    current:object#下一进入提示词组装的步骤所选用的模型
    assembled:object#当前步骤进入提示词组装时捕获的选择

def 安装模型选择(智能体上下文,选择):
    """把一份可变选择接到 Agent 作用域的提示词组装与请求路由。"""
    def 组装监听(_组装,_上下文,下一步):
        """组装时快照所选模型。选择是 dict。"""
        所选=选择['current'] if 'current' in 选择 else None#读取当前选择
        组装结果=下一步()#组装已是同步
        选择['assembled']=所选#记下本步捕获
        if 所选 is None:
            return 组装结果#无选择则原样返回
        结果=dict(组装结果)#保留其余组装字段
        变量源=结果['variables'] if 'variables' in 结果 and 结果['variables'] is not None else {}#其余变量
        变量=dict(变量源)#拷贝变量
        变量['provider']=所选['provider']#写入提供方
        变量['model']=所选['model']#写入模型
        结果['variables']=变量#覆盖变量
        return 结果#组装结果
    拆除组装=智能体上下文.监听('system-prompt/assemble',组装监听)#组装监听
    def 请求监听(_载体,_载荷,下一步):
        """请求时套用已捕获选择。"""
        已解析=下一步()#配置已是同步
        所选=选择['assembled'] if 'assembled' in 选择 else None#使用组装时捕获的选择
        if 所选 is None:
            return 已解析#无捕获则原样返回
        去掉=dict(已解析)#剥掉继承力度前先拷贝
        去掉.pop('reasoningEffort',None)#剥掉继承力度
        去掉['provider']=所选['provider']#覆盖提供方
        去掉['model']=所选['model']#覆盖模型
        力度=所选['reasoningEffort'] if 'reasoningEffort' in 所选 else None#捕获力度
        if 力度 is not None:
            去掉['reasoningEffort']=力度#有力度则带上
        return 去掉#套用后的配置
    拆除请求=智能体上下文.监听('agent/request',请求监听)#请求监听
    def 拆除():
        """一并拆除两个监听器。"""
        拆除组装()#拆除组装监听
        拆除请求()#拆除请求监听
    return 拆除#拆除器
