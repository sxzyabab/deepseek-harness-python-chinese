"""spill 存储能力 seam 的 Service Definition（`ctx.spillStore`）：抽象服务定义溢出后端做什么——持久化工具过大的文本并返回面向模型的定位器加检索指引——不说怎么做。实现子类化溢出存储并注册为 `spillStore` 服务；`@deepseek-ai/dsh-spill-local`（宿主文件系统）是第一个。

Service Definition 故意最小：只有保存文本。它不拥有保留策略（那是 `@deepseek-ai/dsh-output-retention`）、不拥有工具结果替换（那是 `@deepseek-ai/dsh-spill-policy`）、也不拥有检索或搜索 API。后端提供适合其存储基底的定位器和检索提示。
"""
from cordis import 服务#导入Cordis服务基类
from .类型 import (#从本包类型再导出词汇
    溢出定位器,#溢出定位器品牌化
    溢出所有者字段,#所有者词汇
    溢出来源字段,#来源词汇
    保存文本溢出字段,#保存请求词汇
    溢出引用字段,#已保存引用词汇
)#再导出词汇类型

class 溢出存储(服务):#抽象溢出存储服务
    """抽象溢出存储服务。子类化、实现保存文本，并把子类当插件加载——它注册为 `ctx.spillStore`（每个上下文一个实现；加载第二个会抛错，这是 cordis 标准的重复服务行为）。

每个实现必须遵守的语义：
- 保存文本原样持久完整 content，并返回不透明定位器、精确字节长度和面向模型的检索指引。
- 存储按请求的所有者会话限定范围；后端选择私有（非全世界可读）位置，以及从调用方 suggestedName 派生——绝不等于它——的无碰撞名。
- 真实存储失败（权限、ENOSPC、后端不可用）时保存文本拒绝；调用方决定如何降级（溢出策略把拒绝当尽力而为并保留内联结果）。
"""
    def __init__(自身,上下文对象):#注册为ctx.spillStore
        """注册为 ctx.spillStore。"""
        super().__init__(上下文对象,'spillStore')#以spillStore键注册

    def 保存文本(自身,输入):#把全文持久到会话作用域溢出产物
        """把输入.content 持久到会话作用域的溢出产物。输入含所有者、调用方提供的来源字段、建议名和要保存的全文。返回已保存产物的溢出引用；存储失败时拒绝。"""
        raise NotImplementedError('SpillStore.saveText')#子类必须实现

默认=溢出存储#默认导出
default=溢出存储#Cordis默认导出
