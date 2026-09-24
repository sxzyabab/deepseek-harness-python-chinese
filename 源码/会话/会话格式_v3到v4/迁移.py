"""把历史子事实追加到已转换为 V4 的 V3 源事件之后。"""
import json#未知类型诊断
from ..会话格式 import (#从会话格式导入
    定义会话格式迁移,#定义迁移
    会话格式错误,#格式错误
    会话格式不支持迁移错误,#不支持迁移
    是否会话格式json对象,#是否JSON对象
    会话格式计数,#格式计数
)#从会话格式导入
from ..会话格式_v2到v3 import 断言已发布v3头#从v2到v3导入
from .源列表 import 映射事件消息,改写v3消息来源#来源转换
from .工具角色 import 提升工具结果#提升工具结果
from .内容 import 迁移v3事件内容#内容迁移
from .扩展项身份 import 命名空间化v3不透明事件,已发布v3事件类型#不透明与词表
from .校验 import 断言已发布v4头,校验投递已接受#校验
from .事实列表 import 名录事实,子名录源,子名录事实,子名录主语#名录
from .引用 import 重映射v3引用#引用重映射

def 迁移头(头):#迁移头
    """把已发布 v3 头提升为 v4。"""
    断言已发布v3头(头)#断言v3头
    return {**头,'version':4}#升版本

def 创建阶段(输入):#默认创建阶段
    """无显式子证据时拒绝创建体阶段。"""
    raise 会话格式不支持迁移错误('V3 catalog migration requires explicit historical child facts, including an empty array for a parent without children')#拒绝

#头迁移声明；体恢复需要显式子证据。
会话格式v3到v4=定义会话格式迁移({#v3到v4迁移
    'name':'@deepseek-ai/dsh-session-format-v3-to-v4',#迁移名
    'fromVersion':3,#源版本
    'toVersion':4,#目标版本
    'migrateHeader':迁移头,#迁移头
    'createStage':创建阶段,#默认拒绝体阶段
    'validateTargetHeader':断言已发布v4头,#校验目标头
})#会话格式v3到v4结束

def 创建会话格式v3到v4(子项列表):#绑定子证据的迁移
    """把一个父的历史子证据绑定到其 V3→V4 迁移。"""
    def 创建已绑定阶段(输入):#创建阶段闭包
        return 已发布v3到v4阶段(输入,子项列表)#独立阶段
    return 定义会话格式迁移({**会话格式v3到v4,'createStage':创建已绑定阶段})#替换createStage

class 已发布v3到v4阶段:#已发布v3到v4阶段
    """有状态体阶段：转换事件、插入中断回合结束，并补全历史子名录。"""
    def __init__(自身,输入,子项列表):#构造
        """记下输入、排序后的子候选，并初始化切口状态。"""
        自身.输入=输入#输入
        自身.headerInheritedEventCount=None#头继承事件数
        自身.候选=sorted([子名录源(子) for 子 in 子项列表],key=候选排序键)#按创建时间与标识排序
        自身.名录=[]#已见名录载荷
        自身.切口=None if 输入['sourceHeader']['isSeeded'] else 0#目标切口
        自身.源切口=自身.切口#源切口
        自身.映射=[]#源到目标序号映射
        自身.回合=None#当前回合
        自身.步骤开放=False#是否开放步骤
        自身.下一回合已剪接=False#下一回合剪接
        自身.下一序号=0#目标序号
        自身.时间=输入['sourceHeader']['createdAt']#当前时间
        自身.外部投递序号=None#外部投递序号
        if not 输入['sourceHeader']['isSeeded']:#非种子
            自身.headerInheritedEventCount=0#公开0

    def transformEvent(自身,事件,上下文):#转换事件
        """转换一条源事件并同步发出已落定目标项。"""
        if 事件['seq']!=len(自身.映射):#须稠密
            raise 会话格式错误('V3 source events must be dense')#错误
        中断=自身.观察重启(事件)#观察重启
        if 中断 is not None:#插入中断回合结束
            上下文.emitEvent({'type':'turn/end','seq':自身.下一序号,'time':事件['time'],
                'data':{'turn':中断,'reason':{'kind':'interrupted'}}})#发出
            自身.下一序号+=1#推进
        目标序号=自身.下一序号#占用
        自身.下一序号+=1#推进
        自身.时间=事件['time']#更新时间
        if 事件['type']=='session/end-seed' and 是否会话格式json对象(事件.get('data')) and 事件['data'].get('inherited') is True:#继承结束种子
            if not 自身.输入['sourceHeader']['isSeeded']:#非种子却有标记
                raise 会话格式错误('unseeded format v3 Session contains an inherited end-seed marker')#错误
            自身.源切口=事件['seq']#源切口
            自身.切口=目标序号#目标切口（插入后占用前）
            自身.名录.clear()#切口后重计名录
        elif 事件['type']=='subagent/catalog':#名录
            自身.名录.append(事件['data'])#记下
        投递标识=校验投递已接受(事件,3)#v3代投递
        if 事件['type']=='session-log-deepseek/delivery-accepted':#投递标记
            if 是否会话格式json对象(事件.get('data')) and 事件['data'].get('sessionFormatVersion')==4:#拒绝对目标代声称
                raise 会话格式不支持迁移错误('format v3 delivery marker claims target format v4')#拒绝
            if 投递标识 is not None and 投递标识!=自身.输入['sourceHeader']['id']:#外部投递
                自身.外部投递序号=事件['seq']#记下
        不透明=命名空间化v3不透明事件(事件)#不透明化
        if 不透明 is not 事件:#未知可忽略
            自身.映射.append(目标序号)#登记映射
            上下文.emitEvent(不透明 if 不透明['seq']==目标序号 else {**不透明,'seq':目标序号})#只动seq
            return#返回
        if 事件['type'] not in 已发布v3事件类型:#未知必需
            raise 会话格式不支持迁移错误(#拒绝
                'format v3 contains unknown event type '+json.dumps(事件['type'],ensure_ascii=False,separators=(',',':'),allow_nan=False)+' at seq '+str(事件['seq']),#消息
            )#Error结束
        已重映射=重映射v3引用(事件,目标序号,自身.映射)#重映射引用
        自身.映射.append(目标序号)#登记映射
        def 变换消息(消息):#改写来源
            来源=消息.get('source')#来源
            if not 是否会话格式json对象(来源):#无来源对象
                return 消息#原样
            已转=改写v3消息来源(来源,事件['seq'],消息.get('role'))#改写
            return 消息 if 已转 is 来源 else {**消息,'source':已转}#写回
        已改写=映射事件消息(已重映射,变换消息)#改写消息来源
        上下文.emitEvent(迁移v3事件内容(提升工具结果(已改写)))#提升并迁移内容

    def transformRun(自身,游程,上下文):#转换游程
        """展开游程并逐事件转换。"""
        for 事件 in 游程.expand():#展开
            自身.transformEvent(事件,上下文)#转换

    def 观察重启(自身,事件):#观察重启
        """在剪接下一回合后无开放步骤时插入中断回合结束。"""
        数据=事件.get('data')#载荷
        中断=事件['type']=='turn/start' and 自身.回合 is not None and (not 自身.步骤开放) and 自身.下一回合已剪接 and 是否会话格式json对象(数据) and 数据.get('turn')==自身.回合+1
        中断回合=自身.回合 if 中断 else None#被中断回合
        自身.下一回合已剪接=事件['type']=='agent/inbox/spliced' and 是否会话格式json对象(数据) and 数据.get('target')=='next-turn' and isinstance(数据.get('inserted'),list) and len(数据['inserted'])>0
        if 事件['type']=='turn/start' and 是否会话格式json对象(数据) and isinstance(数据.get('turn'),(int,float)) and not isinstance(数据.get('turn'),bool):#打开回合
            自身.回合=数据['turn']#记下
        elif 事件['type']=='turn/end':#回合结束不清除步骤开放
            自身.回合=None#关闭回合
        elif 事件['type']=='step/start':#步骤开始
            自身.步骤开放=True#开放
        elif 事件['type']=='step/end':#步骤结束
            自身.步骤开放=False#关闭
        return 中断回合#返回

    def finish(自身,上下文):#完成
        """按子证据补全名录并返回目标继承事件数。"""
        切割=会话格式计数(自身.切口,'V3 inherited event count')#目标切口
        源切割=会话格式计数(自身.源切口,'V3 source inherited event count')#源切口
        已有名录={}#按子标识
        for 数据 in 自身.名录:#已有名录
            事实=名录事实(数据)#校验
            标识=事实['childId']#子标识
            if 标识 in 已有名录:#重复
                raise 会话格式不支持迁移错误('duplicate catalog child '+标识)#拒绝
            已有名录[标识]=事实#记下
        if 自身.输入['sourceInheritedEventCount'] is not None and 源切割!=自身.输入['sourceInheritedEventCount']:#与输入切口不符
            raise 会话格式错误('format v3 inherited cut disagrees with its source marker')#错误
        if 自身.外部投递序号 is not None and ('parentSession' not in 自身.输入['sourceHeader'] or 自身.外部投递序号>=源切割):#非法外部投递
            raise 会话格式错误('current-generation delivery marker names the wrong Session')#错误
        for 源 in 自身.候选:#补全候选
            标识=源['childId']#子标识
            已有=已有名录.get(标识)#已有
            事实=子名录事实(源)#发现事实
            if 已有 is not None:#已在父名录
                if 已有.get('childCreatedAt')!=源.get('childCreatedAt'):#创建时间冲突
                    raise 会话格式不支持迁移错误(子名录主语(源)+' conflicts with its parent catalog')#拒绝
                if 事实 is not None and any(已有.get(键)!=事实.get(键) for 键 in ('mode','label')):#模式或标签冲突
                    raise 会话格式不支持迁移错误(子名录主语(源)+' conflicts with its parent catalog')#拒绝
                continue#已有则跳过
            条目=事实 if 事实 is not None else {'version':1,'childId':标识,'childCreatedAt':源['childCreatedAt'],'mode':'unknown'}#缺省条目
            已有名录[标识]=条目#登记
            上下文.emitEvent({'type':'subagent/catalog','seq':自身.下一序号,'time':自身.时间,'data':条目})#发出
            自身.下一序号+=1#推进
        return 切割#返回切口

def 候选排序键(源):#候选排序键
    """按子创建时间，其次按子标识。"""
    return (源['childCreatedAt'],源['childId'])#稳定排序
