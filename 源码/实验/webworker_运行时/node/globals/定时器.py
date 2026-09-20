from ..builtin_modules.implemented.async_hooks import 绑定异步上下文

__all__=['安装定时器全局']

def 句柄化(标识):
    """构造 Node 形态定时器句柄。"""
    句柄={}
    def 引用():
        """保持引用。"""
        return 句柄
    def 取消引用():
        """取消引用。"""
        return 句柄
    def 有引用():
        """是否仍被引用。"""
        return True
    def 转原始():
        """转为数字 id。"""
        return 标识
    句柄['ref']=引用
    句柄['unref']=取消引用
    句柄['hasRef']=有引用
    句柄['valueOf']=转原始
    return 句柄

def 取标识(句柄):
    """从句柄或数字取定时器 id。"""
    if isinstance(句柄,(int,float)) and not isinstance(句柄,bool): return int(句柄)
    if isinstance(句柄,dict) and 'valueOf' in 句柄 and callable(句柄['valueOf']): return int(句柄['valueOf']())
    return None

def 绑定处理器(处理器):
    """将定时器处理器绑定到其注册上下文；非函数无可绑定。"""
    return 绑定异步上下文(处理器) if callable(处理器) else 处理器

def 包装调度(调度):
    """调度后包为句柄。"""
    def 调度句柄(处理器,超时=None,*参数):
        """绑定处理器后调度并包句柄。"""
        return 句柄化(调度(绑定处理器(处理器),超时,*参数))
    return 调度句柄

def 包装清除(清除):
    """先取 id 再清除。"""
    def 清除句柄(句柄=None):
        """接受句柄或数字 id。"""
        清除(取标识(句柄))
    return 清除句柄

def 安装定时器全局():
    """用 Node 形态包装器替换 Worker 的定时器全局。"""
    作用域=globals()
    原生超时=作用域['setTimeout']
    原生间隔=作用域['setInterval']
    原生清超时=作用域['clearTimeout']
    原生清间隔=作用域['clearInterval']
    作用域['setTimeout']=包装调度(原生超时)
    作用域['setInterval']=包装调度(原生间隔)
    作用域['clearTimeout']=包装清除(原生清超时)
    作用域['clearInterval']=包装清除(原生清间隔)

    def 立即(处理器,*参数):
        """零延时调度。"""
        return 句柄化(原生超时(绑定处理器(处理器),0,*参数))

    作用域['setImmediate']=立即
    作用域['clearImmediate']=包装清除(原生清超时)
