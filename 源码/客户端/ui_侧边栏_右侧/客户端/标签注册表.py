'标签类型登记。扩展可以盖住内建，卸掉后再回来'
import json
import fnmatch
from urllib.parse import urlparse as 解析网址
from ....基础设施.通用工具 import 观察者集合
from ..异常 import 右侧侧栏错误

__all__=['右侧侧栏标签注册表','默认优先级带','优先级秩']

默认优先级带='extension'
优先级秩={'extension':3,'builtin':2,'fallback':1}


def 编译匹配(模式):
    '含冒号匹配整段地址，否则匹配路径；没有斜杠时只匹配文件名'
    整址=':' in 模式
    折=模式.casefold()

    def 测(地址):
        '这一条模式是否认这个地址'
        if 整址:
            return fnmatch.fnmatchcase(地址.casefold(),折)
        try:
            解析=解析网址(地址)
        except ValueError:
            return False
        if 解析.scheme=='':
            return False
        路径=解析.path
        if '/' in 模式:
            return fnmatch.fnmatchcase(路径.casefold(),折)
        基名=路径.rsplit('/',1)[-1]
        return fnmatch.fnmatchcase(基名.casefold(),折)

    return 测


class 右侧侧栏标签注册表:
    '按种类持有生效定义。扩展在场时内建退到影子里'

    def __init__(自身,上下文):
        '登记寿命挂在这个上下文的副作用上'
        自身.上下文=上下文
        自身.种类表={}
        自身.标识集=set()
        自身.监听者=观察者集合()
        自身.登记序=0
        自身.缓存=()
        自身.向导条目=()

    def 登记(自身,定义):
        '登记一种类型，返回拆除器'
        标识=定义['id']
        种类=定义['kind']
        入口表=定义['guide'] if 定义.get('guide') is not None else ()
        入口标识=[入口['id'] for 入口 in 入口表]
        if len(set(入口标识))!=len(入口标识):
            raise 右侧侧栏错误('sidebarRight: duplicate guide entry id in "'+标识+'"')
        带=定义['priority'] if 定义.get('priority') is not None else 默认优先级带
        if 标识 in 自身.标识集:
            raise 右侧侧栏错误('sidebarRight: tab type id "'+标识+'" is already registered')
        持有=自身.种类表.get(种类)
        可共存=持有 is not None and 带!='fallback' and 持有['inForce']['band']!='fallback' and 持有['inForce']['band']!=带 and 持有['shadowed'] is None
        if 持有 is not None and not 可共存:
            raise 右侧侧栏错误('sidebarRight: tab kind "'+种类+'" is already registered ('+持有['inForce']['band']+')')
        自身.登记序+=1
        模式表=定义['patterns'] if 定义.get('patterns') is not None else ()
        条目={
            'definition':定义,
            'band':带,
            'matchers':[{'pattern':模式,'test':编译匹配(模式)} for 模式 in 模式表],
            'order':自身.登记序,
        }

        def 效应():
            '挂进表，卸的时候再摘掉'
            自身.标识集.add(标识)
            槽=自身._进入(种类,条目)
            自身._刷新()

            def 拆除():
                '离开这个种类'
                自身.标识集.discard(标识)
                自身._离开(种类,槽,条目)
                自身._刷新()

            return 拆除

        拆=自身.上下文.副作用(效应,'sidebarRight.tabs.register('+json.dumps(标识)+')')

        def 对外拆除():
            '再拆一次也没有事'
            拆()

        return 对外拆除

    def _进入(自身,种类,条目):
        '更高的带成为生效项'
        持有=自身.种类表.get(种类)
        if 持有 is None:
            槽={'inForce':条目,'shadowed':None}
            自身.种类表[种类]=槽
            return 槽
        if 优先级秩[条目['band']]>优先级秩[持有['inForce']['band']]:
            持有['shadowed']=持有['inForce']
            持有['inForce']=条目
        else:
            持有['shadowed']=条目
        return 持有

    def _离开(自身,种类,槽,条目):
        '影子里的内建重新生效。种类空了就删槽'
        if 槽['inForce'] is not 条目:
            槽['shadowed']=None
            return
        if 槽['shadowed'] is None:
            del 自身.种类表[种类]
            return
        槽['inForce']=槽['shadowed']
        槽['shadowed']=None

    def _生效(自身):
        '生效登记，按登记顺序'
        表=[槽['inForce'] for 槽 in 自身.种类表.values()]
        表.sort(key=lambda 项: 项['order'])
        return 表

    def 条目(自身):
        '生效定义，引用保持稳定直到下一次变更'
        return 自身.缓存

    def 向导(自身):
        '向导入口，按 order'
        return 自身.向导条目

    def 取(自身,种类):
        '这个种类当前生效的定义'
        槽=自身.种类表.get(种类)
        if 槽 is None:
            return None
        return 槽['inForce']['definition']

    def 候选(自身,地址):
        '能打开这个地址的类型，优者在前'
        排名=[]
        for 项 in 自身._生效():
            长度=-1
            for 匹配 in 项['matchers']:
                if 匹配['test'](地址) and len(匹配['pattern'])>长度:
                    长度=len(匹配['pattern'])
            if 长度<0:
                continue
            定义=项['definition']
            if 定义.get('canOpen') is not None and not 定义['canOpen'](地址):
                continue
            排名.append({'definition':定义,'rank':优先级秩[项['band']],'length':长度,'order':项['order']})
        排名.sort(key=lambda 项: (-项['rank'],-项['length'],项['order']))
        return tuple(项['definition'] for 项 in 排名)

    def 认领(自身,地址,种类=None):
        '决定谁来打开。点了种类就不再看模式'
        if 种类 is not None:
            定义=自身.取(种类)
            if 定义 is None:
                from ..异常 import 未登记种类
                未登记种类(种类)
            if 定义.get('canOpen') is not None and not 定义['canOpen'](地址):
                raise 右侧侧栏错误('sidebarRight: tab type "'+种类+'" refuses "'+地址+'"')
            return {'kind':种类,'contentId':地址,'title':定义['title'](地址)}
        排名=自身.候选(地址)
        if len(排名)==0:
            from ..异常 import 无人认领
            无人认领(地址)
        选中=排名[0]
        return {'kind':选中['kind'],'contentId':地址,'title':选中['title'](地址)}

    def 订阅(自身,监听):
        '登记变更回调，返回退订'
        return 自身.监听者.订阅(监听)

    def _刷新(自身):
        '重建缓存并通知'
        生效=自身._生效()
        自身.缓存=tuple(项['definition'] for 项 in 生效)
        入口=[]
        for 定义 in 自身.缓存:
            for 项 in (定义['guide'] if 定义.get('guide') is not None else ()):
                盒子=dict(项)
                盒子['kind']=定义['kind']
                盒子['providerId']=定义['id']
                入口.append(盒子)
        入口.sort(key=lambda 项: 项['order'])
        自身.向导条目=tuple(入口)
        自身.监听者.通知()
