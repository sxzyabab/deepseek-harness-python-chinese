"""系统提示词组装的结构类型。对齐上游 `system-prompt/src/index.ts` 公开接口。公开面仅中文名；字段键保持上游字面量。"""
from typing import NotRequired,TypedDict#可选字段与结构类型

__all__=(
    '组装上下文',
    '提示词段落',
    '提示词上下文',
    '已组装段落',
    '已组装上下文',
    '工具提供结果',
    '提示词组装',
    '系统提示词配置',
)#仅中文公开名

class 组装上下文(TypedDict,total=False):#一次 assemble 的可合并扩展上下文
    """一次提示词组装的可合并扩展上下文。缺省字段时只有全局提供方与无主体监听器参与。"""
    scope:object#其提供方与瀑布监听器参与的作用域键；缺省则仅全局
    signal:object#显式控制本次组装请求的信号；不得留下来控制更后轮次

class 提示词段落(TypedDict):#注册表输入的一段系统提示词
    """系统提示词的一段贡献（注册表输入）。同层重复名与非有限顺序会抛。"""
    name:str#唯一名；重复登记会抛
    order:float#升序拼接；约定 −100 是 harness 身份，0 是部署人设，工具指导用 100–199
    text:object#静态文本，或每次组装用该次组装上下文求值的提供方；可含严格 {{variable}}
    complete:NotRequired[bool]#真则瀑布后还原为本作用域唯一提示词段落；多于一个有效完整段会使组装失败

class 提示词上下文(TypedDict):#动态运行时上下文贡献
    """物化为耐久用户角色快照的动态模型上下文。空文本不贡献。"""
    name:str#唯一名；重复登记会抛
    order:float#升序拼接
    text:object#静态文本，或每次组装求值的提供方

class 已组装段落(TypedDict):#文本已解析、尚未插值的段落
    """组装的一段：提示词段落且文本已解析。"""
    name:str#贡献段落的唯一名
    text:str#已解析（尚未插值）的段落文本

class 已组装上下文(TypedDict):#文本已解析的动态上下文
    """一条已解析的动态上下文贡献。"""
    name:str#贡献上下文的唯一名
    text:str#变量插值前的已解析文本

class 工具提供结果(TypedDict):#一次提供方求值的可见模式与限制前名
    """一次组装里可见的工具模式及其限制前名称集。"""
    schemas:list#本提供方贡献给这次组装的模式
    knownNames:NotRequired[list]#供 toolOrder 校验用的限制前名称宇宙；缺省取 schemas 的名

class 提示词组装(TypedDict):#可合并扩展的已组装模型输入
    """可合并扩展的已组装模型输入。段落与上下文保持未插值直到渲染；工具已是规范顺序。"""
    sections:list#已组装段落
    contexts:list#已组装上下文
    tools:list#规范顺序的工具模式
    variables:dict#已登记变量在本上下文求得的值；可为 None 表示本组装无值

class 系统提示词配置(TypedDict,total=False):#插件配置字段（与 Config 模式键对齐）
    """部署撰写的系统提示词片段；运行时模式见 系统提示词.Config。"""
    includeHarnessIdentity:bool#人设之前是否含固定 DeepSeek Harness 身份；缺省真
    includeRuntimeContext:bool#是否含动态运行时上下文快照；缺省真
    persona:str#部署范围顺序 0 人设模板；空串渲染时删除该段
    toolOrder:list#面向模型的工具名顺序，须恰含一次 '<unlisted-tools>'；省略则字典序
