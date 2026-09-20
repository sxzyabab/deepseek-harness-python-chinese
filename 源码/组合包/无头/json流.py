"""`--json` 运行投影：从一只智能体的耐久会话事件导出有界有序事件流。

每条投影事件都是提交点：文本与推理只来自已提交的 `assistant/message`，
从不来自仍可能重试或丢弃的现场尝试，因此流从不携带耐久日志没有的内容。
"""
import json,math,os#序列化、有限数与工作目录
from ...模型后端.llm.助手流 import 末条助手流块#流末条用量
__all__=['最大字符串字节','最大事件字节','约束json行','投影json运行']#仅中文公开名

最大字符串字节=8*1024#每串与每键默认上限
最大事件字节=32*1024#单事件序列化上限，含换行；终局 final 豁免
行终止字节=1#换行占用
最大深度=64#容器深度上限

def 截断utf8(文本,最大字节):
    """按 UTF-8 截到最大字节，丢掉被切开的尾字符。"""
    缓冲=文本.encode('utf-8')[:最大字节]#截字节
    解码=缓冲.decode('utf-8','replace')#替换非法尾
    return 解码[:-1] if 解码.endswith('\ufffd') else 解码#丢掉替换符

def 约束键(键,最大字节,状态):
    """约束一个对象键，超长则打截断旗。"""
    if len(键.encode('utf-8'))<=最大字节:#未超
        return 键#原样
    状态['truncated']=True#打旗
    return 截断utf8(键,最大字节)#截断

def 约束值(值,最大字节,状态,深度=0):
    """递归约束可 JSON 序列化值里的每个字符串，含键。"""
    if isinstance(值,str):#字符串
        if len(值.encode('utf-8'))<=最大字节:#未超
            return 值#原样
        状态['truncated']=True#打旗
        return 截断utf8(值,最大字节)#截断
    if isinstance(值,list):#数组
        if 深度>=最大深度:#过深
            状态['truncated']=True#打旗
            return '[truncated: depth]'#截尾
        return [约束值(项,最大字节,状态,深度+1) for 项 in 值]#逐项
    if isinstance(值,dict):#对象
        if 深度>=最大深度:#过深
            状态['truncated']=True#打旗
            return '[truncated: depth]'#截尾
        约束后={}#无继承原型
        for 键,项 in 值.items():#逐键
            约束后[约束键(键,最大字节,状态)]=约束值(项,最大字节,状态,深度+1)#记下
        return 约束后#对象
    return 值#标量

def 约束json事件(事件,最大串字节=最大字符串字节):
    """约束一条投影载荷的每个字符串与键，有截断则加 truncated。"""
    状态={'truncated':False}#截断态
    约束后=约束值(事件,最大串字节,状态)#约束
    if 状态['truncated']:#有截断
        约束后['truncated']=True#打旗
    return 约束后#载荷

def 编码行(值):
    """按线协议锁死的 JSON 序列化。"""
    return json.dumps(值,ensure_ascii=False,separators=(',',':'),allow_nan=False)#紧凑 JSON

def 约束json行(事件,最大串字节=最大字符串字节,最大事件字节数=最大事件字节):
    """在串上限与整行上限下序列化一条投影载荷，不含尾换行。"""
    限额=最大事件字节数-行终止字节#预留换行
    约束后=约束json事件(事件,最大串字节)#先约束串
    行=编码行(约束后)#整行
    if len(行.encode('utf-8'))<=限额:#未超行
        return 行#原样
    标量={}#只留标量
    for 键,值 in 约束后.items():#逐字段
        if 值 is None or not isinstance(值,(dict,list)):#标量
            标量[键]=值#收下
    标量['truncated']=True#打旗
    短行=编码行(标量)#短行
    if len(短行.encode('utf-8'))<=限额:#短行够
        return 短行#短行
    return 编码行({'type':约束后['type'] if 'type' in 约束后 else None,'truncated':True})#只留类型

def 解析参数(原文):
    """按执行器解析工具调用参数：空输入是 {}，非法或不可往返 JSON 保持原文。"""
    if 原文=='':#空
        return {}#空对象
    见到={'nonFinite':False}#非有限旗
    try:#解析
        解析=json.loads(原文)#先解析
        def 扫(值):
            """扫非有限。"""
            if isinstance(值,float) and not math.isfinite(值):#非有限
                见到['nonFinite']=True#记下
            elif isinstance(值,dict):#对象
                for 项 in 值.values():#逐值
                    扫(项)#递归
            elif isinstance(值,list):#数组
                for 项 in 值:#逐项
                    扫(项)#递归
        扫(解析)#扫描
        return 原文 if 见到['nonFinite'] else 解析#非有限则原文
    except (json.JSONDecodeError,ValueError,TypeError):#非法 JSON
        return 原文#保持原文

def 结果文本(块列表):
    """拼接工具结果面向模型的文本块。"""
    文本=''#累积
    for 块 in 块列表:#逐块
        if 块['type']=='text' and 'text' in 块 and isinstance(块['text'],str):#文本块
            文本=文本+块['text']#拼接
    return 文本#文本

def 流用量(流):
    """一次尝试流里提供者报告的用量。"""
    块=末条助手流块(流,'usage')#末条用量块
    if 块 is None:#没有
        return None#缺席
    return 块['usage'] if 'usage' in 块 else None#用量

def 相加可选(甲,乙):
    """两边都有才求和。"""
    if 甲 is None or 乙 is None:#任缺
        return None#省略
    return 甲+乙#求和

def 累加用量(状态,下一次):
    """跨尝试累加一步用量；任一次缺样本则整步省略。"""
    if 下一次 is None:#本次无样本
        return {'usage':状态['usage'],'complete':False}#不完整
    if 状态['usage'] is None:#尚无累计
        return {'usage':下一次,'complete':状态['complete']}#收下
    总计=状态['usage']#已有
    总量=相加可选(总计['totalTokens'] if 'totalTokens' in 总计 else None,下一次['totalTokens'] if 'totalTokens' in 下一次 else None)#总量
    缓存读=相加可选(总计['cacheReadTokens'] if 'cacheReadTokens' in 总计 else None,下一次['cacheReadTokens'] if 'cacheReadTokens' in 下一次 else None)#缓存读
    缓存写=相加可选(总计['cacheWriteTokens'] if 'cacheWriteTokens' in 总计 else None,下一次['cacheWriteTokens'] if 'cacheWriteTokens' in 下一次 else None)#缓存写
    推理=相加可选(总计['reasoningTokens'] if 'reasoningTokens' in 总计 else None,下一次['reasoningTokens'] if 'reasoningTokens' in 下一次 else None)#推理
    用量={#必有输入输出
        'inputTokens':总计['inputTokens']+下一次['inputTokens'],
        'outputTokens':总计['outputTokens']+下一次['outputTokens'],
    }#基础
    if 总量 is not None:#有总量
        用量['totalTokens']=总量#带上
    if 缓存读 is not None:#有缓存读
        用量['cacheReadTokens']=缓存读#带上
    if 缓存写 is not None:#有缓存写
        用量['cacheWriteTokens']=缓存写#带上
    if 推理 is not None:#有推理
        用量['reasoningTokens']=推理#带上
    return {'usage':用量,'complete':状态['complete']}#更新

def 投影json运行(上下文,智能体,汇,选项=None):
    """把一只智能体的运行投影成汇上的换行分隔 JSON。选项为 dict。"""
    if 选项 is None:#缺省
        选项={}#空
    最大串=选项['maxStringBytes'] if 'maxStringBytes' in 选项 else 最大字符串字节#串上限
    已拆除=False#是否已拆
    步用量={'usage':None,'complete':True}#当前步

    def 写出(事件):
        """写一行约束后的事件。"""
        汇.write(约束json行(事件,最大串)+'\n')#带换行

    def 会话事件(会话,事件):
        """只投影本智能体会话上的已提交事件。"""
        nonlocal 步用量#步态
        if 会话 is not 智能体.session:#不是本会话
            return#忽略
        种类=事件['type']#事件类型
        数据=事件['data'] if 'data' in 事件 else {}#数据
        if 种类=='turn/start':#回合开始
            写出({'type':'status','phase':'turn_start','turn':数据['turn']})#状态
            return
        if 种类=='step/start':#步开始
            写出({'type':'status','phase':'step_start','turn':数据['turn'],'step':数据['step']})#状态
            return
        if 种类=='assistant/attempt':#尝试
            步用量=累加用量(步用量,流用量(数据['stream'] if 'stream' in 数据 else None))#累加
            return
        if 种类=='assistant/message':#已提交消息
            用量=数据['usage'] if 'usage' in 数据 else 流用量(数据['stream'] if 'stream' in 数据 else None)#优先消息用量
            步用量=累加用量(步用量,用量)#累加
            内容=数据['message']['content'] if 'message' in 数据 and 'content' in 数据['message'] else []#块
            for 块 in 内容:#逐块
                if 块['type']=='reasoning':#推理
                    写出({'type':'thinking','text':块['text']})#思考
                elif 块['type']=='text':#文本
                    写出({'type':'text','text':块['text']})#文本
            return
        if 种类=='step/end':#步结束
            用量=步用量['usage']#累计
            完整=步用量['complete']#是否完整
            步用量={'usage':None,'complete':True}#重置
            载荷={'type':'status','phase':'step_end','turn':数据['turn'],'step':数据['step']}#状态
            if 完整 and 用量 is not None:#完整才公布
                载荷['usage']=用量#用量
            写出(载荷)#写出
            return
        if 种类=='turn/end':#回合结束
            写出({'type':'status','phase':'turn_end','turn':数据['turn'],'reason':数据['reason']})#状态
            return
        if 种类=='tool/call':#工具调用
            写出({#调用
                'type':'tool_call',
                'callId':数据['callId'],
                'tool':数据['name'],
                'input':解析参数(数据['arguments']),
            })#写出
            return
        if 种类=='tool/result':#工具结果
            if 事件.get('surfaceOp')!='append':#压缩替换的历史
                return#忽略
            块=数据['message']['content'][0]#首块
            写出({#结果
                'type':'tool_result',
                'callId':块['toolCallId'],
                'status':'error' if 块.get('isError') is True else 'completed',
                'result':结果文本(块['content']),
            })#写出
            return

    写出({'type':'session','sessionId':智能体.id,'cwd':选项['cwd'] if 'cwd' in 选项 else os.getcwd()})#开场
    停止会话=上下文.on('session/event',会话事件)#订阅

    def 收场(文本):
        """写出终局 final；答案不做截断。"""
        nonlocal 已拆除#拆除态
        if 已拆除:#已拆
            return#忽略
        汇.write(编码行({'type':'final','text':文本})+'\n')#无损终局

    def 拆除():
        """停止观察会话。"""
        nonlocal 已拆除#拆除态
        已拆除=True#标记
        停止会话()#退订

    return {'finish':收场,'dispose':拆除}#句柄
