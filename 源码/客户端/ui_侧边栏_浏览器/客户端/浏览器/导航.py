__all__=['最大历史条数','浏览器导航']#仅中文公开名

最大历史条数=100#每标签保留的应用已知条目上限

class 浏览器导航:#URL、历史与可观测状态
    """拥有应用已知 URL 历史与 iframe 观测状态机。"""
    def __init__(自身,初始=None):
        """初始为持久化状态或空状态。"""
        自身.值=浏览器导航.空() if 初始 is None else 初始#当前快照

    @staticmethod
    def 空():
        """标签尚无受控导航目标前的状态。"""
        return {'entries':[],'index':-1,'request':None,'navigation':{'status':'empty'},'failure':None}#空态

    @staticmethod
    def 当前(状态):
        """读已选应用历史条目。"""
        if 状态 is None or 状态['index']<0:#无选
            return None#无
        return 状态['entries'][状态['index']]#当前

    @staticmethod
    def 可后退(状态):
        """Web 载体能否使用前一条应用历史。"""
        return 状态['navigation']['status']!='unknown' and 状态['index']>0#可退

    @staticmethod
    def 可前进(状态):
        """Web 载体能否使用后一条应用历史。"""
        return (状态['navigation']['status']!='unknown'
            and 状态['index']>=0
            and 状态['index']<len(状态['entries'])-1)#可进

    @property
    def 快照(自身):
        """当前不可变可序列化状态。"""
        return 自身.值#快照

    @property
    def 可后退属性(自身):
        """本实例是否可后退。"""
        return 浏览器导航.可后退(自身.值)#可退

    @property
    def 可前进属性(自身):
        """本实例是否可前进。"""
        return 浏览器导航.可前进(自身.值)#可进

    def 导航(自身,目标):
        """加入受控目标并丢弃其陈旧前进分支。返回新加载请求。"""
        条目=list(自身.值['entries'][:自身.值['index']+1])+[目标]#截断前进
        if len(条目)>最大历史条数:#超限
            条目=条目[len(条目)-最大历史条数:]#保留尾
        return 自身._请求(目标,{**自身.值,'entries':条目,'index':len(条目)-1})#请求

    def 后退(自身):
        """选前一条应用已知目标。不可用则 None。"""
        if not 自身.可后退属性:#不可
            return None#无
        下标=自身.值['index']-1#前一条
        目标=自身.值['entries'][下标]#目标
        return 自身._请求(目标,{**自身.值,'index':下标})#请求

    def 前进(自身):
        """选后一条应用已知目标。不可用则 None。"""
        if not 自身.可前进属性:#不可
            return None#无
        下标=自身.值['index']+1#后一条
        目标=自身.值['entries'][下标]#目标
        return 自身._请求(目标,{**自身.值,'index':下标})#请求

    def 刷新(自身):
        """再加载最后一条应用已知目标。无目标则 None。"""
        目标=浏览器导航.当前(自身.值)#当前
        return None if 目标 is None else 自身._请求(目标,自身.值)#请求

    def 地址失败(自身,原因):
        """记录无效地址，不改活动文档状态。"""
        自身.值={**自身.值,'failure':{'kind':'address','reason':原因}}#失败

    def 帧已加载(自身,修订):
        """按捕获修订记录一次帧加载。"""
        导航=自身.值['navigation']#导航态
        if 导航['status']=='empty' or 导航['revision']!=修订:#无关
            return#忽略
        if 导航['status']=='loading':#首次加载
            自身.值={**自身.值,'navigation':{'status':'known','revision':修订}}#已知
        elif 导航['status']=='known':#再次加载
            自身.值={**自身.值,'navigation':{'status':'unknown','revision':修订}}#未知

    def _请求(自身,目标,基准):
        """铸造新加载请求并写入状态。"""
        上一=自身.值['request']#上一请求
        修订=(上一['revision'] if 上一 is not None else 0)+1#晋修订
        请求={'revision':修订,'target':目标}#请求
        自身.值={#新状态
            **基准,
            'request':请求,
            'navigation':{'status':'loading','revision':修订},
            'failure':None,
        }#状态结束
        return 请求#请求
