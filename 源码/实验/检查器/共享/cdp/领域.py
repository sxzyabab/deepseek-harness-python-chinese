"""被检查 JavaScript 界域的、与环境无关的后端接口。

对齐上游 `shared/cdp/realm.ts`。公开面仅中文名。
"""
__all__=[#仅中文公开名
    '原生协议通知','领域能力','运行时后端','控制台后端','源后端','调试器后端','原生域后端',
]#公开面结束

class 原生协议通知:#原生协议通知
    """原生引擎协议后端发出的原始通知。"""
    def __init__(自身,method,params=None):#构造
        """保存通知字段。"""
        自身.method=method#方法名
        自身.params=params#参数

def 领域能力(状态,**字段):#界域能力状态
    """显式支持或不支持的界域能力。"""
    return {'state':状态,**字段}#判别联合

class 运行时后端:#Runtime后端
    """在每个连接的界域会话内实现的 Runtime 操作。"""
    def 启用(自身):#启用
        """为本连接准备 Runtime 事件与执行状态。"""
        raise NotImplementedError#子类实现
    def 禁用(自身):#禁用
        """禁用 Runtime 事件并释放后端会话状态。"""
        raise NotImplementedError#子类实现
    def 求值(自身,请求):#求值
        """在本界域求值源码。"""
        raise NotImplementedError#子类实现
    def 获取属性(自身,请求):#获取属性
        """枚举一个保留对象的属性。"""
        raise NotImplementedError#子类实现
    def 调用函数(自身,请求):#调用函数
        """用本界域会话拥有的引用调用函数。"""
        raise NotImplementedError#子类实现
    def 等待承诺(自身,请求):#等待Promise
        """等待一个保留的 Promise。"""
        raise NotImplementedError#子类实现
    def 全局词法作用域名(自身,上下文=None):#全局词法名
        """读取一个后端执行上下文全局词法作用域中可见的名字。"""
        raise NotImplementedError#子类实现
    def 释放对象(自身,句柄):#释放对象
        """释放一个后端对象引用。"""
        raise NotImplementedError#子类实现
    def 释放对象组(自身,组):#释放对象组
        """释放某个组下保留的全部后端对象。"""
        raise NotImplementedError#子类实现

class 控制台后端:#Console后端
    """界域 Console 事件源。"""
    def 订阅(自身,监听器):#订阅
        """订阅 Console 与未捕获异常事件。"""
        raise NotImplementedError#子类实现
    def 清空(自身):#清空
        """在支持时清除后端拥有的 Console 历史。"""
        raise NotImplementedError#子类实现

class 源后端:#源后端
    """与 CDP ScriptId 分配无关的界域脚本目录。"""
    def 列出脚本(自身):#列出脚本
        """返回本界域当前已知的全部脚本。"""
        raise NotImplementedError#子类实现
    def 获取脚本源(自身,脚本键):#取脚本源
        """按界域本地脚本键读取源文本。"""
        raise NotImplementedError#子类实现
    def 获取源映射(自身,脚本键):#取source map
        """按界域本地脚本键读取可选 source map。"""
        raise NotImplementedError#子类实现
    def 订阅(自身,监听器):#订阅新脚本
        """订阅初始目录读取之后发现的脚本。"""
        raise NotImplementedError#子类实现

class 调试器后端:#调试器后端
    """一个界域会话的活动 JavaScript 调试后端。"""
    def 启用(自身,请求):#启用
        """为本连接启用调试器事件。"""
        raise NotImplementedError#子类实现
    def 禁用(自身):#禁用
        """为本连接禁用调试器事件。"""
        raise NotImplementedError#子类实现
    def 暂停(自身):#暂停
        """暂停本界域。"""
        raise NotImplementedError#子类实现
    def 恢复(自身,请求):#恢复
        """恢复本界域。"""
        raise NotImplementedError#子类实现
    def 在调用帧求值(自身,请求):#在调用帧求值
        """在一个已暂停帧中求值表达式。"""
        raise NotImplementedError#子类实现
    def 订阅(自身,监听器):#订阅
        """订阅暂停、恢复与断点事件。"""
        raise NotImplementedError#子类实现

class 原生域后端:#原生域后端
    """仅 Host 拥有的、尚未规范化域的原生协议适配器。"""
    def 请求(自身,方法,参数):#请求
        """执行一条原生协议请求。"""
        raise NotImplementedError#子类实现
    def 订阅(自身,监听器):#订阅
        """订阅原生协议通知。"""
        raise NotImplementedError#子类实现
