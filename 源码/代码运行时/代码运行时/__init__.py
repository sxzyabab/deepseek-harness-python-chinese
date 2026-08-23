"""代码执行能力 seam 的 Service Definition：把一份模型写的程序对着宿主异步绑定跑一次。运行时对工具与会话一无所知；那些由消费方拥有。"""
import re#匹配 dunder 形式成员名
from ...依赖 import cordis#外部依赖胶水
服务=cordis.服务#Cordis 服务基类
from .类型 import (#再导出 seam 词汇类型
    绑定错误类,#绑定错误类约定
    绑定错误类字段,#字段名元组
    绑定命名空间,#绑定命名空间
    绑定命名空间字段,#字段名元组
    运行请求,#运行请求
    运行请求字段,#字段名元组
    失败类别,#失败判别标签
    失败类别元组,#失败类别字面量元组
    运行失败,#运行失败
    运行失败字段,#字段名元组
    运行结果,#运行结果
    运行结果字段,#字段名元组
    绑定函数,#宿主绑定函数
    无损json值,#无损 JSON 值
)#类型再导出结束

__all__=[#仅中文公开名
    '保留绑定全局','保留错误成员','双下划线成员','可移植保留字','代码运行时',
    '绑定错误类','绑定错误类字段','绑定命名空间','绑定命名空间字段',
    '运行请求','运行请求字段','失败类别','失败类别元组','运行失败','运行失败字段',
    '运行结果','运行结果字段','绑定函数','无损json值','默认',
]#公开面结束

#各后端共享的保留绑定全局：某个后端在程序命名空间里拥有该槽。console 为 worker 的日志捕获槽；__dsh_main__/__builtins__/__name__ 为 Python 后端的引导包装与播种模块全局；__debug__ 为 CPython 编译期常量。用一份共享集合——而不是各后端只拒绝自己的槽——才能兑现可移植承诺：一份在某后端合法的命名空间列表在所有后端都合法，调用方不能挑一个在 worker 上能用、在 Python 上碰撞的名字（反之亦然）。__name__ 等本身是合法可移植标识符，因此绑定命名空间.global 的标识符规则不会拒绝它们——所以需要这份显式集合。（错误成员不同：双下划线成员整类拒绝一切 dunder 形式；绑定全局只拒绝此处列出的名字。）列出 __debug__ 是另一原因，不是碰撞：CPython 把裸 __debug__ 引用编译成常量 True，并在编译期拒绝对该名赋值，因此以该名注入的全局从程序里不可达——校验会接受，Python 后端却用不上，而这正是共享集合要防止的分裂。
保留绑定全局=frozenset((#各后端共享的保留绑定全局名
    'console',#worker 日志捕获槽
    '__dsh_main__','__builtins__','__name__','__debug__',#Python 后端播种/包装槽与编译期常量
))#保留绑定全局结束

#各后端共享的保留错误成员：作为一份共享约定，使一份请求在某后端合法则在所有后端合法。name/message/stack 为 JS Error 自有槽；args/with_traceback/add_note 为 Python 异常协议成员。dunder 形式名（__x__，中间非空）整类拒绝——其中若干是受约束的 CPython 描述符，在构造拒绝时 setattr 会抛错，精确集合是解释器版本细节。任何其他非空自有属性名在各处都接受。
保留错误成员=frozenset((#各后端共享的保留错误成员名
    'name','message','stack',#JS Error 自有槽
    'args','with_traceback','add_note',#Python 异常协议成员
))#保留错误成员结束

#dunder 形式（__x__，中间非空）：Python 的对象协议槽，作为保留错误成员在每个后端拒绝。
双下划线成员=re.compile(r'^__.+__$')#匹配 dunder 形式成员名

#跨语言保留字并集：每个可移植目标语言（ECMAScript ∪ Python）的保留字，所有后端都拒绝用作绑定命名空间.global / 错误类名。即使目前只有 TypeScript worker 有已发布后端，Python 仍是可移植目标。可移植标识符约定承诺：一份在某后端合法的命名空间列表在每个后端都合法；按语言分别检查会让 lambda 通过 TypeScript 后端却在 Python 上失败。给 seam 增加新语言意味着扩大这个并集（按设计，要对现有绑定名做破坏性审查）。
可移植保留字=frozenset((#跨语言保留字并集
    'await','break','case','catch','class','const','continue','debugger','default','delete','do',#ECMAScript 控制流与声明
    'else','enum','export','extends','false','finally','for','function','if','import','in',#ECMAScript 分支、模块与字面量
    'instanceof','new','null','return','super','switch','this','throw','true','try','typeof',#ECMAScript 运算与异常
    'var','void','while','with','yield','let','static','implements','interface','package',#ECMAScript 声明与严格模式
    'private','protected','public','arguments','eval',#ECMAScript 可见性与求值槽
    'False','None','True','and','as','assert','async','def','del','elif','except','from',#Python 字面量与语句
    'global','is','lambda','nonlocal','not','or','pass','raise','match','type','_',#Python 其余关键字与软关键字（type 与 _ 是软关键字：实践中可作名字，此处为安全起见保留）
))#可移植保留字结束

class 代码运行时(服务):#代码运行时服务基类
    """注册一份 ctx.codeRuntime 实现。程序、预算、中止与基底失败都在运行结果里决议；只有 Service Definition 约定误用才拒绝。实现桥接可 structured-clone 的绑定，物化每个已声明的命名空间拒绝类，把程序当敌对对等方，使各次运行彼此隔离，并在拆除时终止并等待飞行中的运行。"""
    def __init__(自身,上下文对象):#注册为 codeRuntime 服务
        """注册为 ctx.codeRuntime。"""
        super().__init__(上下文对象,'codeRuntime')#挂到上下文服务名

    @property#只读属性
    def 语言(自身):#源语言标识
        """运行期望 program 所用的源语言，小写标识符。仅作信息，不作门禁——生成语言特定展示（带类型 SDK 桩、用法说明）的消费方据此切换，遇无法展示的语言则大声失败。已知值：typescript 与 python，即 dsh-tools 所展示的那些；目前只有 typescript 有已发布后端。"""
        raise NotImplementedError('代码运行时.语言')#子类必须实现

    @property#只读属性
    def 隔离(自身):#隔离基底标识
        """执行基底，小写标识符。仅作信息，不作门禁——供部署与诊断区分后端的描述符，不是安全声明。已知值：worker-thread、process、container。"""
        raise NotImplementedError('代码运行时.隔离')#子类必须实现

    def 运行(自身,请求):#执行一次程序
        """对着请求的绑定执行一份程序并捕获其发出的内容。决议约定见类文档（错误是结果字段；拒绝只表示 Service Definition 约定误用）。请求携带程序、绑定与中止信号；请求携带运行时要处理的一切，没有隐藏默认值。返回该次运行结局：完成值（可传输时）、有序日志捕获，以及失败（若有）。"""
        raise NotImplementedError('代码运行时.运行')#子类必须实现

默认=代码运行时#默认导出服务基类
