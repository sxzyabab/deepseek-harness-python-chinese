"""代码执行 seam 的词汇类型：调用方交给代码运行时什么、拿回什么。纯类型——此处无运行时代码。"""
from typing import Literal,NotRequired,TypedDict#字面量、可选字段与结构类型

#暴露给程序的一个宿主侧异步可调用函数。运行时桥接对其的调用（可能跨序列化边界），因此 args 与决议值必须是无损 JSON。运行时对有损或不可克隆的值以描述性错误拒绝，而不是污染本次运行。绑定决议没有 seam 级字节上限。本函数的拒绝会在程序内表现为对应调用的拒绝。
绑定函数=callable#宿主绑定函数：入参未知，返回无损 JSON；运行时即 callable

#可通过轻依赖 Service Definition 传输的无损 JSON 值：null|bool|number|string|list|dict，可递归嵌套。后者是服务本地、与规范 JsonValue 结构等价的类型，使 Service Definition 包保持独立于会话。
无损json值=object#递归的无损 JSON 值；运行时为可递归嵌套的 JSON 兼容对象

class 绑定错误类(TypedDict):#某一绑定命名空间对程序可见的带类型拒绝约定
    """运行时在 name 下注入真实错误构造函数；被拒绝的成员调用成为其实例，并通过 memberNameProperty 暴露确切成员名。两个字符串都是运行时数据，而不是对特定消费方（如 Code Mode）的知识。"""
    name:str#构造函数全局名与结果 Error.name；可移植标识符规则与绑定命名空间的 global 相同
    memberNameProperty:str#存放成员名的非空自有属性；可移植排除集是保留错误成员加上 dunder 形式名（__x__，中间非空），每个后端以相同规则强制；任何其他名字——无论是否是标识符——在各处都接受

绑定错误类字段=('name','memberNameProperty')#字段名元组，供文档与对称列举

#一组绑定函数，运行时作为单个全局对象（例如 tools）暴露给程序。函数名是任意字符串——运行时必须把 __proto__ 或 constructor 这类名字当作普通自有属性（空原型构造），绝不当作原型碰撞。
#global 为保留字，故用函数式 TypedDict 保留上游字段名。
绑定命名空间=TypedDict('绑定命名空间',{#程序可见的一组绑定函数
    'global':str,#程序看到的全局标识符。必须匹配 LANGUAGE-PORTABLE 标识符子集 [A-Za-z_][A-Za-z0-9_]*（不含 JS 专有的 $），且不是任何语言的保留字，以便同一命名空间列表对每个后端都可用，无论 language——像 $tools 这种仅 JS 拼写按设计拒绝，而不只是 Python 后端拒绝。满足标识符规则但命名后端自有槽的名字（保留绑定全局，例如 console、__dsh_main__）也在各处拒绝；精确集合与保留原因见其声明
    'functions':dict,#可调用成员，键为程序调用的确切名字，值为绑定函数
    'errorClass':NotRequired[绑定错误类],#可选的、本命名空间对程序可见的带类型拒绝约定
})#绑定命名空间结束
绑定命名空间字段=('global','functions','errorClass')#上游字段名元组

class 运行请求(TypedDict):#一次运行：程序源码加上运行时要处理的一切
    """按显式优于隐式约定，默认值（时间预算、输出上限）是实现的已校验配置——请求不携带可选调优旋钮供隐藏的 ?? 填入。"""
    program:str#程序源码，语言为运行时的语言；作为异步函数体运行：可用顶层 await 与 return，完成值成为运行结果.value
    bindings:list#暴露给程序的宿主函数，每个命名空间一个全局对象（绑定命名空间列表）
    signal:NotRequired[object]#中止本次运行：运行时停止程序（硬停，即使在循环中）并以 kind abort 的运行失败决议；飞行中的绑定调用由调用方自行了结——运行时只停止继续询问

运行请求字段=('program','bindings','signal')#字段名元组

#运行为何失败的正交判别标签。各类是正交结果，独立报告：预算到期不是异常，中止不是超时，基底死亡两者都不是。
#exception — 程序抛错或解析/变换失败。
#timeout — 实现拥有的预算到期；消息说明是哪一项。
#abort — 运行请求.signal 已触发。
#worker-exit — 执行基底未了结就死亡（例如 OOM）。
#invalid-output — 完成值不是无损 JSON。
#output-limit — 序列化后的外层日志/值/诊断超过配置上限。
失败类别=Literal['exception','timeout','abort','worker-exit','invalid-output','output-limit']#失败判别标签
失败类别元组=('exception','timeout','abort','worker-exit','invalid-output','output-limit')#失败类别字面量元组

class 运行失败(TypedDict):#一次运行失败描述
    """错误是已决议结果上的字段，绝不是运行() 的拒绝——报告失败的程序是调用方的工作，不是异常路径。"""
    kind:失败类别#失败类别（各类含义见模块注释）
    message:str#人类可读细节，适合回喂模型以自行纠正

运行失败字段=('kind','message')#字段名元组

class 运行结果(TypedDict):#一次运行的结果
    """错误是已决议结果上的字段，绝不是运行() 的拒绝——报告失败的程序是调用方的工作，不是异常路径。"""
    value:NotRequired[object]#程序的完成值（其顶层 return），当它跑完且该值穿过运行时的无损 JSON 边界时存在；无效或超限的完成会使运行失败，而不是换成渲染字符串；失败或无值的运行不带本字段
    logs:list#程序按顺序发出的文本，仅作为外层结果的一部分受界（字符串列表）
    error:NotRequired[运行失败]#仅当运行失败时存在；分类见运行失败

运行结果字段=('value','logs','error')#字段名元组
