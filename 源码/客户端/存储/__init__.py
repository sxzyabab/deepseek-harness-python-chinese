"""客户端快照存储引擎。

浅相等、创建快照存储、声明存储。
供各 UI 包 `from ...存储 import ...`。
"""
import builtins,json#localStorage 与 JSON
from types import SimpleNamespace as 简易命名空间#声明句柄

__all__=[#仅中文公开名
    '浅相等',
    '创建快照存储',
    '声明存储',
    '通知订阅者',
    '应用',
]

def 浅相等(甲,乙):
    """引用相同，或同形对象/数组逐项 is 比较。"""
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
    """可选 builtins.localStorage；非浏览器则无。"""
    try:#可选
        return builtins.localStorage#存储
    except AttributeError:#未注入
        return None#无

class 快照存储面:
    """可写快照：getSnapshot / subscribe / update / set；可选 localStorage 持久化。"""
    def __init__(自身,初值,选项=None):
        """记下初值与可选 flush/persist。"""
        选项=选项 or {}#缺省
        自身._状态=初值#当前值
        自身._监听者=set()#订阅者
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
        """返回当前状态引用。"""
        return 自身._状态#状态

    def subscribe(自身,回调):
        """登记变更回调，返回退订。"""
        自身._监听者.add(回调)#加入
        def 退订():
            """取消。"""
            自身._监听者.discard(回调)#删除
        return 退订#退订器

    def update(自身,变换):
        """经草稿变换写状态；dict 就地改，其余把返回值当下一态。"""
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
        """整值替换。"""
        自身._状态=下一#替换
        自身._写出()#持久化
        自身._调度通知()#通知

    def __getitem__(自身,键):
        """兼容 dict 面：store['getSnapshot']。"""
        return getattr(自身,键)#方法

    def _调度通知(自身):
        """sync 立即扇出；raf 合并到下一拍（无 RAF 时退化为 sync）。"""
        if 自身._flush!='raf':#同步
            自身._扇出()#立即
            return
        if 自身._待通知:#已排队
            return#合并
        自身._待通知=True#记下
        def 冲刷():
            """一拍后扇出。"""
            自身._待通知=False
            自身._扇出()#扇出
        调度=getattr(builtins,'requestAnimationFrame',None)#浏览器 RAF
        if callable(调度):#有
            调度(lambda *_:冲刷())#排队
        else:#无 RAF
            冲刷()#立即

    def _扇出(自身):
        """通知全部订阅者；单回调失败不饿死其余。"""
        通知订阅者(自身._监听者,'快照存储')#扇出

    def _再水合(自身):
        """从 localStorage 读回；失败只关掉持久化。"""
        存储=_取本地存储()#可选
        if 存储 is None:#无
            自身._可持久化=False#关
            return
        try:#读
            原始=存储.getItem(自身._持久名)#读串
            if 原始 is not None:#有值
                自身._状态=json.loads(原始)#整值还原
        except (TypeError,ValueError,AttributeError) as 错误:#再水合失败
            print("快照存储 '"+自身._持久名+"' 回灌失败:",错误)#诊断
            自身._可持久化=False#关

    def _写出(自身):
        """写入 localStorage；配额失败只关掉持久化。"""
        if not 自身._可持久化:#已关
            return#跳过
        存储=_取本地存储()#可选
        if 存储 is None:#无
            自身._可持久化=False#关
            return
        try:#写
            存储.setItem(自身._持久名,json.dumps(自身._状态,ensure_ascii=False,separators=(',',':'),allow_nan=False))#整值
        except (TypeError,ValueError,AttributeError,OSError) as 错误:#写失败
            print("快照存储 '"+自身._持久名+"' 持久化失败:",错误)#诊断
            自身._可持久化=False#关

    def clearPersisted(自身):
        """清掉持久化条目；内存态保留。"""
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
    """铸造可写快照存储面。"""
    return 快照存储面(初值,选项)#面

def 声明存储(声明):
    """init / persist / actions → 带 create 的句柄。"""
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
        """铸造引擎实例；作用域键拼进持久化名以隔离会话。"""
        初=声明['init']()#每实例新种子
        本选项=dict(选项)#拷贝
        if 'persist' in 本选项 and 作用域键 is not None:#会话作用域
            名=本选项['persist']['name']#基名
            本选项['persist']={'name':名+':'+str(作用域键)}#按作用域隔离
        仓=创建快照存储(初,本选项 if 本选项 else None)#底层仓
        def 绑(名,函):
            """把草稿变换烤成动作。"""
            def 调用(*位置参数):
                """写草稿并通知。"""
                def 变换(草稿):
                    """调用声明的变换。"""
                    函(草稿,*位置参数)#写
                仓.update(变换)#经引擎
            return 调用#绑定
        动作={名:绑(名,函) for 名,函 in 声明['actions'].items()}#已烤动作
        实例={
            'getSnapshot':仓.getSnapshot,
            'subscribe':仓.subscribe,
            'actions':动作,
            'clearPersisted':仓.clearPersisted,
            'store':仓,
            'scopeKey':作用域键,
        }#实例结束
        return 实例#实例

    return 简易命名空间(spec=声明,create=创建)#句柄：.spec / .create

def 通知订阅者(监听者列表,标签,*参数):
    """逐个通知，单个回调失败不饿死其余。"""
    for 监听 in list(监听者列表):#复制后派发
        try:#单回调
            监听(*参数)#调用
        except Exception as 错误:#订阅者回调契约未定
            print(标签+' 订阅者失败:',错误)#打出

def 应用():
    """本包导出库引擎，无宿主侧行为。"""
    return#空 apply

apply=应用#框架槽
