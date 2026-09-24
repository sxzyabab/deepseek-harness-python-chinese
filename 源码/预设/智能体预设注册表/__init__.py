import threading
from weakref import WeakKeyDictionary as 弱键字典
import yaml
from ...依赖.include import 插件列表写出器
from ...内核.作用域 import 创建作用域,获取作用域,绑定作用域父
from ...typert.协议 import 远程服务,远程 as _远程
from .类型 import 远程错误,预设注册表错误
from .预设 import 配置
from .会话 import 智能体预设投影定义
from .定义 import 条目列表问题
from .挂载 import (
    审计表行列表,实时预设挂载表,已泄漏服务列表,获取智能体服务,常驻挂载,挂载预设,
)
from .组合清单 import 定义组合体,已挂载组合体表行列表

__all__=[
    '包名','名称','依赖','默认','配置','智能体预设注册表','智能体预设信息',
    '智能体预设投影定义','条目列表问题',
    '审计表行列表','实时预设挂载表','已泄漏服务列表','获取智能体服务','常驻挂载',
    '定义组合体','已挂载组合体表行列表',
]

包名='@deepseek-ai/dsh-agent-preset-registry'
名称='agent-preset-registry'
依赖=['加载器','sessionProjections']

class 智能体预设信息:
    """一条声明的当前元数据。"""
    def __init__(自身,标识,名称=None,描述=None,次序=None,损坏=None):
        """记下标识与可选展示字段。"""
        自身.id=标识
        if 名称 is not None:
            自身.name=名称
        if 描述 is not None:
            自身.description=描述
        if 次序 is not None:
            自身.order=次序
        if 损坏 is not None:
            自身.broken=损坏

def 未知预设(标识,可用):
    """名册里没有该标识。"""
    return 远程错误(
        'agent-preset/not-found',
        '未知智能体预设: '+str(标识),
        {'agentPreset':标识,'available':可用},
    )

class 智能体预设注册表(远程服务):
    """YAML 声明的预设与智能体持留的修订。"""
    def __init__(自身,上下文,配置值=None):
        """登记投影、可选设置页关闭，并转发选中事件。"""
        super().__init__(上下文,'agentPresets')
        if 配置值 is None:
            配置值={}
        自身.配置=配置值
        自身._拥有=上下文
        自身._定义表={}
        自身._世代表=弱键字典()
        自身._绑定表=弱键字典()
        自身._切换锁={}
        自身._切换表锁=threading.Lock()
        上下文.sessionProjections.登记(智能体预设投影定义)
        def 接线(子上下文):
            """设置服务在场时关掉本纤程的自动配置页。"""
            def 效果():
                """进行配置返回拆除器。"""
                return 子上下文.settings.进行配置({'auto':False},上下文.纤程)
            子上下文.副作用(效果)
        上下文.依赖启动(['settings'],接线)
        def 会话事件(会话,事件,*剩余):
            """把选中记录扇出成进程事件。"""
            if 事件['type']!='agent-preset/selected':
                return
            上下文.广播('agent-preset/selected',会话.id,事件['data']['agentPreset'])
        上下文.监听('session/event',会话事件)

    @property
    def 默认标识(自身):
        """随后创建的会话使用的默认预设。"""
        return 自身._策略()['defaultId']

    def _策略(自身):
        """选择器可见性与当前默认标识。"""
        已启用=自身.配置['modeSelectionEnabled'] if 'modeSelectionEnabled' in 自身.配置 else True
        部署默认=自身.配置['default']
        if not 已启用:
            return {'enabled':False,'defaultId':部署默认}
        已选=自身.配置['selectedDefault'] if 'selectedDefault' in 自身.配置 else None
        return {'enabled':True,'defaultId':部署默认 if 已选 is None else 已选}

    def 注册(自身,定义):
        """登记并立即激活；失败留在名册诊断里。"""
        标识=定义['id']
        if 标识.strip()=='':
            raise 预设注册表错误('预设标识不得为空')
        if 标识 in 自身._定义表:
            raise 预设注册表错误('重复的智能体预设: '+标识)
        记录={'config':定义,'context':自身.ctx}
        自身._定义表[标识]=记录
        已拆除=[False]
        自身._激活(记录)
        def 注销():
            """摘掉声明并退役仍无用户的世代。"""
            if 已拆除[0]:
                return
            已拆除[0]=True
            自身._定义表.pop(标识,None)
            if 'generation' in 记录:
                记录['generation']['retired']=True
                自身._收集(记录['generation'])
        return 注销

    def _激活(自身,记录):
        """在注册表作用域下装一棵修订。"""
        键=object()
        作用域对象=创建作用域(自身._拥有,键)
        try:
            问题=条目列表问题(记录['config']['plugins'])
            if 问题 is not None:
                raise 预设注册表错误(问题)
            声明上下文=记录['context']
            子上下文=作用域对象.上下文.扩展({'基准网址':声明上下文.基准网址})
            挂载=挂载预设(子上下文,记录['config']['id'],记录['config']['plugins'])
            世代={
                'scope':作用域对象,
                'key':键,
                'mount':挂载,
                'users':0,
                'retired':False,
            }
            自身._世代表[键]=世代
            记录['generation']=世代
        except BaseException as 错误:
            记录['broken']=str(错误)
            自身._拥有.日志.警告('智能体预设 '+记录['config']['id']+': '+记录['broken'])
            作用域对象.拆除()

    def _诊断(自身,记录):
        """挂载失败为终态；已挂载树每次读取再审计。"""
        if 'generation' not in 记录:
            return 记录['broken'] if 'broken' in 记录 else None
        树=记录['generation']['mount']['tree']
        审计=审计表行列表(树)
        if len(审计['pending'])>0:
            自身._拥有.加载器.等待()
            审计=审计表行列表(树)
        行列表=审计['failed']+审计['pending']
        if len(行列表)==0:
            return None
        return '\n'.join(行列表)

    def _收集(自身,世代):
        """已退役且无用户则拆掉作用域。"""
        if not 世代['retired'] or 世代['users']!=0:
            return
        自身._世代表.pop(世代['key'],None)
        世代['scope'].拆除()

    def 列出(自身):
        """全部声明，含激活失败。"""
        行列表=[]
        for 记录 in 自身._定义表.values():
            配置行=记录['config']
            损坏=自身._诊断(记录)
            项=智能体预设信息(
                配置行['id'],
                名称=配置行['name'] if 'name' in 配置行 else None,
                描述=配置行['description'] if 'description' in 配置行 else None,
                次序=配置行['order'] if 'order' in 配置行 else None,
                损坏=损坏,
            )
            行列表.append(项)
        def 排序键(项):
            """次序缺席视为正无穷，再按标识。"""
            次序=项.order if hasattr(项,'order') else float('inf')
            return (次序,项.id)
        行列表.sort(key=排序键)
        return 行列表

    @_远程('list')
    def 远程列出(自身):
        """名册与选择器策略。"""
        策略=自身._策略()
        预设列表=[]
        for 项 in 自身.列出():
            行={'id':项.id,'isDefault':项.id==策略['defaultId']}
            if hasattr(项,'name'):
                行['name']=项.name
            if hasattr(项,'description'):
                行['description']=项.description
            if hasattr(项,'order'):
                行['order']=项.order
            if hasattr(项,'broken'):
                行['broken']=项.broken
            预设列表.append(行)
        return {'presets':预设列表,'modeSelectionEnabled':策略['enabled']}

    def resolve(自身,标识=None):
        """不启动智能体，只读当前元数据。"""
        目标=自身.默认标识 if 标识 is None else 标识
        记录=自身._定义表.get(目标)
        if 记录 is None:
            raise 未知预设(目标,list(自身._定义表.keys()))
        损坏=自身._诊断(记录)
        return 智能体预设信息(目标,损坏=损坏)

    @_远程('read')
    def 读取文档(自身,智能体预设):
        """把子插件列表按条目列表方言写成 YAML，只供查看。"""
        记录=自身._定义表.get(智能体预设)
        if 记录 is None:
            raise 未知预设(智能体预设,list(自身._定义表.keys()))
        配置行=记录['config']
        内容=yaml.dump(
            配置行['plugins'],Dumper=插件列表写出器,
            allow_unicode=True,sort_keys=False,width=2147483647,
        )
        结果={'agentPreset':配置行['id'],'content':内容}
        if 'name' in 配置行:
            结果['name']=配置行['name']
        if 'description' in 配置行:
            结果['description']=配置行['description']
        return 结果

    def _持留(自身,标识=None):
        """对当前可用修订加用户计数。"""
        目标=自身.默认标识 if 标识 is None else 标识
        while True:
            记录=自身._定义表.get(目标)
            if 记录 is None:
                raise 未知预设(目标,list(自身._定义表.keys()))
            损坏=自身._诊断(记录)
            if 自身._定义表.get(目标) is not 记录:
                continue
            if 损坏 is not None or 'generation' not in 记录:
                原因=损坏 if 损坏 is not None else ''
                raise 远程错误(
                    'agent-preset/invalid',
                    原因,
                    {'agentPreset':目标,'reason':原因},
                )
            世代=记录['generation']
            世代['users']+=1
            return 世代

    def _绑定(自身,上下文,世代):
        """把智能体作用域接到该修订。"""
        键=获取作用域(上下文)
        if 键 is None:
            raise 预设注册表错误('智能体预设绑定需要带作用域的上下文')
        绑定=自身._绑定表.get(键)
        if 绑定 is not None and 绑定['generation'] is 世代:
            return
        if 绑定 is not None:
            绑定['parent'].改接(世代['key'])
            旧=绑定['generation']
            世代['users']+=1
            绑定['generation']=世代
            旧['users']-=1
            自身._收集(旧)
            return
        自身._接入(上下文,键,世代)

    def _接入(自身,上下文,键,世代):
        """第一次把作用域接到修订。"""
        绑定={'parent':绑定作用域父(键,世代['key']),'generation':世代}
        世代['users']+=1
        自身._绑定表[键]=绑定
        def 拆除效果():
            """作用域拆除时放掉引用。"""
            def 清理():
                """减用户并收集。"""
                自身._绑定表.pop(键,None)
                绑定['generation']['users']-=1
                自身._收集(绑定['generation'])
            return 清理
        上下文.副作用(拆除效果,'agent-preset.binding')

    def mount(自身,上下文,标识=None):
        """把未发布智能体接到当前修订。"""
        世代=自身._持留(标识)
        try:
            自身._绑定(上下文,世代)
            return 智能体预设信息(世代['mount']['presetId'])
        finally:
            世代['users']-=1
            自身._收集(世代)

    def composeFrom(自身,上下文,父上下文):
        """子智能体加入父智能体同一修订。"""
        已挂=常驻挂载(父上下文)
        if 已挂 is None:
            return None
        世代=自身._世代表.get(已挂['key'])
        if 世代 is None:
            raise 预设注册表错误('父预设修订已不可用')
        键=获取作用域(上下文)
        if 键 is None:
            raise 预设注册表错误('子预设绑定需要作用域')
        if 键 in 自身._绑定表:
            raise 预设注册表错误('子智能体已经加入过预设')
        自身._接入(上下文,键,世代)
        return 已挂['presetId']

    def composedPreset(自身,上下文):
        """活智能体正在使用的预设标识。"""
        已挂=常驻挂载(上下文)
        if 已挂 is None:
            return None
        return 已挂['presetId']

    def serviceFor(自身,智能体,名称):
        """读智能体所在预设隔离域里的服务。"""
        return 获取智能体服务(自身._拥有,智能体,名称)

    def 重组(自身,上下文,标识):
        """空白智能体改接到另一预设。"""
        预设=自身.mount(上下文,标识)
        try:
            自身._拥有.广播('tools/change')
        except BaseException as 错误:
            自身._拥有.日志.警告('预设工具观察者: '+str(错误))
        return 预设

    def _取切换锁(自身,标识):
        """每个智能体一把选择互斥锁。"""
        with 自身._切换表锁:
            if 标识 not in 自身._切换锁:
                自身._切换锁[标识]=threading.Lock()
            return 自身._切换锁[标识]

    @_远程('select')
    def 选择(自身,智能体,智能体预设):
        """首回合前选定预设并写入会话日志。"""
        锁=自身._取切换锁(智能体.id)
        锁.acquire()
        try:
            边界=自身._拥有.sessionProjections.状态(智能体.session,'turnBoundary')
            if 边界 is not None and (
                    边界['openTurnStartSeq'] is not None or 边界['lastTurn']>0):
                raise 远程错误(
                    'agent-preset/locked',
                    '此会话已经开始',
                    {'sessionId':智能体.id,'agentPreset':智能体预设},
                )
            预设=自身.重组(智能体.ctx,智能体预设)
            智能体.session.追加('agent-preset/selected',{'agentPreset':预设.id})
            return 预设.id
        finally:
            锁.release()

    def 取得作用域(自身,标识=None):
        """冷记录展示用的修订租约。"""
        世代=自身._持留(标识)
        已拆除=[False]
        def 拆除():
            """放掉租约。"""
            if 已拆除[0]:
                return
            已拆除[0]=True
            世代['users']-=1
            自身._收集(世代)
        return {'key':世代['key'],'拆除':拆除}

    def 组合体库存清单(自身):
        """不创建智能体，读各声明的插件行。"""
        结果=[]
        默认=自身.默认标识
        for 记录 in 自身._定义表.values():
            配置行=记录['config']
            损坏=自身._诊断(记录)
            def 拒绝求值(表达式):
                """未激活声明不得求值禁用表达式。"""
                raise 预设注册表错误('未激活的声明')
            读取=定义组合体(配置行['plugins'],拒绝求值)
            项={
                'id':配置行['id'],
                'isDefault':配置行['id']==默认,
                'rows':[] if 'generation' not in 记录 else 已挂载组合体表行列表(记录['generation']['mount']['tree']),
            }
            if 'name' in 配置行:
                项['name']=配置行['name']
            if 'description' in 配置行:
                项['description']=配置行['description']
            if 损坏 is not None:
                项['broken']=损坏
            if 'generation' not in 记录:
                项['rows']=读取['rows'] if 'rows' in 读取 else []
            结果.append(项)
        return 结果

默认=智能体预设注册表
Config=配置
name=名称
inject=依赖
default=默认
智能体预设注册表.inject=依赖
智能体预设注册表.Config=配置
