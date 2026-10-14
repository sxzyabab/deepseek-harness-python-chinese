'快捷键速查可见性与搜索状态，各入口共享'
from ...存储 import 声明存储

__all__=['创建快捷键存储','快捷键存储面']

def 初值():
    '根作用域：关、空查询、焦点代数 0'
    return {'open':False,'query':'','focusRequest':0}

def 打开(草稿):
    '打开并抬焦点代数，逼搜索框重聚焦'
    草稿['open']=True
    草稿['focusRequest']+=1

def 关闭(草稿):
    '关掉并清查询'
    草稿['open']=False
    草稿['query']=''

def 搜索(草稿,查询):
    '写入查询串'
    草稿['query']=查询

class 快捷键存储面:
    '把声明存储的字典实例收成带 getSnapshot/subscribe 的对象'
    def __init__(自身,原始):
        '记下底层字典'
        自身.actions=原始['actions']
        自身._读=原始['getSnapshot']
        自身._订=原始['subscribe']
        自身.clearPersisted=原始['clearPersisted']

    def getSnapshot(自身):
        '当前可见性与查询'
        return 自身._读()

    def subscribe(自身,监听):
        '订阅替换'
        return 自身._订(监听)

def 创建快捷键存储():
    '声明速查对话框 store：根作用域可见性、焦点请求与搜索'
    return 声明存储({
        'init':初值,
        'actions':{
            'open':打开,
            'close':关闭,
            'search':搜索,
        },
    })
