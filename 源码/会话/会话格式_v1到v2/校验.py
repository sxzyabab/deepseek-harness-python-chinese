"""已发布 v2 逻辑产物校验与当代恢复。"""
import json,os#JSON与绝对路径
from ...模型后端.llm import 块组装器,展开助手流#块装配与流展开
from ...工具.值 import 深相等json#深度相等
from ..会话格式 import (#从会话格式导入
    会话格式错误,#格式错误
    会话格式不支持迁移错误,#不支持迁移
    会话格式计数,#格式计数
    会话格式安全整数,#安全整数
    快照会话格式json,#快照JSON
)#从会话格式导入
from ..会话格式_v0到v1 import (#从v0到v1导入
    断言已发布产物关系,#断言关系
    断言已发布载荷语义,#断言载荷语义
    断言已发布表面元数据,#断言表面元数据
)#从v0到v1导入
from .处置 import 已发布v2事件处置,已发布v2事件类型#从处置导入

头必填=('version','id','createdAt','isSeeded','delegationDepth')#头必填
头可选=('cwd','parentSession','origin','agentPreset')#头可选
事件必填=('type','seq','time','data')#事件必填
表面类型=frozenset(['user/message','assistant/message','tool/result'])#表面类型
表面可选=('ignorable','sourceEventSeqs','surfaceOp')#表面可选
日志可选=('ignorable',)#日志可选
已发布v2事件类型集=frozenset(已发布v2事件类型)#v2类型集
已发布v2关系扩展={#关系扩展
    'stepEvents':frozenset(['assistant/attempt']),#步骤事件
    'preservedSourceTitleRequestText':True,#保留标题请求文本
}#扩展结束

def 断言已发布v2头(头):#断言v2头
    """校验已发布 v2 写出的精确逻辑头。"""
    记录=json记录(头,'format v2 header')#记录
    精确键(记录,头必填,头可选,'format v2 header')#精确键
    if 记录['version']!=2:#版本
        raise 会话格式错误('expected format v2 header')#版本
    if not isinstance(记录['id'],str):#id
        raise 会话格式错误('format v2 header id must be a string')#id
    会话格式计数(记录['createdAt'],'format v2 header createdAt')#创建时间
    会话格式计数(记录['delegationDepth'],'format v2 header delegationDepth')#委托深度
    if not isinstance(记录['isSeeded'],bool):#种子
        raise 会话格式错误('format v2 header isSeeded must be boolean')#种子
    if 'cwd' in 记录 and (not isinstance(记录['cwd'],str) or not os.path.isabs(记录['cwd'])):#cwd非法
        raise 会话格式错误('format v2 header cwd must be absolute')#错误
    for 键 in ('parentSession','agentPreset'):#可选字符串
        if 键 in 记录 and not isinstance(记录[键],str):#类型不符
            raise 会话格式错误(f'format v2 header {键} must be a string')#错误
    if 'origin' in 记录 and 记录['origin']!='subagent':#origin非法
        raise 会话格式错误('format v2 header origin must be "subagent"')#错误

def 断言已发布v2产物(产物):#断言v2产物
    """校验已发布 v2 写出器发出的精确逻辑镜像。"""
    校验已发布v2产物(产物,'target',已发布v2事件类型集)#目标模式

def 断言已发布v2物理产物(产物):#断言物理产物
    """仅校验已发布 v2 物理头、事件信封与继承切割。"""
    校验已发布v2产物(产物,'physical')#物理模式

def 校验已发布v2产物(产物,模式,已知事件类型=None):#校验v2产物
    """按目标、当代或物理模式校验产物。"""
    断言已发布v2头(产物['header'])#断言头
    切割=会话格式计数(产物['inheritedEventCount'],'format v2 inherited event count')#切割
    if 切割>len(产物['events']):#越界
        raise 会话格式错误('format v2 inherited event count exceeds its events')#越界
    if not 产物['header']['isSeeded'] and 切割!=0:#非种子
        raise 会话格式错误('unseeded format v2 Session has inherited events')#非种子
    最后继承标记=None#最后继承标记
    for 下标,事件 in enumerate(产物['events']):#遍历事件
        记录=json记录(事件,f'format v2 event {下标}')#记录
        类型=记录['type']#类型
        if not isinstance(类型,str):#类型须串
            raise 会话格式错误(f'format v2 event {下标} type must be a string')#类型须串
        处置=已发布v2事件处置.get(类型)#处置
        已安装=已知事件类型 is not None and 类型 in 已知事件类型#已安装
        可忽略未知=(处置 is None#可忽略未知
            and 模式=='current'#当代模式
            and 记录.get('ignorable') is True)#可忽略
        if 模式!='physical' and 处置 is None and not 已安装 and not 可忽略未知:#未知必填
            raise 会话格式不支持迁移错误(#拒绝
                f'format v2 contains unknown event type {json.dumps(类型,ensure_ascii=False)} at seq {下标}',#消息
            )#Error结束
        表面=处置 is not None and 类型 in 表面类型#是否表面
        if 模式=='physical' or 处置 is None:#物理或未知
            可选=表面可选#表面可选
        elif 表面:#表面
            可选=表面可选#表面可选
        else:#日志
            可选=日志可选#日志可选
        精确键(记录,事件必填,可选,f'format v2 event {下标}')#精确键
        if 记录['seq']!=下标:#非稠密
            raise 会话格式错误(f'format v2 event {下标} is not dense')#非稠密
        会话格式安全整数(记录['time'],f'format v2 event {下标} time')#时间
        if 'ignorable' in 记录 and 记录['ignorable'] is not True:#ignorable非法
            raise 会话格式错误(f'format v2 event {下标} ignorable must be true when present')#错误
        if 模式=='target' and 表面:#表面元数据
            断言已发布表面元数据(记录,下标,类型,'forbid-assistant')#表面元数据
        if 模式=='target' and 处置 is not None:#载荷
            断言载荷(事件,处置)#载荷
        if 类型=='session/end-seed':#end-seed
            数据=json记录(事件['data'],f'session/end-seed {下标} data')#data
            if 数据.get('inherited') is True:#继承标记
                最后继承标记=下标#记下
    if 产物['header']['isSeeded'] and 最后继承标记!=切割:#种子不一致
        raise 会话格式错误('format v2 seeded header disagrees with its last inherited end-seed marker')#错误
    if not 产物['header']['isSeeded'] and 最后继承标记 is not None:#非种子却有标记
        raise 会话格式错误('format v2 unseeded Session contains an inherited end-seed marker')#错误
    if 模式=='target':#目标模式
        断言已发布产物关系(产物,已发布v2关系扩展)#关系

def 断言载荷(事件,处置):#断言载荷
    """按处置表校验事件载荷与嵌入助手流。"""
    数据=json记录(事件['data'],f"{事件['type']} {事件['seq']} data")#data
    精确键(数据,处置['required'],处置['optional'],f"{事件['type']} {事件['seq']} data")#精确键
    for 键 in 处置['opaque']:#不透明键
        if 键 in 数据:#有键
            快照会话格式json(数据[键],f"{事件['type']} {事件['seq']} opaque {键}")#快照
    if 事件['type']=='assistant/attempt' or 事件['type']=='assistant/message':#助手流事件
        回合=会话格式计数(数据['turn'],f"{事件['type']} {事件['seq']} turn")#回合
        步骤=会话格式计数(数据['step'],f"{事件['type']} {事件['seq']} step")#步骤
        装配器=块组装器()#装配器
        try:#尝试展开
            定时=展开助手流(数据['stream'])#展开流
            for 成员 in 定时:#遍历成员
                断言已发布载荷语义({#断言语义
                    'type':'assistant/chunk',#类型
                    'seq':事件['seq'],#序号
                    'time':成员['time'],#时间
                    'data':{'turn':回合,'step':步骤,'chunk':成员['chunk']},#数据
                },2)#版本2
                装配器.推入(成员['chunk'])#推入块
        except BaseException as 错误:#捕获
            raise 会话格式错误(f"{事件['type']} {事件['seq']} has an invalid embedded stream",错误)#错误
        if 事件['type']=='assistant/attempt':#attempt到此
            return#返回
        断言已发布载荷语义(事件,2)#消息语义
        if len(定时)>0:#有流
            消息=json记录(数据['message'],f"assistant/message {事件['seq']} message")#消息
            内容=装配器.中断块列表() if 数据.get('interrupted') is True else 装配器.块列表()#内容
            if not 深相等json(消息['content'],内容):#内容不一致
                raise 会话格式错误(f"assistant/message {事件['seq']} message content disagrees with its embedded stream")#错误
            if not 深相等json(数据['usage'],装配器.用量):#用量不一致
                raise 会话格式错误(f"assistant/message {事件['seq']} usage disagrees with its embedded stream")#错误
            出处=json记录(消息['source'],f"assistant/message {事件['seq']} source")#出处
            if not 深相等json(出处['replayState'],装配器.回放状态):#回放不一致
                raise 会话格式错误(f"assistant/message {事件['seq']} replay state disagrees with its embedded stream")#错误
        return#返回
    if 事件['type']=='session/end-seed':#end-seed
        if 'inherited' in 数据 and 数据['inherited'] is not True:#inherited非法
            raise 会话格式错误(f"session/end-seed {事件['seq']} inherited must be true when present")#错误
        return#返回
    断言已发布载荷语义(事件,2)#其余语义

def json记录(值,标签):#JSON记录
    """要求值为非 null 非数组对象。"""
    if not isinstance(值,dict):#非对象
        raise 会话格式错误(f'{标签} must be an object')#错误
    return 值#断言

def 精确键(值,必填,可选,标签):#精确键
    """要求恰好含必填键，且无意外键。"""
    允许=set(必填)|set(可选)#允许集
    for 键 in 必填:#缺键
        if 键 not in 值:#缺键
            raise 会话格式错误(f'{标签} lacks required field {键}')#缺键错误
    for 键 in 值.keys():#意外键
        if 键 not in 允许:#意外
            raise 会话格式错误(f'{标签} has unexpected field {键}')#意外错误

def 恢复已发布v2产物(产物,已知事件类型):#恢复v2产物
    """恢复并校验一个已解码的已发布 v2 产物。"""
    校验已发布v2产物(产物,'current',已知事件类型)#当代模式
    return 产物#返回
