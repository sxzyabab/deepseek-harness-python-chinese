"""快照存储引擎：裸可观察源（无 React 钩）。

对齐上游 `runtime/src/client/contract/store.ts`。公开面仅中文名。
Python 侧用深拷贝模拟 immer draft；无 zustand 依赖。
持久化键写入进程内账本（无浏览器 localStorage 时等价静默停用）。
"""
import copy#深拷贝 draft
import json#整值 JSON
import os#环境

__all__=[#仅中文公开名
    '浅相等',
    '创建快照存储',
    '声明存储',
    '进程持久账本',
]#公开面结束

进程持久账本={}#进程内持久化（对齐 localStorage 键值）

def 浅相等(甲,乙):#浅相等
    """选择器切片的浅相等。"""
    if 甲 is 乙:#同引用
        return True#相等
    if type(甲) is not type(乙):#类型不同
        return False#不等
    if isinstance(甲,(list,tuple)):#序列
        if len(甲)!=len(乙):#长度
            return False#不等
        return all(甲[i] is 乙[i] or 甲[i]==乙[i] for i in range(len(甲)))#逐元
    if isinstance(甲,dict):#映射
        if 甲.keys()!=乙.keys():#键集
            return False#不等
        return all(甲[键] is 乙[键] or 甲[键]==乙[键] for 键 in 甲)#逐值
    return 甲==乙#标量

def 深冻(值):#递归冻结（开发态语义；Python 用只读约定）
    """开发态深冻；生产不冻。"""
    if os.environ.get('NODE_ENV')=='production':#生产
        return 值#不冻
    return 值#Python 无 Object.freeze；保留引用约定

class 快照存储:#可写快照存储
    """裸数据面：读快照 / 订阅 / draft 更新 / 整份替换。"""

    def __init__(自身,初值,选项=None):#初始状态与选项
        """flush 默认 sync；persist 名可选。"""
        选项=选项 or {}#缺省
        自身._状态=copy.deepcopy(初值)#当前状态
        自身._监听们=set()#订阅者
        自身._冲洗=选项.get('flush','sync')#flush 模式
        自身._持久名=None#持久键
        持久=选项.get('persist')#可选持久
        if 持久 is not None:#有持久声明
            自身._持久名=持久.get('name') if isinstance(持久,dict) else None#取出名
            自身._挂持久化()#回灌并订阅写入

    def 取快照(自身):#读当前状态
        """返回当前状态引用。"""
        return 自身._状态#当前

    def 订阅(自身,回调):#订阅
        """登记变更回调；返回退订。"""
        自身._监听们.add(回调)#加入
        def 退订():#退订
            自身._监听们.discard(回调)#删除
        return 退订#退订器

    def 更新(自身,变换):#draft 更新
        """经深拷贝 draft 变更状态。"""
        草稿=copy.deepcopy(自身._状态)#draft
        变换(草稿)#就地改
        自身._状态=草稿#整份替换
        自身._通知()#通知

    def 设(自身,下一):#整份替换
        """整份替换状态。"""
        自身._状态=深冻(copy.deepcopy(下一))#冻后写入
        自身._通知()#通知

    def _通知(自身):#通知监听器
        """同步通知全部订阅者。"""
        for 回调 in list(自身._监听们):#逐个
            回调()#回调
        if 自身._持久名 is not None:#要持久
            自身._写持久()#写入账本

    def _挂持久化(自身):#挂持久化
        """从进程账本回灌。"""
        名=自身._持久名#键
        if 名 is None:#无键
            return#停用
        原文=进程持久账本.get(名)#读已存
        if 原文 is None:#无旧值
            return#跳过
        try:#尝试回灌
            自身._状态=json.loads(原文)#回灌
        except Exception:#解析失败
            pass#只停持久，不弄坏存储

    def _写持久(自身):#写持久
        """整值 JSON 写入进程账本。"""
        名=自身._持久名#键
        if 名 is None:#无键
            return#停用
        try:#尝试持久
            进程持久账本[名]=json.dumps(自身._状态,ensure_ascii=False)#整值
        except Exception:#序列化失败
            pass#非致命

def 创建快照存储(初值,选项=None):#创建快照存储
    """创建一台快照存储。"""
    return 快照存储(初值,选项)#实例

def 声明存储(规格):#声明 store
    """init / persist / actions → 句柄（create 收窄到引擎实例）。"""
    def 创建(作用域键=None):#按作用域创建
        持久声明=规格.get('persist')#可选持久键
        持久键=None#解析后的键
        if 持久声明 is not None:#有持久
            持久键=持久声明 if 作用域键 is None else str(持久声明)+'.'+str(作用域键)#根用原键，会话加后缀
        初值函数=规格['init']#播种
        存储=创建快照存储(初值函数(),{'persist':{'name':持久键}} if 持久键 is not None else None)#造引擎
        动作表={}#烤后动作
        for 键,变换 in (规格.get('actions') or {}).items():#每个声明动作
            def 绑(变换_=变换):#绑到 update
                def 调用(*参数):#动作入口
                    存储.更新(lambda 草稿:变换_(草稿,*参数))#draft 变换
                return 调用#已烤
            动作表[键]=绑()#写入
        def 清持久():#清持久
            if 持久键 is None:#无键
                return#跳过
            进程持久账本.pop(持久键,None)#丢掉条目
        return {#引擎实例
            'actions':动作表,#已烤动作
            'getSnapshot':存储.取快照,#读快照
            'subscribe':存储.订阅,#订阅
            'store':存储,#裸存储
            'clearPersisted':清持久,#清持久
        }#实例结束
    return {'spec':规格,'create':创建}#句柄
