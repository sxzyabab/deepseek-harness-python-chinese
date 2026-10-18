'无界面的快照存储引擎。状态在 Python，localStorage 仍在浏览器，读到才取回。'
import json,math,threading,types
from ...基础设施.通用工具 import 紧凑json编码#紧凑 JSON，对齐 JSON.stringify
from ..模块.客户端.通告 import 取握手窗口#这次握手传进来的窗口
from . import 约定,异常#同目录模块，导入即执行顶层
from .约定 import (
    可观察快照,
    快照选择器钩子,
    可能快照选择器钩子,
    动作声明,
    已烤动作,
    存储规格,
    存储实例,
    存储句柄,
    存储工厂,
    存储声明,
    句柄提取,
    绑定动作,
    属性存储,
    定义存储,
)#约定别名，对应 index 对 contract 的再导出

简易命名空间=types.SimpleNamespace#带属性的简单对象
方法类型=types.MethodType#绑定方法，用来识别还没接上浏览器的桩
定时器类=threading.Timer#没有浏览器调度时的微任务近似
解析json=json.loads#把 localStorage 里的文本解析成值
浏览器窗口=取握手窗口#这次握手传进来的窗口

__all__=[
    '约定','异常',
    '可观察快照','快照选择器钩子','可能快照选择器钩子','动作声明','已烤动作',
    '存储规格','存储实例','存储句柄','存储工厂','存储声明','句柄提取',
    '绑定动作','属性存储','定义存储',
    '通知订阅者','浅相等','创建快照存储','声明存储',
]

订阅者标签='[client-store]'#诊断前缀，保持上游原文


def 可起草(值):
    '普通字典、列表、集合。类实例不算'
    return type(值) in (dict,list,set)


class 草稿基:
    '草稿的修改标记。子节点一改，父节点也算改'
    def __init__(自身,基,父):
        '记下原值和父草稿'
        自身._基=基
        自身._父=父
        自身._改=False

    def _标改(自身):
        '标成本节点已改，并通知父节点'
        if 自身._改:
            return
        自身._改=True
        if 自身._父 is not None:
            自身._父._标改()


class 对象草稿(草稿基):
    '字典的写时复制草稿。没改过的子键保持原引用'
    def __init__(自身,基,父):
        '记下原字典、覆盖、删除和已打开的子草稿'
        草稿基.__init__(自身,基,父)
        自身._副本={}
        自身._删=set()
        自身._子={}

    def _键列(自身):
        '原顺序在前，新键在后，已删的跳过'
        列=[]
        见过=set()
        for 键 in 自身._基:
            if 键 in 自身._删:
                continue
            列.append(键)
            见过.add(键)
        for 键 in 自身._副本:
            if 键 in 自身._删 or 键 in 见过:
                continue
            列.append(键)
        return 列

    def _包装(自身,键,值):
        '可起草的值包成子草稿，其余原样'
        子=建立草稿(值,自身)
        if 子 is None:
            return 值
        自身._子[键]=子
        return 子

    def __contains__(自身,键):
        '删除优先，其次覆盖，最后看原字典'
        if 键 in 自身._删:
            return False
        if 键 in 自身._副本:
            return True
        return 键 in 自身._基

    def __getitem__(自身,键):
        '读出一个键。字典、列表、集合返回草稿'
        if 键 not in 自身:
            raise KeyError(键)
        if 键 in 自身._子:
            return 自身._子[键]
        if 键 in 自身._副本:
            值=自身._副本[键]
        else:
            值=自身._基[键]
        return 自身._包装(键,值)

    def __setitem__(自身,键,值):
        '写下覆盖。嵌套草稿先收成普通值'
        自身._标改()
        自身._删.discard(键)
        自身._子.pop(键,None)
        自身._副本[键]=剥(值)

    def __delitem__(自身,键):
        '删掉一个键'
        if 键 not in 自身:
            raise KeyError(键)
        自身._标改()
        自身._删.add(键)
        自身._副本.pop(键,None)
        自身._子.pop(键,None)

    def __iter__(自身):
        '按当前键顺序迭代'
        return iter(自身._键列())

    def __len__(自身):
        '当前键的个数'
        return len(自身._键列())

    def get(自身,键,默认=None):
        '没有这个键时返回默认'
        if 键 not in 自身:
            return 默认
        return 自身[键]

    def keys(自身):
        '当前键列表'
        return 自身._键列()

    def values(自身):
        '当前值。可起草的仍是草稿'
        return [自身[键] for 键 in 自身._键列()]

    def items(自身):
        '当前键值对。值可起草时是草稿'
        return [(键,自身[键]) for 键 in 自身._键列()]

    def pop(自身,键,*默认):
        '取出并删除。没有这个键时用默认，否则报 KeyError'
        if 键 not in 自身:
            if len(默认)==0:
                raise KeyError(键)
            return 默认[0]
        if 键 in 自身._子:
            值=自身._子[键].定稿()
        elif 键 in 自身._副本:
            值=自身._副本[键]
        else:
            值=自身._基[键]
        自身._标改()
        自身._删.add(键)
        自身._副本.pop(键,None)
        自身._子.pop(键,None)
        return 值

    def update(自身,*位置参数,**关键字参数):
        '按键写入。字典和草稿按键，其余按对'
        if len(位置参数)>0:
            映射=位置参数[0]
            if isinstance(映射,dict) or isinstance(映射,对象草稿):
                for 键 in list(映射):
                    自身[键]=映射[键]
            else:
                for 键,值 in 映射:
                    自身[键]=值
        for 键,值 in 关键字参数.items():
            自身[键]=值

    def setdefault(自身,键,默认=None):
        '没有这个键就写下默认，并返回当前值'
        if 键 not in 自身:
            自身[键]=默认
        return 自身[键]

    def clear(自身):
        '删掉全部当前键'
        键列=自身._键列()
        自身._标改()
        for 键 in 键列:
            自身._删.add(键)
        自身._副本.clear()
        自身._子.clear()

    def 定稿(自身):
        '没改就交回原字典。改过则新字典，没动的子键保持原引用'
        if not 自身._改:
            return 自身._基
        结果={}
        for 键 in 自身._键列():
            if 键 in 自身._子:
                结果[键]=自身._子[键].定稿()
            elif 键 in 自身._副本:
                结果[键]=自身._副本[键]
            else:
                结果[键]=自身._基[键]
        return 结果


class 数组草稿(草稿基):
    '列表的写时复制草稿'
    def __init__(自身,基,父):
        '记下原列表。副本在第一次结构修改时才拷'
        草稿基.__init__(自身,基,父)
        自身._副本=None
        自身._子={}

    def _源(自身):
        '有副本用副本，否则用原列表'
        if 自身._副本 is not None:
            return 自身._副本
        return 自身._基

    def _规范(自身,下标):
        '把负下标收成正下标。越界抛 IndexError'
        源=自身._源()
        长度=len(源)
        if 下标<0:
            下标=下标+长度
        if 下标<0 or 下标>=长度:
            raise IndexError('list index out of range')
        return 下标

    def _包装(自身,下标,值):
        '可起草的元素包成子草稿'
        子=建立草稿(值,自身)
        if 子 is None:
            return 值
        自身._子[下标]=子
        return 子

    def _落地(自身):
        '结构修改前把已打开的元素收进副本'
        if 自身._副本 is None:
            自身._副本=list(自身._基)
        for 下标,子 in list(自身._子.items()):
            if 0<=下标<len(自身._副本):
                自身._副本[下标]=子.定稿()
        自身._子.clear()
        自身._标改()

    def __len__(自身):
        '当前长度'
        return len(自身._源())

    def __iter__(自身):
        '按当前顺序逐个交出。可起草的是草稿'
        下标=0
        长度=len(自身._源())
        while 下标<长度:
            yield 自身[下标]
            下标=下标+1

    def __getitem__(自身,下标):
        '按下标读。切片返回普通列表'
        if isinstance(下标,slice):
            return list(自身._源()[下标])
        实际=自身._规范(下标)
        if 实际 in 自身._子:
            return 自身._子[实际]
        return 自身._包装(实际,自身._源()[实际])

    def __setitem__(自身,下标,值):
        '替换下标处的元素'
        if isinstance(下标,slice):
            raise TypeError('快照草稿不支持切片赋值')
        自身._落地()
        实际=自身._规范(下标)
        自身._副本[实际]=剥(值)

    def __delitem__(自身,下标):
        '删掉下标处的元素'
        自身._落地()
        实际=自身._规范(下标)
        del 自身._副本[实际]

    def append(自身,值):
        '追加一个元素'
        自身._落地()
        自身._副本.append(剥(值))

    def extend(自身,序列):
        '接上一段'
        自身._落地()
        for 项 in 序列:
            自身._副本.append(剥(项))

    def pop(自身,下标=-1):
        '取出并删掉下标处的元素'
        自身._落地()
        实际=自身._规范(下标)
        return 自身._副本.pop(实际)

    def 定稿(自身):
        '没改就交回原列表。改过则新列表，没动的元素保持原引用'
        if not 自身._改:
            return 自身._基
        if 自身._副本 is None:
            源=list(自身._基)
        else:
            源=list(自身._副本)
        for 下标,子 in 自身._子.items():
            if 0<=下标<len(源):
                源[下标]=子.定稿()
        return 源


class 集合草稿(草稿基):
    '集合的写时复制草稿'
    def __init__(自身,基,父):
        '记下原集合'
        草稿基.__init__(自身,基,父)
        自身._副本=None

    def _源(自身):
        '有副本用副本，否则用原集合'
        if 自身._副本 is not None:
            return 自身._副本
        return 自身._基

    def _确保(自身):
        '第一次修改时拷一份'
        if 自身._副本 is None:
            自身._副本=set(自身._基)
        自身._标改()

    def add(自身,值):
        '加进一个元素'
        自身._确保()
        自身._副本.add(剥(值))

    def discard(自身,值):
        '没有这个元素也不报错'
        自身._确保()
        自身._副本.discard(值)

    def remove(自身,值):
        '没有这个元素就报错'
        自身._确保()
        自身._副本.remove(值)

    def pop(自身):
        '取出任意一个元素'
        自身._确保()
        return 自身._副本.pop()

    def clear(自身):
        '清空'
        自身._确保()
        自身._副本.clear()

    def __contains__(自身,值):
        '当前集合里有没有这个元素'
        return 值 in 自身._源()

    def __iter__(自身):
        '迭代当前元素'
        return iter(set(自身._源()))

    def __len__(自身):
        '当前元素个数'
        return len(自身._源())

    def 定稿(自身):
        '没改就交回原集合'
        if not 自身._改:
            return 自身._基
        return set(自身._副本)


def 建立草稿(基,父):
    '可起草的值包成对应草稿。其余返回 None'
    if type(基) is dict:
        return 对象草稿(基,父)
    if type(基) is list:
        return 数组草稿(基,父)
    if type(基) is set:
        return 集合草稿(基,父)
    return None


def 剥(值):
    '把嵌进去的草稿收成普通值。没有草稿就保持原引用'
    if isinstance(值,对象草稿) or isinstance(值,数组草稿) or isinstance(值,集合草稿):
        return 值.定稿()
    if type(值) is dict:
        新=None
        for 键,项 in 值.items():
            后=剥(项)
            if 后 is not 项:
                if 新 is None:
                    新=dict(值)
                新[键]=后
        if 新 is None:
            return 值
        return 新
    if type(值) is list:
        新=None
        下标=0
        for 项 in 值:
            后=剥(项)
            if 后 is not 项:
                if 新 is None:
                    新=list(值)
                新[下标]=后
            下标=下标+1
        if 新 is None:
            return 值
        return 新
    return 值


def 同值(甲,乙):
    '对应 Object.is。同引用、NaN 与 NaN 为真，正负零分开，布尔不与数字相等'
    if 甲 is 乙:
        return True
    if isinstance(甲,bool) or isinstance(乙,bool):
        return False
    if isinstance(甲,(int,float)) and isinstance(乙,(int,float)):
        if isinstance(甲,float) and 甲!=甲 and isinstance(乙,float) and 乙!=乙:
            return True
        if 甲==0 and 乙==0:
            return math.copysign(1.0,float(甲))==math.copysign(1.0,float(乙))
        return 甲==乙
    if isinstance(甲,str) and isinstance(乙,str):
        return 甲==乙
    return False


def 浅相等(甲,乙):
    '只比一层。对象和数组的子项用同值，更深的不同引用算不等'
    if 同值(甲,乙):
        return True
    if isinstance(甲,dict) and isinstance(乙,dict):
        if len(甲)!=len(乙):
            return False
        for 键 in 甲:
            if 键 not in 乙 or not 同值(甲[键],乙[键]):
                return False
        return True
    if isinstance(甲,(list,tuple)) and isinstance(乙,(list,tuple)):
        if len(甲)!=len(乙):
            return False
        下标=0
        while 下标<len(甲):
            if not 同值(甲[下标],乙[下标]):
                return False
            下标=下标+1
        return True
    if isinstance(甲,set) and isinstance(乙,set):
        if len(甲)!=len(乙):
            return False
        for 项 in 甲:
            if 项 not in 乙:
                return False
        return True
    return False


def 写控制台错误(*数据):
    '写到浏览器 console.error。没有接上浏览器时打印'
    窗口=浏览器窗口()
    错误方法=窗口.console.error
    if callable(错误方法) and not isinstance(错误方法,方法类型):
        try:
            错误方法(*数据)
            return
        except Exception:
            print(*数据)
            return
    print(*数据)


def 通知订阅者(监听集合,标签,*参数):
    '逐个通知。先复制名单，一个回调失败不挡住其余'
    for 监听 in list(监听集合):
        try:
            监听(*参数)
        except Exception as 错误:
            写控制台错误(标签+' subscriber failed:',错误)


def 取本地存储():
    '浏览器 localStorage。还是桩方法时视为不存在，持久化静默关闭'
    窗口=浏览器窗口()
    存储=窗口.localStorage
    读取=存储.getItem
    if not callable(读取) or isinstance(读取,方法类型):
        return None
    return 存储


def 创建快照存储(初值,选项=None):
    '铸造可写快照。默认同步通知；flush 为 raf 时同一拍合并成一次。可选按名持久化'
    状态={'当前':初值}
    监听者=[]
    每次变更=[]
    刷='sync'
    排门闩={'已排':False}
    if 选项 is not None and 选项.get('flush')=='raf':
        刷='raf'
    名=None
    if 选项 is not None and isinstance(选项.get('persist'),dict):
        名=选项['persist'].get('name')
    if 名 is not None:
        存储=取本地存储()
        if 存储 is not None:
            try:
                原始=存储.getItem(名)
                if 原始 is not None:
                    状态['当前']=解析json(原始)
            except Exception as 错误:
                写控制台错误("snapshot store '"+str(名)+"' rehydration failed:",错误)

            def 写出(状态值):
                '每次变更后把整值写回。失败只记日志，不关掉以后的写入'
                try:
                    存储.setItem(名,紧凑json编码(状态值))
                except Exception as 错误:
                    写控制台错误("snapshot store '"+str(名)+"' persistence failed:",错误)

            每次变更.append(写出)

    def 取快照():
        '返回当前状态引用。没变之前一直是同一个对象'
        return 状态['当前']

    def 订阅(回调):
        '登记变更回调，返回退订。同一函数登记两次就是两次'
        监听者.append(回调)

        def 退订():
            '卸下最先登记的那一次'
            try:
                监听者.remove(回调)
            except ValueError as 错误:
                return#已经卸过，不用再报

        return 退订

    def 通知变更():
        '持久化立刻写。同步模式马上通知，raf 把这一拍收成一次'
        for 回调 in list(每次变更):
            回调(状态['当前'])
        if 刷!='raf':
            通知订阅者(监听者,订阅者标签)
            return
        if 排门闩['已排']:
            return
        排门闩['已排']=True

        def 到点(*位置参数):
            '这一拍到了就扇出。扇出前先开门，回调里的新写入可以再排一拍'
            排门闩['已排']=False
            通知订阅者(监听者,订阅者标签)

        窗口=浏览器窗口()
        帧=窗口.requestAnimationFrame
        if callable(帧) and not isinstance(帧,方法类型):
            try:
                帧(到点)
                return
            except Exception as 帧错误:
                帧错误=None#这一路帧调度失败，改走微任务
        微任务=窗口.queueMicrotask
        if callable(微任务) and not isinstance(微任务,方法类型):
            try:
                微任务(到点)
                return
            except Exception as 微任务错误:
                微任务错误=None#微任务也失败，改走定时器
        定时器=定时器类(0,到点)
        定时器.start()

    def 更新(变换):
        '经草稿变换写出下一态。不可起草或没有改动则不通知'
        当前=状态['当前']
        if not 可起草(当前):
            变换(当前)
            return
        根=建立草稿(当前,None)
        变换(根)
        下一=根.定稿()
        if 下一 is 当前:
            return
        状态['当前']=下一
        通知变更()

    def 替换(下一):
        '整值替换'
        if 下一 is 状态['当前']:
            return
        状态['当前']=下一
        通知变更()

    return 简易命名空间(getSnapshot=取快照,subscribe=订阅,update=更新,set=替换)


def 声明存储(声明):
    'init、可选 persist、actions 收成句柄。create 每次给一份新实例'
    def 创建(作用域键=None):
        '播种一份实例。有作用域键时用点号拼进持久化名'
        持久名=声明['persist'] if 'persist' in 声明 else None
        if 持久名 is None:
            持久键=None
            仓=创建快照存储(声明['init']())
        else:
            if 作用域键 is None:
                持久键=持久名
            else:
                持久键=持久名+'.'+str(作用域键)
            仓=创建快照存储(声明['init'](),{'persist':{'name':持久键}})
        动作={}
        for 键 in 声明['actions']:
            变换=声明['actions'][键]

            def 调用(*位置参数,变换=变换):
                '烤好的动作。参数写进草稿，不把草稿交给调用方'
                def 改(草稿):
                    '调用声明里的变换'
                    变换(草稿,*位置参数)

                仓.update(改)

            动作[键]=调用

        def 取快照():
            '读这份实例的当前快照'
            return 仓.getSnapshot()

        def 订阅(回调):
            '订阅这份实例，返回退订'
            return 仓.subscribe(回调)

        def 清除持久化():
            '删掉这一实例的持久化条目。没有键、没有存储或删除失败都只跳过'
            if 持久键 is None:
                return
            存储=取本地存储()
            if 存储 is None:
                return
            try:
                存储.removeItem(持久键)
            except Exception as 错误:
                return#存储失败只跳过清理

        return 简易命名空间(
            actions=动作,
            getSnapshot=取快照,
            subscribe=订阅,
            store=仓,
            clearPersisted=清除持久化,
        )

    return 简易命名空间(spec=声明,create=创建)
