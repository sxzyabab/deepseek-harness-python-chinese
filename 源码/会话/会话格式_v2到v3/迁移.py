"""流式提升系统提示词，随后做规范 V3 信封转换。"""
import hashlib,json#哈希与身份材料
from ..会话格式 import (#从会话格式导入
    会话格式错误,#格式错误
    会话格式不支持迁移错误,#不支持迁移
    定义会话格式迁移,#定义迁移
    会话格式计数,#格式计数
)#从会话格式导入
from ..会话格式_v1到v2 import 断言已发布v2头#从v1到v2导入
from .载荷 import 断言事件,规范化已转换事件,记录,表面类型#从载荷导入
from .引用 import 重映射事件#从引用导入
from .校验 import 断言已发布v3头#从校验导入

def 迁移头(头):#迁移头
    """把已发布 v2 头提升为 v3，并重命名 code 预设。"""
    断言已发布v2头(头)#断言v2头
    结果={**头,'version':3}#升版本
    if 头.get('agentPreset')=='code':#重命名预设
        结果['agentPreset']='ptc'#改为ptc
    return 结果#返回

def 创建阶段(输入):#创建阶段
    """创建已发布 v2 到 v3 迁移阶段。"""
    return 已发布v2到v3阶段(输入)#创建

#提升系统提示词、重映射经审计的引用，并规范化信封与 PTC 词汇。
会话格式v2到v3=定义会话格式迁移({#v2到v3迁移
    'name':'@deepseek-ai/dsh-session-format-v2-to-v3',#迁移名
    'fromVersion':2,#源版本
    'toVersion':3,#目标版本
    'migrateHeader':迁移头,#迁移头
    'createStage':创建阶段,#创建阶段
    'validateTargetHeader':断言已发布v3头,#校验目标头
})#会话格式v2到v3结束

class 已发布v2到v3阶段:#已发布v2到v3阶段
    """有状态体阶段：插入系统头、重映射引用、规范化信封。"""
    def __init__(自身,输入):#构造
        """记下输入并初始化稠密序号与切口状态。"""
        自身.输入=输入#输入
        自身.headerInheritedEventCount=None#头继承事件数
        自身.映射=[]#源到目标序号映射
        自身.源标识=set()#源消息标识
        自身.生成标识=set()#生成消息标识
        自身.目标序号=0#目标序号
        自身.源切口=None#源切口
        自身.目标切口=None#目标切口
        自身.末次外部投递序号=None#末次外部投递序号
        自身.步骤=None#开放步骤
        自身.头节点=None#受保护系统头节点
        自身.提示词=''#当前系统提示词
        源头=输入['sourceHeader']#源头
        断言已发布v2头(源头)#断言源头
        if not 源头['isSeeded']:#非种子
            自身.源切口=0#非种子切口为0
            自身.目标切口=0#非种子目标切口为0
            自身.headerInheritedEventCount=0#非种子公开0

    def transformEvent(自身,事件,上下文):#转换事件
        """转换一条源事件并同步发出已落定目标项。"""
        if 事件['seq']!=len(自身.映射):#须稠密
            raise 会话格式错误('format v2 source events must be dense')#错误
        断言事件(事件,2)#断言源事件
        自身.观察消息标识(事件)#观察消息标识
        源=事件#待发出源
        数据=记录(事件['data'],事件['type'])#载荷对象
        if 事件['type']=='request/header':#请求头
            头记录=记录(数据['header'],'request header')#请求头
            系统=头记录.get('system')#拆出system
            头其余={键:值 for 键,值 in 头记录.items() if 键!='system'}#去掉system
            提示词=系统 if isinstance(系统,str) else ''#提示词
            if 提示词!=自身.提示词:#变化则插入系统消息
                自身.发出系统(提示词,事件,上下文)#插入
            源={**事件,'data':{**数据,'header':头其余}}#去掉system后的源
        if 事件['type'] in 表面类型 and 自身.头节点 is None:#首步前的surface
            raise 会话格式不支持迁移错误('format v2 surface before first step cannot acquire a system head without changing chronology')#拒绝
        if 事件['type']=='session/end-seed' and 数据.get('inherited') is True:#继承结束种子
            if not 自身.输入['sourceHeader']['isSeeded']:#非种子却有标记
                raise 会话格式错误('format v2 unseeded Session contains an inherited end-seed marker')#错误
            自身.源切口=事件['seq']#源切口
            自身.目标切口=自身.目标序号#目标切口（插入前）
        if 事件['type']=='session-log-deepseek/delivery-accepted':#投递标记
            if 数据.get('sessionFormatVersion')==3:#拒绝对目标代声称
                raise 会话格式错误('format v2 delivery marker claims target format v3')#错误
            if (数据.get('sessionFormatVersion')==2
                and 数据.get('sessionId')!=自身.输入['sourceHeader']['id']):#记外部投递
                自身.末次外部投递序号=事件['seq']#记下
        目标=重映射事件(源,自身.目标序号,自身.映射)#重映射引用
        自身.映射.append(自身.目标序号)#登记映射
        自身.目标序号+=1#推进
        上下文.emitEvent(规范化已转换事件(重命名ptc事件(目标)))#规范化并发出
        if 事件['type']=='step/start':#步骤开始
            自身.步骤={'turn':数据['turn'],'step':数据['step']}#开放步骤
            if 自身.头节点 is None:#首次追加空头节点
                自身.发出系统('',事件,上下文)#追加
        elif 事件['type']=='step/end' or 事件['type']=='turn/end':#步骤或回合结束
            自身.步骤=None#关闭步骤

    def transformRun(自身,游程,上下文):#转换游程
        """展开游程并逐事件转换。"""
        for 事件 in 游程.expand():#展开逐事件转换
            自身.transformEvent(事件,上下文)#转换

    def finish(自身,_上下文):#完成
        """校验切口与投递标记，返回目标继承事件数。"""
        切割=会话格式计数(自身.源切口,'format v2 inherited end-seed marker')#源切口
        源继承=自身.输入['sourceInheritedEventCount']#输入切口
        if 源继承 is not None and 源继承!=切割:#与输入切口不符
            raise 会话格式错误('format v2 inherited end-seed marker disagrees with its source cut')#错误
        源头=自身.输入['sourceHeader']#源头
        if (自身.末次外部投递序号 is not None
            and ('parentSession' not in 源头 or 自身.末次外部投递序号>=切割)):#非法外部投递
            raise 会话格式错误('current-generation delivery marker names the wrong Session')#错误
        return 会话格式计数(自身.目标切口,'format v3 inherited event count')#返回目标切口

    def 观察消息标识(自身,事件):#观察消息标识
        """登记源消息标识并拒绝与生成标识冲突。"""
        数据=记录(事件['data'],事件['type'])#载荷
        if 事件['type']=='user/message':#用户消息
            消息列表=[数据]#单条
        elif 事件['type']=='assistant/message' or 事件['type']=='tool/result':#嵌套消息
            消息列表=[记录(数据['message'],'message')]#嵌套
        elif 事件['type']=='agent/inbox/spliced':#收件箱
            消息列表=数据['inserted']#插入
        elif 事件['type']=='session/title-llm-request':#标题请求
            消息列表=数据['messages']#消息
        else:#无消息
            消息列表=[]#空
        #assertEvent 已在观察标识前校验每个自有消息。
        for 消息 in 消息列表:#遍历消息
            标识=消息['id']#标识
            if 标识 in 自身.生成标识:#与生成标识冲突
                raise 会话格式不支持迁移错误('source message id collides with a generated system message id')#拒绝
            自身.源标识.add(标识)#记入源标识

    def 发出系统(自身,提示词,锚点,上下文):#发出系统消息
        """在开放步骤内插入或替换系统头节点。"""
        if 自身.步骤 is None:#无开放步骤
            raise 会话格式不支持迁移错误('format v2 changed request prompt outside an open step cannot retain source chronology')#拒绝
        身份材料=json.dumps(#合成身份材料
            ['session-format-v2-to-v3',自身.输入['sourceHeader']['id'],锚点['seq'],锚点['type']],#材料
            separators=(',',':'),#紧凑
            ensure_ascii=False,#与 Node 一致
        )#dumps结束
        标识='v2-to-v3-system-'+hashlib.sha256(身份材料.encode('utf-8')).hexdigest()#合成标识
        if 标识 in 自身.源标识 or 标识 in 自身.生成标识:#标识冲突
            raise 会话格式不支持迁移错误('generated system message id collides with an existing message id')#拒绝
        自身.生成标识.add(标识)#记入生成标识
        序号=自身.目标序号#占用目标序号
        自身.目标序号+=1#推进
        事件={#规范化前事件
            'type':'system/message','seq':序号,'time':锚点['time'],#信封
            'data':{#载荷
                **自身.步骤,#回合与步骤
                'message':{#消息
                    'id':标识,#标识
                    'role':'system','source':{'kind':'plugin','plugin':'@deepseek-ai/dsh-system-prompt'},#系统插件来源
                    'content':[] if 提示词=='' else [{'type':'text','text':提示词}],#空或单文本块
                },#message结束
            },#data结束
        }#事件基
        if 自身.头节点 is None:#首次追加
            事件['surfaceOp']='append'#追加
        else:#替换当前头
            事件['surfaceOp']={'op':'replace','start':自身.头节点,'end':自身.头节点}#替换
            事件['sourceEventSeqs']=[自身.头节点]#溯源
        上下文.emitEvent(规范化已转换事件(事件))#规范化并发出
        自身.头节点=序号#更新头节点
        自身.提示词=提示词#更新提示词

def 重命名ptc事件(事件):#重命名PTC事件
    """源准入先于重命名，因此这些载荷具有精确的经审计字段。"""
    类型=事件['type']#类型
    if 类型=='agent-preset/selected':#预设选择
        数据=事件['data']#载荷
        if isinstance(数据,dict) and 数据.get('agentPreset')=='code':#code→ptc
            return {**事件,'data':{**数据,'agentPreset':'ptc'}}#改名
        return 事件#原样
    if 类型=='tool/code-dispatch-start':#代码分发开始
        return {**事件,'type':'tool/ptc-dispatch-start'}#改为ptc标签
    if 类型=='tool/code-dispatch':#代码分发
        return {**事件,'type':'tool/ptc-dispatch'}#改为ptc标签
    if 类型=='user/message':#用户消息
        数据=重命名消息来源(事件['data'])#重命名来源
        return 事件 if 数据 is 事件['data'] else {**事件,'data':数据}#无变化则原样
    if 类型=='agent/inbox/spliced' or 类型=='session/title-llm-request':#收件箱/标题
        数据=事件['data']#载荷
        键='inserted' if 类型=='agent/inbox/spliced' else 'messages'#消息字段
        消息列表=数据[键]#消息列表
        已改=[重命名消息来源(消息) for 消息 in 消息列表]#逐条重命名
        if all(已改[下标] is 消息列表[下标] for 下标 in range(len(消息列表))):#无变化
            return 事件#原样
        return {**事件,'data':{**数据,键:已改}}#有变化则写回
    #内容、工具参数、消息标识及其他载荷不是插件归属槽位。
    return 事件#原样

def 重命名消息来源(消息):#重命名消息插件来源
    """把 tools-code-mode 插件来源改为 tools-ptc。"""
    来源=消息['source']#来源
    if 来源.get('kind')!='plugin' or 来源.get('plugin')!='tools-code-mode':#非目标插件
        return 消息#原样
    return {**消息,'source':{**来源,'plugin':'tools-ptc'}}#改为tools-ptc

