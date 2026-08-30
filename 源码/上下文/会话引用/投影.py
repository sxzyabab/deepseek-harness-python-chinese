"""当前表面投影与按字节封顶的渲染。"""
import math#ceil与floor
from ...压缩.压缩 import 是否压缩检查点来源#导入压缩检查点来源判定
from ...模型后端.llm import 断言永不#导入穷尽检查
from ...工具.输出保留 import 文本保留器#导入头尾文本保留器
from .序列化 import 序列化标签安全JSON#导入标签安全JSON序列化

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 字节长(文本):#UTF-8字节长度
    """对齐 Buffer.byteLength(text, 'utf8')。"""
    return len(文本.encode('utf-8'))#按utf8计字节

def 投影会话对话(快照):#从表面快照投影对话
    """投影当前用户/助手对话，排除工具、推理与注入上下文。"""
    对话=[]#收集投影项
    for 事件 in 取字段(快照,'events'):#遍历表面事件
        种类=取字段(事件,'type')#事件类型
        if 种类=='user/message':#用户消息
            数据=取字段(事件,'data')#事件数据
            检查点=是否压缩检查点来源(取字段(数据,'source'))#是否压缩检查点
            if (not 检查点) and 取字段(取字段(数据,'source'),'kind')!='user':#非检查点且非用户来源则跳过
                continue#跳过
            文本=抽出文本(取字段(数据,'content'))#抽出文本块
            if 文本!='':#非空才入列
                对话.append({'role':'user','text':文本,'checkpoint':检查点,'originalText':文本,'omittedBytes':0})#入列
        elif 种类=='assistant/message':#助手消息
            文本=抽出文本(取字段(取字段(取字段(事件,'data'),'message'),'content'))#抽出助手文本
            if 文本!='':#非空才入列
                对话.append({'role':'assistant','text':文本,'checkpoint':False,'originalText':文本,'omittedBytes':0})#入列
        elif 种类=='tool/result':#工具结果
            pass#引用快照不纳入工具输出
        else:#不可达分支
            断言永不(事件,'session-reference surface event')#编译期穷尽检查
    return 对话#返回投影对话

def 保留引用会话(快照,标签,最大字节):#按字节预算保留引用会话
    """把一份投影快照装进精确的已渲染 JSON 对象字节上限。装得下则返回数据与统计；固定数据仍装不下时为 None。"""
    原始=投影会话对话(快照)#先投影完整对话
    保留=[dict(项) for 项 in 原始]#可就地删改的副本
    省略消息=0#整条丢掉的消息数
    丢掉省略字节=0#丢掉整条时计入的原文字节
    def 数据():#按当前保留集组装序列化对象
        """组装面向模型的引用会话数据。"""
        会话=取字段(快照,'session')#源会话头
        return {#序列化对象
            'sessionId':取字段(会话,'id'),#源会话id
            'label':标签,#展示标签
            'cwd':取字段(会话,'cwd',None),#缺cwd则为null
            'capturedThroughSeq':取字段(快照,'capturedThroughSeq'),#捕获序号
            'conversation':[{'role':取字段(项,'role'),'text':取字段(项,'text')} for 项 in 保留],#只输出角色与文本
        }#对象结束
    def 尺寸():#当前JSON的UTF-8字节
        """当前序列化对象的 UTF-8 字节。"""
        return 字节长(序列化标签安全JSON(数据()))#计字节
    while 尺寸()>最大字节:#先丢掉非检查点、非最新的整条消息
        最新下标=len(保留)-1#最新一条下标
        丢弃下标=-1#可丢下标
        for 下标,项 in enumerate(保留):#找可丢的旧非检查点
            if (not 取字段(项,'checkpoint')) and 下标!=最新下标:#可丢
                丢弃下标=下标#记下
                break#找到即停
        if 丢弃下标<0:#没有可丢的整条则改截断
            break#改截断
        移除=保留.pop(丢弃下标)#删掉该条
        if 移除 is None:#理论上pop总会给出元素
            raise Exception('session-reference retention selected a missing message')#防御：选中了不存在的消息
        省略消息+=1#整条省略计数
        丢掉省略字节+=字节长(取字段(移除,'originalText'))#按原文计省略字节
    while 尺寸()>最大字节:#再截断当前最长文本
        最长下标=-1#当前最长项下标
        最长字节=0#当前最长项字节
        for 下标,项 in enumerate(保留):#扫描保留集
            当前字节=字节长(取字段(项,'text'))#该项当前文本字节
            if 当前字节>最长字节:#发现更长项
                最长字节=当前字节#记下长度
                最长下标=下标#记下位置
        if 最长下标<0 or 最长字节==0:#没有可再截的文本则失败
            return None#失败
        溢出=尺寸()-最大字节#超出预算的字节
        目标=max(0,最长字节-溢出)#该条目标输出字节
        项=保留[最长下标]#取出最长项
        if 项 is None:#理论上下标有效
            raise Exception('session-reference retention selected a missing longest message')#防御：最长项缺失
        缩短=附通知截断(取字段(项,'originalText'),目标)#按目标截断并附省略通知
        if 缩短['text']==取字段(保留[最长下标],'text'):#截断没有变短则无法继续
            return None#失败
        下一=dict(项)#写回截断结果
        下一['text']=缩短['text']#截断文本
        下一['omittedBytes']=缩短['omittedBytes']#省略字节
        保留[最长下标]=下一#写回
    含压缩=any(取字段(项,'checkpoint') for 项 in 原始)#原投影是否含检查点
    截断省略字节=sum(取字段(项,'omittedBytes') for 项 in 保留)#截断省略字节
    省略字节=截断省略字节+丢掉省略字节#截断加整条丢掉
    return {#组装成功结果
        'data':数据(),#最终序列化对象
        'stats':{#保留统计
            'compacted':含压缩,#是否压缩过
            'originalMessages':len(原始),#投影前条数
            'retainedMessages':len(保留),#保留条数
            'omittedMessages':省略消息,#整条省略数
            'omittedBytes':省略字节,#省略字节
            'truncated':省略消息>0 or 省略字节>0,#有省略或截断则为真
        },#stats结束
    }#返回对象结束

def 抽出文本(内容):#抽出文本块并换行拼接
    """抽出文本块并换行拼接；非文本块丢掉。"""
    if 内容 is None:#无内容
        return ''#空
    段们=[]#文本段
    for 块 in 内容:#逐块
        if 取字段(块,'type')=='text' and isinstance(取字段(块,'text'),str):#文本块
            段们.append(取字段(块,'text'))#收下
    return '\n'.join(段们)#换行拼接

def 附通知截断(文本,最大输出字节):#头尾截断并附省略通知
    """头尾截断并附省略通知。"""
    if 字节长(文本)<=最大输出字节:#已能装下则原样返回
        return {'text':文本,'omittedBytes':0}#原样
    下界=0#二分下界：保留字节
    上界=最大输出字节#二分上界
    最佳={'text':'','omittedBytes':字节长(文本)}#目前最佳候选，初始为全省略
    while 下界<=上界:#二分寻找最大可装下的头尾保留
        保留字节=math.floor((下界+上界)/2)#本轮尝试的保留字节
        头字节=math.ceil(保留字节/2)#头半
        尾字节=math.floor(保留字节/2)#尾半
        保留器=文本保留器({'kind':'headTail','headBytes':头字节,'tailBytes':尾字节})#头尾保留器
        保留器.推入(文本)#推入完整原文
        结果=保留器.收尾()#结束并取出保留文本
        省略量=取字段(结果,'omittedBytes')#省略元数据
        if 取字段(省略量,'kind')!='exact':#省略量必须精确
            raise Exception('session-reference retention did not report exact omitted bytes')#防御：非精确省略
        省略=取字段(省略量,'count')#精确省略字节
        候选=取字段(结果,'text')+'\n[… omitted '+str(省略)+' UTF-8 bytes …]'#附上省略通知
        if 字节长(候选)<=最大输出字节:#通知后仍装得下
            最佳={'text':候选,'omittedBytes':省略}#记下更长的可行候选
            下界=保留字节+1#尝试保留更多
        else:#装不下
            上界=保留字节-1#减少保留
    return 最佳#返回最佳截断

引用会话数据字段=('sessionId','label','cwd','capturedThroughSeq','conversation')#面向模型的引用会话数据字段
引用保留统计字段=('compacted','originalMessages','retainedMessages','omittedMessages','omittedBytes','truncated')#引用保留统计字段
