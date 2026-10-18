__all__=['最大历史条数','浏览器导航']

最大历史条数=100


class 浏览器导航:
    '应用自己记下的地址历史，以及内嵌帧能观察到的加载状态'

    def __init__(自身,初始=None):
        '用保存下来的状态，或者一份空状态'
        if 初始 is None:
            初始=浏览器导航.空()
        自身.值=初始

    @staticmethod
    def 空():
        '还没有受控地址时的可保存状态'
        return {
            'entries':[],
            'index':-1,
            'request':None,
            'navigation':{'status':'empty'},
            'failure':None,
        }

    @staticmethod
    def 当前(状态):
        '读当前选中的那条地址'
        if 状态 is None or 状态['index']<0:
            return None
        return 状态['entries'][状态['index']]

    @staticmethod
    def 可后退(状态):
        '网页载体能不能退到上一条已知地址'
        return 状态['navigation']['status']!='unknown' and 状态['index']>0

    @staticmethod
    def 可前进(状态):
        '网页载体能不能进到下一条已知地址'
        return 状态['navigation']['status']!='unknown' and 状态['index']>=0 and 状态['index']<len(状态['entries'])-1

    @property
    def 快照(自身):
        '当前可保存状态'
        return 自身.值

    @property
    def 能后退(自身):
        '这一份历史现在能不能后退'
        return 浏览器导航.可后退(自身.值)

    @property
    def 能前进(自身):
        '这一份历史现在能不能前进'
        return 浏览器导航.可前进(自身.值)

    def 导航(自身,目标):
        '放入受控地址，并丢掉它后面的前进分支'
        条目=list(自身.值['entries'][:自身.值['index']+1])
        条目.append(目标)
        if len(条目)>最大历史条数:
            溢出=len(条目)-最大历史条数
            条目=条目[溢出:]
        return 自身.请求(目标,{**自身.值,'entries':条目,'index':len(条目)-1})

    def 后退(自身):
        '选上一条已知地址。不能退就没有请求'
        if not 自身.能后退:
            return None
        下标=自身.值['index']-1
        目标=自身.值['entries'][下标]
        return 自身.请求(目标,{**自身.值,'index':下标})

    def 前进(自身):
        '选下一条已知地址。不能进就没有请求'
        if not 自身.能前进:
            return None
        下标=自身.值['index']+1
        目标=自身.值['entries'][下标]
        return 自身.请求(目标,{**自身.值,'index':下标})

    def 刷新(自身):
        '再加载最后一条已知地址。还没有地址就没有请求'
        目标=浏览器导航.当前(自身.值)
        if 目标 is None:
            return None
        return 自身.请求(目标,自身.值)

    def 帧已加载(自身,修订):
        '记下这一代文档的一次加载。第一次保持地址已知，再来一次就标成未知'
        导航=自身.值['navigation']
        if 导航['status']=='empty' or 导航.get('revision')!=修订:
            return
        if 导航['status']=='loading':
            自身.值={**自身.值,'navigation':{'status':'known','revision':修订}}
        elif 导航['status']=='known':
            自身.值={**自身.值,'navigation':{'status':'unknown','revision':修订}}

    def 请求(自身,目标,基准):
        '铸造新的加载请求，并写成正在加载'
        旧=自身.值.get('request')
        修订=1 if 旧 is None else 旧['revision']+1
        请求={'revision':修订,'target':目标}
        自身.值={
            **基准,
            'request':请求,
            'navigation':{'status':'loading','revision':请求['revision']},
            'failure':None,
        }
        return 请求
