'初始状态，以及每条操作用的标识铸造。铸造在施加之外，记录才能回放出同一棵树'

__all__=['创建标识铸造','创建初始状态']

def 创建标识铸造(种子=0):
    '造一个标识源。种子是第一枚之前的计数，默认从 0 起'
    计数={'值':种子}
    def 下一枚(前缀):
        '下一枚标识。前缀标明种类，计数保证这一源里不重复'
        计数['值']+=1
        return f'{前缀}{计数["值"]}'
    return {'next':下一枚}

def 创建初始状态(铸造,造初始标签=None,模式='push'):
    '折叠着的一块停靠窗格。第一张标签属于初始状态，不记成操作'
    窗格标识=铸造['next']('pane')
    初始=None
    if 造初始标签 is not None:
        初始=造初始标签(铸造['next']('tab'))
    if 初始 is None:
        标签序=[]
        标签表={}
        活动=None
    else:
        标签序=[初始['id']]
        标签表={初始['id']:初始}
        活动=初始['id']
    return {
        'nodes':{
            窗格标识:{
                'kind':'pane',
                'id':窗格标识,
                'host':'dock',
                'tabs':标签序,
                'activeTabId':活动,
                'rect':None,
            },
        },
        'tabs':标签表,
        'rootId':窗格标识,
        'floats':[],
        'activePaneId':窗格标识,
        'expanded':False,
        'mode':模式,
    }
