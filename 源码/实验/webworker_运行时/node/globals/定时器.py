"""Node 形态的定时器句柄。浏览器的 `setTimeout`/`setInterval` 返回
数字 id，而 harness 与自带代码会对句柄调用 `.unref()`
（`client-hmr` 的轮询间隔、cordis 的定时器插件）。包装器返回带 Node 的
`ref`/`unref`/`hasRef` 的句柄对象，且 `clear*` 接受两种形态——
对象也会转换为其数字 id，因此把它当数字存的代码仍可用。

处理器还绑定到注册定时器时的异步上下文
（`./async-context-hooks.ts`），因此在发起方边界内调度的回调
触发时仍归属于该边界。

对齐上游 `webworker-runtime/src/node/globals/timers.ts`。公开面仅中文名。
"""
from ..builtin_modules.implemented.async_hooks import 绑定异步上下文#导入异步上下文绑定

__all__=['安装定时器全局']#仅中文公开名

def 句柄化(标识):#数字id包装为句柄
    """构造 Node 形态定时器句柄。"""
    句柄={}#句柄对象
    def 引用():#无操作ref
        """保持引用。"""
        return 句柄#链式
    def 取消引用():#无操作unref
        """取消引用。"""
        return 句柄#链式
    def 有引用():#恒有引用
        """是否仍被引用。"""
        return True#恒有引用
    def 转原始():#暴露数字id
        """转为数字 id。"""
        return 标识#数字id
    句柄['ref']=引用#ref
    句柄['unref']=取消引用#unref
    句柄['hasRef']=有引用#hasRef
    句柄['valueOf']=转原始#对齐 Symbol.toPrimitive
    return 句柄#返回句柄

def 取标识(句柄):#从句柄取数字id
    """从句柄或数字取定时器 id。"""
    if isinstance(句柄,(int,float)) and not isinstance(句柄,bool): return int(句柄)#已是数字
    if isinstance(句柄,dict) and callable(句柄.get('valueOf')): return int(句柄['valueOf']())#转数字
    return None#无法识别

def 绑定处理器(处理器):#绑定处理器上下文
    """将定时器处理器绑定到其注册上下文；非函数无可绑定。"""
    return 绑定异步上下文(处理器) if callable(处理器) else 处理器#函数则绑定

def 包装调度(调度):#包装调度器
    """调度后包为句柄。"""
    def 调度句柄(处理器,超时=None,*参数):#绑定后调度
        """绑定处理器后调度并包句柄。"""
        return 句柄化(调度(绑定处理器(处理器),超时,*参数))#绑定后调度
    return 调度句柄#交回

def 包装清除(清除):#包装清除器
    """先取 id 再清除。"""
    def 清除句柄(句柄=None):#清除
        """接受句柄或数字 id。"""
        清除(取标识(句柄))#先取id再清除
    return 清除句柄#交回

def 安装定时器全局():#安装定时器全局
    """用 Node 形态包装器替换 Worker 的定时器全局。"""
    作用域=globals()#可写全局面
    原生超时=作用域['setTimeout']#原生setTimeout
    原生间隔=作用域['setInterval']#原生setInterval
    原生清超时=作用域['clearTimeout']#原生clearTimeout
    原生清间隔=作用域['clearInterval']#原生clearInterval
    作用域['setTimeout']=包装调度(原生超时)#替换setTimeout
    作用域['setInterval']=包装调度(原生间隔)#替换setInterval
    作用域['clearTimeout']=包装清除(原生清超时)#替换clearTimeout
    作用域['clearInterval']=包装清除(原生清间隔)#替换clearInterval

    def 立即(处理器,*参数):#安装setImmediate
        """零延时调度。"""
        return 句柄化(原生超时(绑定处理器(处理器),0,*参数))#零延时

    作用域['setImmediate']=立即#挂setImmediate
    作用域['clearImmediate']=包装清除(原生清超时)#用clearTimeout清immediate
