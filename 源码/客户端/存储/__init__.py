'客户端快照存储引擎'
import json#JSON
import os#只用于从说明里去掉路径和用户名
from ...基础设施.通用工具 import 观察者集合,紧凑json编码

def _失败说明(错误):
    '日志里的失败句。去掉绝对路径、用户名和环境变量，其余原文保留。'
    原文=str(错误)
    屏蔽名=set(os.environ)
    屏蔽值=set()
    for 键 in ('USERNAME','USER','LOGNAME','USERPROFILE','HOME'):
        值=os.environ.get(键)
        if isinstance(值,str) and 值!='':
            屏蔽值.add(值)
            基=os.path.basename(值.rstrip('\\/'))
            if 基!='':
                屏蔽值.add(基)
    for 值 in os.environ.values():
        if isinstance(值,str) and (len(值)>=8 or '\\' in 值 or '/' in 值):
            屏蔽值.add(值)
    留下=[]
    for 词 in 原文.split():
        裸=词.strip('\'"')
        统一=裸.replace('\\','/')
        if 统一.startswith('/') or 统一.startswith('~/') or (len(统一)>2 and 统一[0].isalpha() and 统一[1]==':' and 统一[2]=='/'):
            continue
        if 裸.startswith('$') and len(裸)>1:
            continue
        if len(裸)>2 and 裸.startswith('%') and 裸.endswith('%'):
            continue
        if '=' in 裸 and 裸.split('=',1)[0] in 屏蔽名:
            continue
        if 裸 in 屏蔽名 or 裸 in 屏蔽值 or 统一 in 屏蔽值:
            continue
        含敏感=False
        for 项 in 屏蔽值:
            if len(项)>=3 and 项 in 裸:
                含敏感=True
                break
        if 含敏感:
            continue
        留下.append(词)
    说明=' '.join(留下).strip()
    if 说明!='':
        return 说明
    if isinstance(错误,BaseException):
        return type(错误).__name__
    return 说明

__all__=[#仅中文公开名
    '浅相等',
    '创建快照存储',
    '声明存储',
    '应用',
]

def 浅相等(甲,乙):
    '引用相同，或同形对象/数组逐项 is 比较'
    if 甲 is 乙:#同引用
        return True#相等
    if isinstance(甲,dict) and isinstance(乙,dict):#两边对象
        if len(甲)!=len(乙):#键数不同
            return False#不等
        for 键,值 in 甲.items():#逐键
            if 键 not in 乙 or 乙[键] is not 值:#缺键或值非同引用
                return False#不等
        return True#浅相等
    if isinstance(甲,(list,tuple)) and isinstance(乙,(list,tuple)):#两边数组
        if len(甲)!=len(乙):#长度不同
            return False#不等
        for 下标 in range(len(甲)):#逐项
            if 甲[下标] is not 乙[下标]:#非同引用
                return False#不等
        return True#浅相等
    return False#其余不等

def _取本地存储():
    '可选 localStorage；非浏览器则无'
    try:#可选
        return localStorage#存储
    except NameError:#未注入
        return None#无

class 快照存储面:
    '可写快照：getSnapshot / subscribe / update / set；可选 localStorage 持久化'
    def __init__(自身,初值,选项=None):
        '记下初值与可选 flush/persist'
        if 选项 is None:#缺省；空字典仍是一份选项
            选项={}
        自身._状态=初值#当前值
        自身._监听者=观察者集合()#订阅者
        自身._flush=选项.get('flush') or 'sync'#同步或 raf
        自身._待通知=False#raf 合并门闩
        持久=选项.get('persist')#持久化声明
        自身._持久名=None#键
        if isinstance(持久,dict) and isinstance(持久.get('name'),str):#标准形
            自身._持久名=持久['name']#记下
        elif isinstance(持久,str):#规格简写
            自身._持久名=持久#记下
        自身._可持久化=自身._持久名 is not None#是否尝试持久化
        if 自身._可持久化:#有名则再水合
            自身._再水合()#读回

    def getSnapshot(自身):
        '返回当前状态引用'
        return 自身._状态#状态

    def subscribe(自身,回调):
        '登记变更回调，返回退订'
        return 自身._监听者.订阅(回调)#退订器

    def update(自身,变换):
        '经草稿变换写状态；dict 就地改，其余把返回值当下一态'
        当前=自身._状态#当前
        if isinstance(当前,dict):#可就地
            变换(当前)#草稿变换
        else:#标量等
            下一=变换(当前)#求下一
            if 下一 is not None:#有返回
                自身._状态=下一#替换
        自身._写出()#持久化
        自身._调度通知()#通知

    def set(自身,下一):
        '整值替换'
        自身._状态=下一#替换
        自身._写出()#持久化
        自身._调度通知()#通知

    def __getitem__(自身,键):
        '兼容 dict 面：store[\'getSnapshot\']'
        return getattr(自身,键)#方法

    def _调度通知(自身):
        'sync 立即扇出；raf 合并到下一拍（无 RAF 时退化为 sync）'
        if 自身._flush!='raf':#同步
            自身._扇出()#立即
            return
        if 自身._待通知:#已排队
            return#合并
        自身._待通知=True#记下
        def 冲刷():
            '一拍后扇出'
            自身._待通知=False
            自身._扇出()#扇出
        try:#下一拍
            调度=requestAnimationFrame#浏览器 RAF
        except NameError:#非浏览器
            调度=None#无
        if callable(调度):#有
            调度(lambda *_:冲刷())#排队
        else:#无 RAF
            冲刷()#立即

    def _扇出(自身):
        '通知全部订阅者；单回调失败不饿死其余'
        try:#某回调失败不影响其余
            自身._监听者.通知()#扇出
        except Exception as 错误:#观察者集合在全部回调之后抛出
            内层=错误#汇总异常
            列表=getattr(错误,'错误列表',None)#各回调失败
            if isinstance(列表,list) and len(列表)>0:#有内层
                内层=列表[0]#第一条
            raise RuntimeError('快照存储订阅者失败: '+_失败说明(内层)) from None#说明不含绝对路径

    def _再水合(自身):
        '从 localStorage 读回；失败只关掉持久化'
        存储=_取本地存储()#可选
        if 存储 is None:#无
            自身._可持久化=False#关
            return
        try:#读
            原始=存储.getItem(自身._持久名)#读串
            if 原始 is not None:#有值
                自身._状态=json.loads(原始)#整值还原
        except (TypeError,ValueError,AttributeError) as 错误:#再水合失败
            print("快照存储 '"+自身._持久名+"' 回灌失败:",_失败说明(错误))#说明不含绝对路径
            自身._可持久化=False#关

    def _写出(自身):
        '写入 localStorage；配额失败只关掉持久化'
        if not 自身._可持久化:#已关
            return#跳过
        存储=_取本地存储()#可选
        if 存储 is None:#无
            自身._可持久化=False#关
            return
        try:#写
            存储.setItem(自身._持久名,紧凑json编码(自身._状态))#整值
        except (TypeError,ValueError,AttributeError,OSError) as 错误:#写失败
            print("快照存储 '"+自身._持久名+"' 持久化失败:",_失败说明(错误))#说明不含绝对路径
            自身._可持久化=False#关

    def clearPersisted(自身):
        '清掉持久化条目；内存态保留'
        if 自身._持久名 is None:#无键
            return
        存储=_取本地存储()#可选
        if 存储 is None:#无
            return
        try:#删
            存储.removeItem(自身._持久名)#删键
        except (TypeError,AttributeError,OSError):#忽略
            pass

def 创建快照存储(初值,选项=None):
    '铸造可写快照存储面；返回带 getSnapshot 与 subscribe 方法的对象'
    return 快照存储面(初值,选项)#面

class 存储实例:
    '声明存储的活实例。钩子按属性读 getSnapshot 与 subscribe，不把这两个名字放进字典'
    def __init__(自身,仓,动作,作用域键):
        '记下底层仓、已烤动作与作用域'
        自身.actions=动作#已烤动作
        自身.store=仓#底层仓
        自身.scopeKey=作用域键#作用域；根作用域为 None

    def getSnapshot(自身):
        '读当前快照'
        return 自身.store.getSnapshot()#快照

    def subscribe(自身,回调):
        '订阅变更，返回退订'
        return 自身.store.subscribe(回调)#退订

    def clearPersisted(自身):
        '清掉这份实例的持久化条目'
        自身.store.clearPersisted()#清

    def __getitem__(自身,键):
        '旧调用仍可用方括号；绑定器走的是上面的方法'
        if 键 in ('getSnapshot','subscribe','actions','clearPersisted','store','scopeKey'):#已知键
            return getattr(自身,键)#当前属性
        raise KeyError(键)#未知

class 存储句柄:
    '登记货币。按对象身份做键，spec 与 create 是属性'
    def __init__(自身,规格,创建):
        '记下规格与工厂'
        自身.spec=规格#声明
        自身.create=创建#工厂

def 声明存储(声明):
    'init / persist / actions → 带 create 的句柄'
    if not isinstance(声明,dict):#须为规格表
        raise TypeError('声明存储: 声明必须是字典')
    if 'init' not in 声明 or not callable(声明['init']):#须有播种
        raise TypeError('声明存储: init 必须是零参工厂')
    if 'actions' not in 声明 or not isinstance(声明['actions'],dict):#须有动作表
        raise TypeError('声明存储: actions 必须是字典')
    持久=声明.get('persist')#可选键
    选项={}#快照选项
    if isinstance(持久,str):#简写键
        选项['persist']={'name':持久}#标准形
    elif isinstance(持久,dict):#已是标准
        选项['persist']=持久#透传

    def 创建(作用域键=None):
        '铸造引擎实例；作用域键用点号拼进持久化名'
        初=声明['init']()#每实例新种子
        本选项=dict(选项)#拷贝
        持久项=本选项.get('persist')#可能缺席
        if isinstance(持久项,dict) and isinstance(持久项.get('name'),str) and 作用域键 is not None:#会话作用域
            本选项['persist']={'name':持久项['name']+'.'+str(作用域键)}#与上游点号相同
        仓=创建快照存储(初,本选项 if len(本选项)>0 else None)#空选项不传
        def 绑(名,函):
            '把草稿变换烤成动作'
            def 调用(*位置参数):
                '写草稿并通知'
                def 变换(草稿):
                    '调用声明的变换'
                    函(草稿,*位置参数)#写
                仓.update(变换)#经引擎
            return 调用#绑定
        动作={名:绑(名,函) for 名,函 in 声明['actions'].items()}#已烤动作；空表也保留
        return 存储实例(仓,动作,作用域键)#对象，不是字典

    return 存储句柄(声明,创建)#句柄：.spec / .create

def 应用():
    '本包导出库引擎，无宿主侧行为'
    return#空 apply

apply=应用#框架槽
