'同一读取器和同一文件的已挂上控件，共用一份关联查询。'
from ...模块.客户端.通告 import 取握手窗口
from weakref import WeakKeyDictionary as 弱键字典
from ...存储 import 创建快照存储

__all__=['空刷新','使用文件应用','接上文件应用']

读者表=弱键字典()


def 空刷新():
    '未启用时没有查询可刷新'
    return None


def 使用文件应用(目标,查询,启用,监听=None):
    '挂上共享查询。返回当前快照、刷新和退订'
    if 启用 is not True:
        def 空退():
            '未启用，没有要取消的查询'
            return None
        return {
            'apps':[],
            'loading':True,
            'failed':False,
            'refresh':空刷新,
            '退订':空退,
            '状态':None,
        }
    目标表=读者表.get(查询)
    if 目标表 is None:
        目标表={}
        读者表[查询]=目标表
    项=目标表.get(目标)
    初次=项 is None
    if 项 is None:
        项={
            'state':创建快照存储({'apps':[],'loading':True,'failed':False}),
            'users':0,
            'controller':None,
        }

        def 刷新(项=项,查询=查询,目标=目标):
            '中止上一次，再查这个文件'
            控=项['controller']
            if 控 is not None:
                控.abort()
            窗口=取握手窗口()
            新控=窗口.AbortController()
            项['controller']=新控
            应用=查询(目标,新控.signal)
            if 新控.signal.aborted:
                return
            if 应用 is None:
                项['state'].set({'apps':[],'loading':False,'failed':True})
            else:
                项['state'].set({'apps':应用,'loading':False,'failed':False})

        项['refresh']=刷新
        目标表[目标]=项
    保留=项
    保留['users']+=1
    退状态=None
    if 监听 is not None:
        退状态=保留['state'].subscribe(监听)
    if 初次:
        保留['refresh']()

    def 退订(保留=保留,目标表=目标表,目标=目标,退状态=退状态):
        '最后一个使用者离开时中止并丢掉'
        if 退状态 is not None:
            退状态()
        保留['users']-=1
        if 保留['users']==0:
            控=保留['controller']
            if 控 is not None:
                控.abort()
            if 目标 in 目标表:
                del 目标表[目标]

    快照=保留['state'].getSnapshot()
    return {
        'apps':快照['apps'],
        'loading':快照['loading'],
        'failed':快照['failed'],
        'refresh':保留['refresh'],
        '退订':退订,
        '状态':保留['state'],
    }


def 接上文件应用(持有,目标,查询,启用,监听):
    '同一个文件、读取器和启用状态只订阅一次'
    键=(目标,id(查询),启用 is True)
    if getattr(持有,'联想键',None)==键:
        仓=getattr(持有,'状态仓',None)
        if 仓 is None:
            return {
                'apps':[],
                'loading':True,
                'failed':False,
                'refresh':持有.刷新函数,
            }
        快照=仓.getSnapshot()
        return {
            'apps':快照['apps'],
            'loading':快照['loading'],
            'failed':快照['failed'],
            'refresh':持有.刷新函数,
        }
    旧=getattr(持有,'退订联想',None)
    if 旧 is not None:
        持有.退订联想=None
        旧()
    持有.联想键=键
    结果=使用文件应用(目标,查询,启用 is True,监听)
    持有.退订联想=结果['退订']
    持有.状态仓=结果['状态']
    持有.刷新函数=结果['refresh']
    return {
        'apps':结果['apps'],
        'loading':结果['loading'],
        'failed':结果['failed'],
        'refresh':结果['refresh'],
    }
