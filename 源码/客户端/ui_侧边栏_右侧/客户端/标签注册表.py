import fnmatch#通配
from urllib.parse import urlparse#路径提取

__all__=['右侧侧栏标签注册表','默认优先级带','优先级秩']#仅中文公开名

默认优先级带='extension'#未声明时的带
优先级秩={'extension':3,'builtin':2,'fallback':1}#带秩


def _通知订阅者(监听者列表,标签,*参数):
    """逐个通知，单个回调失败不饿死其余。"""
    for 监听 in list(监听者列表):#复制后派发
        try:#单回调
            监听(*参数)#调用
        except Exception as 错误:#订阅者回调契约未定
            print(标签+' 订阅者失败:',错误)#打出


def _路径于(地址):
    """URI 路径；非绝对 URI 则无。"""
    解析=urlparse(地址)#解析
    if 解析.scheme=='':#非 URI
        return None#无
    return 解析.path#路径


def _匹配器(模式):
    """编译一声明模式：含 `:` 整址；否则路径或基名（`*.md`→基名）。"""
    整址=':' in 模式#含方案分隔
    折=模式.casefold()#折

    def 测(地址):
        """测地址。"""
        if 整址:#整址
            return fnmatch.fnmatchcase(地址.casefold(),折)#匹配
        路径=_路径于(地址)#路径
        if 路径 is None:#非 URI
            return False#否
        if '/' in 模式:#路径型
            return fnmatch.fnmatchcase(路径.casefold(),折)#路径
        基=路径.rsplit('/',1)[-1]#末段
        return fnmatch.fnmatchcase(基.casefold(),折)#基名

    return 测#可调用


def _可共存(槽,带):
    """extension 与 builtin 可一对；fallback 独占。"""
    return 带!='fallback' and 槽['inForce']['band']!='fallback' and 槽['inForce']['band']!=带 and 槽['shadowed'] is None#可


class 右侧侧栏标签注册表:#标签类型登记表
    """按种类持生效定义；扩展可暂替内建。"""

    def __init__(自身,上下文):
        """记下上下文（effect 拥有登记寿命）。"""
        自身.上下文=上下文#上下文
        自身.种类表={}#kind → 槽
        自身.标识集=set()#id 集
        自身.监听者=set()#订阅
        自身.登记序=0#全局序
        自身.缓存=()#entries 稳定引用
        自身.向导条目=()#guide 稳定引用

    def 登记(自身,定义):
        """登记一类型；返回幂等拆除器。"""
        标识=定义['id']#实现 id
        种类=定义['kind']#种类
        带=定义['priority'] if 'priority' in 定义 and 定义['priority'] is not None else 默认优先级带#带
        if 标识 in 自身.标识集:#撞 id
            raise Exception('sidebarRight: 标签类型 id "'+标识+'" 已经登记')#接线错误
        持=自身.种类表[种类] if 种类 in 自身.种类表 else None#已持
        if 持 is not None and not _可共存(持,带):#不可共存
            raise Exception('sidebarRight: 标签种类 "'+种类+'" 已经登记 ('+持['inForce']['band']+')')#拒绝
        自身.登记序+=1#序
        模式列表=定义['patterns'] if 'patterns' in 定义 and 定义['patterns'] is not None else ()#模式
        条目={#已登记
            'definition':定义,
            'band':带,
            'matchers':[{'pattern':模,'test':_匹配器(模)} for 模 in 模式列表],
            'order':自身.登记序,
        }#条目

        def 效应():
            """挂入并刷新。"""
            自身.标识集.add(标识)#id
            槽=自身._进入(种类,条目)#进槽
            自身._刷新()#刷新
            def 拆除():
                """离开。"""
                自身.标识集.discard(标识)#id
                自身._离开(种类,槽,条目)#离
                自身._刷新()#刷新
            return 拆除#拆除器

        拆=自身.上下文.副作用(效应,'sidebarRight.tabs.register('+repr(标识)+')')#效应

        def 对外拆除():
            """幂等。"""
            拆()#拆
        return 对外拆除#拆除器

    def _进入(自身,种类,条目):
        """写入种类槽。"""
        持=自身.种类表[种类] if 种类 in 自身.种类表 else None#已持
        if 持 is None:#新槽
            槽={'inForce':条目,'shadowed':None}#槽
            自身.种类表[种类]=槽#写
            return 槽#槽
        if 优先级秩[条目['band']]>优先级秩[持['inForce']['band']]:#更高带
            持['shadowed']=持['inForce']#影
            持['inForce']=条目#效
        else:#较低带
            持['shadowed']=条目#影
        return 持#槽

    def _离开(自身,种类,槽,条目):
        """移出；影恢复或删槽。"""
        if 槽['inForce'] is not 条目:#影离
            槽['shadowed']=None#清影
        elif 槽['shadowed'] is None:#无影
            del 自身.种类表[种类]#删槽
        else:#恢复影
            槽['inForce']=槽['shadowed']#恢复
            槽['shadowed']=None#清

    def _生效(自身):
        """生效登记，按登记序。"""
        列表=[槽['inForce'] for 槽 in 自身.种类表.values()]#表
        列表.sort(key=lambda 项:项['order'])#序
        return 列表#列表

    def 条目(自身):
        """生效定义，引用稳定。"""
        return 自身.缓存#缓存

    def 向导(自身):
        """向导入口盒，按 order。"""
        return 自身.向导条目#缓存

    def 取(自身,种类):
        """生效定义或 None。"""
        槽=自身.种类表[种类] if 种类 in 自身.种类表 else None#槽
        if 槽 is None:#无
            return None#无
        return 槽['inForce']['definition']#定义

    def 候选(自身,地址):
        """认领候选，优者在前。"""
        排名=[]#表
        for 项 in 自身._生效():#逐生效
            定义=项['definition']#定义
            长度=-1#最长命中
            for 匹配 in 项['matchers']:#模式
                if 匹配['test'](地址) and len(匹配['pattern'])>长度:#更长
                    长度=len(匹配['pattern'])#记
            if 长度<0:#未认
                continue#跳
            可开=定义['canOpen'] if 'canOpen' in 定义 else None#否决
            if 可开 is not None and not 可开(地址):#否
                continue#跳
            排名.append({'definition':定义,'rank':优先级秩[项['band']],'length':长度,'order':项['order']})#记
        排名.sort(key=lambda 甲:(-甲['rank'],-甲['length'],甲['order']))#排
        return tuple(项['definition'] for 项 in 排名)#定义序

    def 认领(自身,地址,种类=None):
        """决定谁开；无认领则抛接线错误。"""
        if 种类 is not None:#点名
            定义=自身.取(种类)#定义
            if 定义 is None:#无
                raise Exception('sidebarRight: 没有标签类型登记为 "'+种类+'"')#拒绝
            可开=定义['canOpen'] if 'canOpen' in 定义 else None#否决
            if 可开 is not None and not 可开(地址):#拒
                raise Exception('sidebarRight: 标签类型 "'+种类+'" 拒绝 "'+地址+'"')#拒绝
            return {'kind':种类,'contentId':地址,'title':定义['title'](地址)}#认领
        候选表=自身.候选(地址)#候选
        if len(候选表)==0:#无
            raise Exception('sidebarRight: 没有已登记的标签类型认领 "'+地址+'"')#拒绝
        选=候选表[0]#优
        return {'kind':选['kind'],'contentId':地址,'title':选['title'](地址)}#认领

    def 订阅(自身,监听):
        """低频变更。"""
        自身.监听者.add(监听)#加
        def 退订():
            """退。"""
            自身.监听者.discard(监听)#删
        return 退订#退订器

    def _刷新(自身):
        """重建缓存并通知。"""
        自身.缓存=tuple(项['definition'] for 项 in 自身._生效())#定义
        盒=[]#向导盒
        for 定义 in 自身.缓存:#逐类型
            条目表=定义['guide'] if 'guide' in 定义 and 定义['guide'] is not None else ()#入口
            for 条目 in 条目表:#逐入口
                盒.append({**条目,'kind':定义['kind']})#带 kind
        盒.sort(key=lambda 项:项['order'])#序
        自身.向导条目=tuple(盒)#稳定
        _通知订阅者(自身.监听者,'[ui-sidebar-right] tab registry')#通知
