import re
from ...依赖.cordis.服务 import 服务
from .设置作用域 import 设置错误

__all__=['设置模式服务']

数字键=re.compile(r'^\d+\Z',re.ASCII)#纯数字键

def 克隆容器(容器,键):
    """数组浅拷；对象浅拷；缺席则按下一键形状新建。"""
    if isinstance(容器,list):#数组
        return list(容器)#浅拷
    if isinstance(容器,dict):#对象
        return dict(容器)#浅拷
    if 数字键.match(键) is not None:#下一键是下标
        return []#数组
    return {}#对象

def 克隆脊(根,路径):
    """沿路径浅拷到叶父，返回新根、父、叶键。"""
    结果=dict(根)#根拷
    目标=结果#当前容器
    for 下标 in range(len(路径)-1):#走到叶前
        键=路径[下标]#本键
        下一=路径[下标+1]#下一键
        旧=目标[int(键)] if isinstance(目标,list) else (目标[键] if 键 in 目标 else None)
        子=克隆容器(旧,下一)#拷或新建
        if isinstance(目标,list):#数组
            目标[int(键)]=子#写回
        else:#对象
            目标[键]=子#写回
        目标=子#下行
    return 结果,目标,路径[len(路径)-1]#新根、父、叶

class 设置模式服务(服务):
    """设置自有的同步模式与不可变路径操作。"""
    def __init__(自身,上下文):
        """服务名 settingsSchema。"""
        super().__init__(上下文,'settingsSchema')#登记

    def 再水合(自身,序列化):
        """把 schema.toJSON() 信封当作活节点（本侧节点即 dict）。"""
        return 序列化#信封即节点

    def 校验(自身,模式,草稿):
        """校验草稿；通过返回 None，失败返回英文消息。"""
        if callable(模式) is False:#序列化信封无法就地调用
            return None#通过
        try:#活节点可调用
            模式(草稿)#抛则失败
            return None#通过
        except Exception as 错误:#失败
            return str(错误)#英文消息

    def 路径节点(自身,根,路径):
        """沿 object/dict/array 走到路径；缺席返回 None。"""
        节点=根#当前
        for 键 in 路径:#逐段
            if 节点 is None:#断
                return None#缺
            if not isinstance(节点,dict):#非节点
                return None#缺
            类型名=节点['type'] if 'type' in 节点 else None#类型
            if 类型名=='object':#对象
                表=节点['dict'] if 'dict' in 节点 else None#字段表
                节点=(表[键] if 键 in 表 else None) if isinstance(表,dict) else None
            elif 类型名=='dict' or 类型名=='array':#字典或数组
                节点=节点['inner'] if 'inner' in 节点 else None#内层
            else:#标量
                return None#缺
        return 节点#命中

    def 取路径(自身,值,路径):
        """按键或下标取值；缺席 None。"""
        当前=值#游标
        for 键 in 路径:#逐段
            if isinstance(当前,list):#数组
                当前=当前[int(键)]#下标
                continue#下
            if not isinstance(当前,dict):#非对象
                return None#缺
            当前=当前[键] if 键 in 当前 else None#字段
        return 当前#值

    def 有路径(自身,值,路径):
        """叶键是否存在，与值无关。"""
        if len(路径)==0:#空路径
            return 值 is not None#有值
        父=自身.取路径(值,路径[:-1])#父
        键=路径[len(路径)-1]#叶
        if isinstance(父,list):#数组
            return int(键)<len(父)#下标在
        if not isinstance(父,dict):#非对象
            return False#无
        return 键 in 父#有键

    def 设路径(自身,根,路径,值):
        """不可变写入；空路径抛错。"""
        if len(路径)==0:#空
            raise 设置错误('设路径需要非空路径')
        结果,父,叶=克隆脊(根,路径)#脊
        if isinstance(父,list):#数组
            父[int(叶)]=值#写
        else:#对象
            父[叶]=值#写
        return 结果#新根

    def 删路径(自身,根,路径):
        """不可变删除；缺席原根。"""
        if len(路径)==0:#空
            raise 设置错误('删路径需要非空路径')
        if 自身.有路径(根,路径) is False:#无
            return 根#原样
        结果,父,叶=克隆脊(根,路径)#脊
        if isinstance(父,list):#数组
            del 父[int(叶)]#删下标
        else:#对象
            del 父[叶]#删键
        return 结果#新根
