"""校验并收下一次程序可用的绑定名。"""
import re#标识符形态
from ..ptc运行时 import (#缝上共享的保留表
    双下划线成员,#__x__ 形态
    可移植保留字,#ECMAScript ∪ Python 保留字
    保留绑定全局,#后端拒绝的绑定全局
    保留错误成员,#后端拒绝的错误成员
)#保留表结束
from .协议 import 节点ptc错误#本包异常

__all__=['校验绑定']#仅中文公开名

标识符=re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$',re.ASCII)#可用标识符

def 校验绑定(请求):#拒绝不可用命名空间
    """启动进程前拒绝不可用命名空间。请求是 dict。返回按声明全局键控的命名空间。"""
    绑定表={}#全局名到命名空间
    for 命名空间 in 请求['bindings']:#逐个命名空间
        全局名=命名空间['global']#声明全局
        if 标识符.search(全局名) is None or 全局名 in 可移植保留字:#不是可用标识符
            raise 节点ptc错误('dsh-ptc-runtime-node: binding global '+repr(全局名)+' is not a usable identifier')#拒绝
        if 全局名 in 保留绑定全局:#缝上共享的后端保留集
            raise 节点ptc错误('dsh-ptc-runtime-node: reserved binding global '+repr(全局名))#拒绝
        if 全局名 in 绑定表:#重复全局
            raise 节点ptc错误('dsh-ptc-runtime-node: duplicate binding global '+repr(全局名))#拒绝
        绑定表[全局名]=命名空间#记下
    错误类名=set()#已注入的错误类名
    for 命名空间 in 请求['bindings']:#再扫错误类
        if 'errorClass' not in 命名空间:#无错误类
            continue#跳过
        描述=命名空间['errorClass']#错误类描述
        if 描述 is None:#显式空
            continue#跳过
        类名=描述['name']#类名
        if 标识符.search(类名) is None or 类名 in 可移植保留字:#不是可用标识符
            raise 节点ptc错误('dsh-ptc-runtime-node: binding error class '+repr(类名)+' is not a usable identifier')#拒绝
        if 类名 in 保留绑定全局:#保留全局
            raise 节点ptc错误('dsh-ptc-runtime-node: reserved binding global '+repr(类名))#拒绝
        if 类名 in 绑定表 or 类名 in 错误类名:#与全局或另一错误类冲突
            raise 节点ptc错误('dsh-ptc-runtime-node: duplicate injected global '+repr(类名))#拒绝
        成员=描述['memberNameProperty']#成员名属性
        if len(成员)==0 or 成员 in 保留错误成员 or 双下划线成员.search(成员) is not None:#不可用成员
            raise 节点ptc错误('dsh-ptc-runtime-node: binding error member property '+repr(描述['memberNameProperty'])+' is not usable')#拒绝
        错误类名.add(类名)#记下
    return 绑定表#按全局键控
