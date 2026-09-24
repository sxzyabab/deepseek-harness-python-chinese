"""在精确源事件前缀上构造分叉种子。"""
from .修复 import 打开轮次关闭器

__all__=['构建分叉种子']

def 构建分叉种子(事件列表,边界):
    """复制含端点前缀，标记继承切断，用分叉结局关闭打开尾。调用方保证边界是已有连续序号。"""
    前缀=list(事件列表[:边界+1])
    前缀.append({
        'type':'session/end-seed',
        'seq':边界+1,
        'time':事件列表[边界]['time'],
        'data':{'inherited':True},
    })
    return 前缀+打开轮次关闭器(前缀,{'kind':'forked'})
