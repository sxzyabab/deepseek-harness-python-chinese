"""快捷键速查可见性与搜索状态，各入口共享。"""
from ...存储 import 声明存储

__all__=['创建快捷键存储']

def 初值():
    """根作用域：关、空查询、焦点代数 0。"""
    return {'open':False,'query':'','focusRequest':0}

def 打开(草稿):
    """打开并抬焦点代数，逼搜索框重聚焦。"""
    草稿['open']=True
    草稿['focusRequest']+=1

def 关闭(草稿):
    """关掉并清查询。"""
    草稿['open']=False
    草稿['query']=''

def 搜索(草稿,查询):
    """写入查询串。"""
    草稿['query']=查询

def 创建快捷键存储():
    """声明速查对话框 store：根作用域可见性、焦点请求与搜索。"""
    return 声明存储({
        'init':初值,
        'actions':{
            'open':打开,
            'close':关闭,
            'search':搜索,
        },
    })
