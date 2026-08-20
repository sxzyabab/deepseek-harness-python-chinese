"""核心上下文类型与根上下文实现。"""
from .上下文 import 上下文,Context#再导出上下文
from .事件 import 事件服务,是否中断,isBailed,EventsService#再导出事件
from .光纤 import (
    光纤,#光纤类
    光纤状态,#生命周期
    Fiber,#英文别名
    FiberState,#英文别名
    校验错误,#配置校验错误
    ValidationError,#英文别名
    解析配置,#配置校验
    resolveConfig,#英文别名
    Cordis错误,#框架错误
    CordisError,#英文别名
)
from .日志 import (
    日志器,#日志门面
    日志服务,#日志服务
    日志级别,#数字级别
    Logger,#英文别名
    LoggerService,#英文别名
    LoggerLevel,#英文别名
    默认格式化器,#占位符
    defaultFormatters,#英文别名
    色板16,#16 色
    色板256,#256 色
    c16,#英文别名
    c256,#英文别名
)
from .注册表 import 注册表服务,注入,Inject,RegistryService,解析注入#再导出注册表
from .服务 import 服务,Service#再导出服务
from .工具 import (
    符号,#共享符号
    symbols,#下面赋值
    可释放列表,#可释放列表
    DisposableList,#下面赋值
    拼接错误,#错误拼接
    composeError,#下面赋值
    构建外层栈,#外层栈
    buildOuterStack,#下面赋值
    取可追踪,#可追踪
    getTraceable,#下面赋值
    是否构造器,#构造器判断
    isConstructor,#下面赋值
    是否对象,#对象判断
    isObject,#下面赋值
    创建可调用,#可调用服务
    createCallable,#下面赋值
    承诺,#可等待
    聚合错误,#多失败
)
from .反射 import 反射服务,ReflectService#再导出反射

symbols=符号#英文别名
DisposableList=可释放列表#英文别名
composeError=拼接错误#英文别名
buildOuterStack=构建外层栈#英文别名
getTraceable=取可追踪#英文别名
isConstructor=是否构造器#英文别名
isObject=是否对象#英文别名
createCallable=创建可调用#英文别名
