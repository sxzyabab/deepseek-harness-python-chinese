"""原生 V4 元数据与本代次自有关系校验。"""
import json#未知类型诊断
from os.path import isabs as 是否绝对路径#cwd须为绝对路径
from ..会话格式 import (#从会话格式导入
    会话格式错误,#格式错误
    会话格式不支持迁移错误,#不支持迁移
    是否会话格式json对象,#是否JSON对象
    会话格式计数,#格式计数
)#从会话格式导入
from .开发者 import 断言v4开发者数据#开发者数据
from .关系 import 断言v4生命周期关系#生命周期关系
from .消息源列表 import 断言v4消息来源#消息来源
from .事实列表 import 名录事实#名录事实
from .已退役语法 import 断言v4已退役语法#已退役语法
from .系统消息 import 断言v4系统消息字段#系统消息字段
from .分叉结果 import 断言v4分叉结果#分叉结果
from .工具角色 import 断言v4工具结果消息#工具结果消息

def 断言已发布v4头(头):#断言v4头
    """校验精确的原生 V4 逻辑头。"""
    if not 是否会话格式json对象(头) or 头.get('version')!=4:#须为v4对象
        raise 会话格式错误('expected format v4 header')#错误
    必填=['version','id','createdAt','isSeeded','delegationDepth']#必填键
    允许=set(必填+['cwd','parentSession','origin','agentPreset'])#允许键
    缺=None#缺必填
    for 键 in 必填:#找缺
        if 键 not in 头:#缺
            缺=键#记下
            break#找到
    意外=None#意外键
    for 键 in 头.keys():#找意外
        if 键 not in 允许:#意外
            意外=键#记下
            break#找到
    if 缺 is not None:#缺字段
        raise 会话格式错误('format v4 header lacks required field '+缺)#错误
    if 意外 is not None:#意外字段
        raise 会话格式错误('format v4 header has unexpected field '+意外)#错误
    if not isinstance(头.get('id'),str):#id须串
        raise 会话格式错误('format v4 header id must be a string')#错误
    会话格式计数(头['createdAt'],'format v4 header createdAt')#创建时间
    会话格式计数(头['delegationDepth'],'format v4 header delegationDepth')#委派深度
    if not isinstance(头.get('isSeeded'),bool):#isSeeded须布尔
        raise 会话格式错误('format v4 header isSeeded must be boolean')#错误
    if 'cwd' in 头 and (not isinstance(头['cwd'],str) or not 是否绝对路径(头['cwd'])):#cwd须绝对
        raise 会话格式错误('format v4 header cwd must be absolute')#错误
    for 键 in ('parentSession','agentPreset'):#可选字符串
        if 键 in 头 and not isinstance(头[键],str):#须串
            raise 会话格式错误('format v4 header '+键+' must be a string')#错误
    if 'origin' in 头 and 头['origin']!='subagent':#origin仅subagent
        raise 会话格式错误('format v4 header origin must be "subagent"')#错误

def 恢复已发布v4产物(产物,已知事件类型):#恢复v4产物
    """校验 V4 继承、词表、原生消息准入与生命周期归属。"""
    断言已发布v4头(产物['header'])#断言头
    切割=会话格式计数(产物['inheritedEventCount'],'format v4 inherited event count')#继承切口
    if 切割>len(产物['events']):#切口越界
        raise 会话格式错误('format v4 inherited event count exceeds its events')#错误
    if (not 产物['header']['isSeeded']) and 切割!=0:#非种子却有继承
        raise 会话格式错误('unseeded format v4 Session has inherited events')#错误
    末次继承标记=None#末次继承结束种子
    for 下标,事件 in enumerate(产物['events']):#逐事件
        if 事件['type'] not in 已知事件类型 and 事件.get('ignorable') is not True:#未知必需
            raise 会话格式不支持迁移错误(#拒绝
                'format v4 contains unknown event type '+json.dumps(事件['type'],ensure_ascii=False,separators=(',',':'),allow_nan=False)
                +' at seq '+str(下标),#消息
            )#Error结束
        if 事件['seq']!=下标:#须稠密
            raise 会话格式错误('format v4 event '+str(下标)+' is not dense')#错误
        if 事件['type'] not in 已知事件类型:#未知可忽略跳过载荷
            continue#继续
        断言v4已退役语法(事件)#已退役语法
        断言v4系统消息字段(事件)#系统消息
        断言v4工具结果消息(事件)#工具结果
        断言v4分叉结果(事件)#分叉结果
        if (事件['type']=='session/end-seed' and 是否会话格式json对象(事件['data'])
            and 事件['data'].get('inherited') is True):#继承结束种子
            末次继承标记=下标#记下
    if 产物['header']['isSeeded'] and 末次继承标记!=切割:#种子切口不符
        raise 会话格式错误('format v4 seeded header disagrees with its last inherited end-seed marker')#错误
    if (not 产物['header']['isSeeded']) and 末次继承标记 is not None:#非种子却有标记
        raise 会话格式错误('format v4 unseeded Session contains an inherited end-seed marker')#错误
    断言已发布v4关系(产物,已知事件类型)#关系
    return 产物#返回原产物

def 校验投递已接受(事件,当前版本):#校验投递已接受
    """在评估归属前校验投递代次与活动代次坐标。"""
    if 事件['type']!='session-log-deepseek/delivery-accepted':#非投递
        return None#无
    数据=事件['data']#载荷
    if not 是否会话格式json对象(数据):#须对象
        raise 会话格式错误('delivery-accepted data must be an object')#错误
    版本=会话格式计数(0 if 'sessionFormatVersion' not in 数据 else 数据['sessionFormatVersion'],'delivery sessionFormatVersion')#代次
    if 版本!=当前版本:#非当前代
        return None#无
    直至序号=会话格式计数(数据['throughSeq'],'delivery throughSeq')#水位
    if 直至序号>=事件['seq']:#须更早
        raise 会话格式错误('delivery throughSeq must precede its marker')#错误
    标识=数据.get('sessionId')#会话标识
    if not isinstance(标识,str) or len(标识)==0:#须非空
        raise 会话格式错误('delivery requires a nonempty Session id')#错误
    return 标识#返回

def 断言已发布v4关系(产物,已知事件类型):#断言已发布v4关系
    """校验原生开发者字段、消息来源、生命周期、名录与投递关系。"""
    标识集=set()#名录子标识
    for 事件 in 产物['events']:#逐事件
        if 事件['type'] not in 已知事件类型:#未知不解释
            continue#继续
        断言v4开发者数据(事件)#开发者
        断言v4消息来源(事件)#消息来源
        投递标识=校验投递已接受(事件,4)#当前代投递
        if (投递标识 is not None
            and not ('parentSession' in 产物['header'] and 事件['seq']<产物['inheritedEventCount'])
            and 投递标识!=产物['header']['id']):#当前代投递须指向本会话
            raise 会话格式错误('current-generation delivery marker names the wrong Session')#错误
        if 事件['type']=='subagent/catalog' and 事件['seq']>=产物['inheritedEventCount']:#当代名录
            事实=名录事实(事件['data'])#名录事实
            标识=事实['childId']#子标识
            if 标识 in 标识集:#重复
                raise 会话格式错误('duplicate catalog child '+标识)#错误
            标识集.add(标识)#记入
    断言v4生命周期关系(产物,已知事件类型)#生命周期
