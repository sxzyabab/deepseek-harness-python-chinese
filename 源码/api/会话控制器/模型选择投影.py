"""持久模型选择意图与请求使用投影。

对齐上游 `session-controller/src/model-selection-projection.ts`。公开面仅中文名。
"""
from .工具 import 取字段#辅助

__all__=['安装模型选择投影']#仅中文公开名

def 选择相同(左,右):#比较模型选择
    """两条模型选择是否相同。"""
    if 左 is 右:#同引用
        return True#相同
    if 左 is None or 右 is None:#一方为空
        return False#不同
    return (取字段(左,'provider')==取字段(右,'provider') and 取字段(左,'model')==取字段(右,'model') and 取字段(左,'reasoningEffort')==取字段(右,'reasoningEffort'))#字段

def 应用模型选择投影(状态,事件):#折叠一步
    """按事件推进 durable modelSelection 状态。"""
    种类=取字段(事件,'type')#事件类型
    if 种类=='model/selection':#用户选择
        数据=取字段(事件,'data')#载荷
        if 选择相同(取字段(状态,'pending'),数据):#未变
            return 状态#原样
        return {'lastUsed':取字段(状态,'lastUsed'),'pending':数据}#更新 pending
    if 种类!='request/header':#其它
        return 状态#不变
    头=取字段(取字段(事件,'data'),'header')#请求头
    配置=取字段(头,'config')#配置
    最近使用={#lastUsed
        'provider':取字段(配置,'provider'),#提供方
        'model':取字段(配置,'model'),#模型
        **({} if 取字段(配置,'reasoningEffort') is None else {'reasoningEffort':str(取字段(配置,'reasoningEffort'))}),#推理
    }#结束
    待定=None if 选择相同(取字段(状态,'pending'),最近使用) else 取字段(状态,'pending')#消费 pending
    if 选择相同(取字段(状态,'lastUsed'),最近使用) and 待定 is 取字段(状态,'pending'):#未变
        return 状态#原样
    return {'lastUsed':最近使用,'pending':待定}#新状态

def 安装模型选择投影(上下文):#注册投影
    """在 sessionProjections 注册 modelSelection 列。"""
    上下文.sessionProjections.register({#注册定义
        'key':'modelSelection',#键
        'init':lambda:{'lastUsed':None,'pending':None},#初值
        'apply':应用模型选择投影,#折叠
        'wire':{#线上视图
            'view':lambda 状态:{'lastUsed':取字段(状态,'lastUsed'),'next':取字段(状态,'pending') if 取字段(状态,'pending') is not None else 取字段(状态,'lastUsed')},#next 回退
        },#wire 结束
        'stateVersion':2,#版本
    })#register 结束
