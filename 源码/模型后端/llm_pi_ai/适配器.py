"""harness LLM seam 的通用 pi-ai 后端实现。

对齐上游 `llm-pi-ai/src/adapter.ts`。公开面仅中文名；无英文别名。
中止信号公开面为已中止/原因；中止控制器公开面为信号/中止。对接上游 AbortSignal 时只在读取函数内认英文键。
"""
import threading#工作线程
from .. import llm#语言模型服务
from ...依赖 import pi_ai#外部依赖胶水（pi-ai SDK）
from ..超时 import 空闲看门狗,取超时#空闲看门狗与超时判定
from .上下文 import 转派上下文#上下文转换
from .流 import 转流块#事件翻译

__all__=('派爱适配器','合成信号','配置流选项','解析思考档位','推理信息','请求头','流空闲超时码')#仅中文公开名

线程=threading.Thread#工作线程
事件=threading.Event#中止事件
流空闲超时码='LLM_STREAM_IDLE_TIMEOUT'#空闲超时码

class 中止信号:
    """对应中止信号协议，只通知不自己停工作。"""
    def __init__(自身,事件对象,取原因):
        """绑到共享事件与原因读取。"""
        自身._事件=事件对象#中止事件
        自身._取原因=取原因#读取原因
    @property
    def 已中止(自身):
        """是否已经中止。"""
        return 自身._事件.is_set()#事件已置位
    @property
    def 原因(自身):
        """中止原因。"""
        return 自身._取原因()#当前原因
    def 等待(自身):
        """阻塞直到中止。"""
        自身._事件.wait()#等待事件

class 中止控制器:
    """对应中止控制器。"""
    def __init__(自身):
        """创建一对控制器与信号。"""
        自身._事件=事件()#中止事件
        自身._原因=None#中止原因
        自身.信号=中止信号(自身._事件,自身._读原因)#对外信号
    def _读原因(自身):
        """读取当前中止原因。"""
        return 自身._原因#原因
    def 中止(自身,原因=None):
        """发出中止；重复调用忽略。"""
        if 自身._事件.is_set():#已经中止过则忽略，原因以第一次为准
            return#忽略
        自身._原因=原因#记下原因
        自身._事件.set()#置位

def 源已中止(源):
    """调用方或上游信号是否已中止；本类只暴露已中止，上游 AbortSignal 只在此处认 aborted。"""
    if 源 is None:#没有信号则视为未中止
        return False#无信号
    if getattr(源,'aborted',False):#上游 AbortSignal 键，不导出为别名
        return True#上游已中止
    if getattr(源,'已中止',False):#公开面旗标
        return True#已中止
    return False#未中止

def 源原因(源):
    """取出中止原因；本类只暴露原因，上游 AbortSignal 只在此处认 reason。"""
    if 源 is None:#没有信号则没有原因
        return None#无信号
    原因=getattr(源,'reason',None)#上游 AbortSignal 键，不导出为别名
    if 原因 is not None:#上游先给出原因则用它，与合成时先中止者获胜一致
        return 原因#上游原因
    return getattr(源,'原因',None)#公开面原因

def 源等待(源):
    """阻塞直到源中止。"""
    if hasattr(源,'等待'):#优先走公开面等待，避免轮询
        源.等待()#等待
        return#已等到
    if hasattr(源,'wait'):#上游英文 wait，只在此处对接，不导出为别名
        源.wait()#等待
        return#已等到
    完成=事件()#等到中止
    def 放行(*位置参数):
        """中止回调。"""
        完成.set()#放行
    if hasattr(源,'addEventListener'):#上游 AbortSignal 用 abort 事件名，只听一次
        源.addEventListener('abort',放行,{'once':True})#只听一次
        完成.wait()#等待
        return#已等到
    if hasattr(源,'加入监听'):#中文监听入口仍用上游 abort 事件名
        源.加入监听('abort',放行,{'once':True})#只听一次
        完成.wait()#等待
        return#已等到
    while not 源已中止(源):#没有等待方法则短间隔轮询旗标
        完成.wait(0.05)#短等

def 合成信号(源们):
    """对应AbortSignal.any，先中止的一路获胜。"""
    控制器=中止控制器()#合成控制器
    for 源 in 源们:#先扫一轮：已中止的立刻胜出，不必再开监视线程
        if 源已中止(源):#这一路已经中止，立刻合成并带回原因
            控制器.中止(源原因(源))#立刻合成
            return 控制器.信号#合成信号
    def 转发(源):
        """源中止后转发到合成控制器。"""
        源等待(源)#阻塞到源中止
        控制器.中止(源原因(源))#转发原因
    for 源 in 源们:#尚未中止的各路后台监视，先到者获胜
        线程(target=转发,args=(源,),daemon=True).start()#监视一路
    return 控制器.信号#融合信号

def 配置流选项(配置,推理,密钥):
    """把配置的流旋钮拷进 pi-ai 的共用选项词表。"""
    启用推理=None if 推理=='off' else 推理#off映射为省略
    选项={'maxRetries':0}#适配器内不再试
    if 密钥 is not None:#有密钥才带 apiKey，省略则交给 pi-ai 环境发现
        选项['apiKey']=密钥#有密钥才带上
    if 启用推理 is not None:#off 已映射为省略，有思考档位才带 reasoning
        选项['reasoning']=启用推理#有思考才带上
    if 配置.get('thinkingBudgets') is not None:#有思考预算才带上
        选项['thinkingBudgets']=配置['thinkingBudgets']#有预算才带上
    if 配置.get('cacheRetention') is not None:#有缓存保留才带上
        选项['cacheRetention']=配置['cacheRetention']#有缓存保留才带上
    if 配置.get('transport') is not None:#有传输才带上
        选项['transport']=配置['transport']#有传输才带上
    if 配置.get('timeoutMs') is not None:#有超时才带上
        选项['timeoutMs']=配置['timeoutMs']#有超时才带上
    if 配置.get('websocketConnectTimeoutMs') is not None:#有 WebSocket 连接超时才带上
        选项['websocketConnectTimeoutMs']=配置['websocketConnectTimeoutMs']#有WebSocket连接超时才带上
    return 选项#共用选项

def 取模型字段(模型,键):
    """读取 pi-ai 模型字段，兼容映射与对象。"""
    if isinstance(模型,dict):#映射走下标，对象走属性
        return 模型[键]#字段
    return getattr(模型,键)#属性

def 可描述思考档位(模型,力度):
    """本精确模型实际能接受的配置默认，用于描述它。"""
    if 力度 is None:#没有配置默认则不描述档位
        return None#没有配置
    受支持=pi_ai.getSupportedThinkingLevels(模型)#受支持档位
    for 档位 in 受支持:#配置档位必须是本模型实际能接受的
        if 档位==力度:#模型支持该档位才拿去描述
            return 力度#用该档位
    return None#不支持则不描述

def 解析思考档位(模型,力度):
    """校验显式的 harness/配置力度，不调用 pi-ai 的钳制。"""
    if 力度 is None:#没有显式力度则不校验
        return None#没有力度
    受支持=pi_ai.getSupportedThinkingLevels(模型)#受支持档位
    for 档位 in 受支持:#显式力度必须命中受支持列表，否则大声失败
        if 档位==力度:#支持则原样用，不钳到邻近档位
            return 力度#支持则用
    提供方=取模型字段(模型,'provider')#提供方
    标识=取模型字段(模型,'id')#模型id
    raise llm.大模型错误(
        'pi-ai provider "'+str(提供方)+'" model "'+str(标识)+'" does not support reasoning effort "'+str(力度)+'"',
        'UNSUPPORTED_REASONING_EFFORT',
    )#不支持

def 推理信息(模型,默认档位):
    """一个模型的可选推理力度，或什么都没有。"""
    if isinstance(模型,dict):#映射读 reasoning 键，对象读属性
        推理=模型.get('reasoning',False)#是否推理
    else:#对象
        推理=getattr(模型,'reasoning',False)#是否推理
    if not 推理:#非推理模型不提供力度控件
        return {}#不提供控件
    档位们=pi_ai.getSupportedThinkingLevels(模型)#受支持档位
    力度列表=[]#展示列表
    for 档位 in 档位们:#每个受支持档位做成 id 加展示名
        力度列表.append({
            'id':llm.推理力度标识(档位),#品牌化档位
            'name':档位[0].upper()+档位[1:],#首字母大写展示名
        })#一条力度
    推理块={'efforts':力度列表}#力度列表
    if 默认档位 is not None:#有可描述的默认档位才带 defaultEffort
        推理块['defaultEffort']=llm.推理力度标识(默认档位)#有默认才带上
    return {'reasoning':推理块}#推理元数据

def 请求头(头):
    """合并部署头，同时去掉大小写不敏感的归属碰撞。"""
    归属=llm.归属头()#harness归属
    保留=set()#保留头名
    for 名 in 归属:#归属头名一律小写保留，部署头不得覆盖
        保留.add(名.lower())#小写保留
    合并={}#去掉碰撞的部署头
    for 名,值 in (头 or {}).items():#部署头；与归属小写同名的丢掉
        if 名.lower() not in 保留:#非保留名才收下部署头
            合并[名]=值#非保留部署头
    合并.update(归属)#归属获胜
    return 合并#合并结果

class 派爱适配器(llm.大模型适配器):
    """派爱后端的多提供方适配器。"""
    def __init__(自身,配置):
        """保存插件钩子。"""
        llm.大模型适配器.__init__(自身)#适配器基类
        自身.配置=配置#插件钩子
        自身.快照=None#当前快照
    def 当前(自身):
        """当前配置的快照。"""
        配置表=自身.配置['profiles']()#当前配置
        if 自身.快照 is not None and 自身.快照['profiles'] is 配置表:#同一份配置对象则复用模型集合
            return 自身.快照#复用
        模型集合=pi_ai.createModels()#新集合
        for 配置项 in 配置表.values():#每条已解析路由挂上它的 pi-ai 提供方
            模型集合.setProvider(配置项['piProvider'])#挂上每条路由的提供方
        自身.快照={'profiles':配置表,'models':模型集合}#记下新快照
        return 自身.快照#当前快照
    def 配置于(自身,快照,提供方):
        """一份快照里一条路由的配置，或不拥有该路由的失败。"""
        配置项=快照['profiles'].get(提供方)#查表
        if 配置项 is None:#本适配器不拥有该路由
            raise llm.大模型错误('pi-ai adapter does not own provider "'+提供方+'"','NO_ADAPTER')#未注册
        return 配置项#已解析配置
    def 模型于(自身,快照,提供方,模型):
        """一份快照里一对精确路由/模型的已配置描述符。"""
        自身.配置于(快照,提供方)#先确认拥有路由
        已解析=快照['models'].getModel(提供方,模型)#从集合取模型
        if 已解析 is None:#路由有了但集合里没有这个模型
            raise llm.大模型错误('pi-ai provider "'+提供方+'" has no configured model "'+模型+'"','UNKNOWN_MODEL')#未知模型
        return 已解析#已配置模型
    def 提供方信息(自身,提供方):
        """提供方展示。"""
        配置项=自身.当前()['profiles'].get(提供方)#当前配置
        if 配置项 is None:#没有该路由则展示名落到路由键
            名字=提供方#路由键
        else:#有配置则用展示名，缺席仍落到路由键
            名字=配置项.get('displayName',提供方)#展示名或路由键
        return {'id':提供方,'name':名字}#展示
    def 提供方重试政策(自身,提供方):
        """提供方政策。"""
        配置项=自身.当前()['profiles'].get(提供方)#当前快照的配置
        if 配置项 is None:#不拥有该路由则没有政策
            return None#没有该路由
        return 配置项.get('retryPolicy')#政策
    def 列出模型(自身,提供方):
        """建议目录。"""
        快照=自身.当前()#当前快照
        自身.配置于(快照,提供方)#确认拥有
        结果=[]#目录
        for 模型 in 快照['models'].getModels(提供方):#把集合里的模型投影成建议目录
            输入=取模型字段(模型,'input')#输入模态
            结果.append({
                'provider':提供方,#提供方
                'id':取模型字段(模型,'id'),#模型id
                'name':取模型字段(模型,'name'),#展示名
                'inputModalities':list(输入),#输入模态
            })#一条目录
        return 结果#建议目录
    def 解析模型(自身,提供方,模型,信号=None):
        """解析精确模型。"""
        快照=自身.当前()#当前快照
        配置项=自身.配置于(快照,提供方)#已解析配置
        已解析模型=自身.模型于(快照,提供方,模型)#已配置模型
        默认档位=可描述思考档位(已解析模型,配置项.get('reasoning'))#描述用默认档位
        配置上限=配置项['configuredMaxTokens'].get(模型)#配置的按次上限
        信息={
            'provider':提供方,#提供方
            'id':模型,#模型id
            'name':取模型字段(已解析模型,'name'),#展示名
            'inputModalities':list(取模型字段(已解析模型,'input')),#输入模态
            'context':{'contextWindow':取模型字段(已解析模型,'contextWindow')},#窗口
        }#已解析信息
        if 配置上限 is not None:#配置显式写了按次上限才带 defaultMaxTokens
            信息['defaultMaxTokens']=配置上限#有配置上限才带上
        信息.update(推理信息(已解析模型,默认档位))#推理元数据
        return 信息#已解析信息
    def 流式(自身,选项):
        """流式调用。"""
        停止=选项.get('stop')#停止序列
        if 停止 is not None:#本后端不支持 GenerateOptions.stop
            raise llm.大模型错误('llm-pi-ai does not support GenerateOptions.stop','UNSUPPORTED_OPTION')#不支持
        快照=自身.当前()#本次快照
        提供方=选项['provider']#提供方
        模型标识=选项['model']#模型id
        配置项=自身.配置于(快照,提供方)#本次配置
        模型=自身.模型于(快照,提供方,模型标识)#本次模型
        请求力度=选项.get('reasoningEffort')#请求力度
        if 请求力度 is None:#请求没给力度则用路由配置默认
            请求力度=配置项.get('reasoning')#配置力度
        推理=解析思考档位(模型,请求力度)#校验力度
        密钥=自身.配置['resolveApiKey'](提供方,配置项)#从本快照解析密钥
        消费方=中止控制器()#消费方中止
        调用方信号=选项.get('signal')#调用方信号
        if 调用方信号 is None:#调用方未给信号
            上游=消费方.信号#只用消费方
        else:#融合
            上游=合成信号([调用方信号,消费方.信号])#融合调用方与消费方
        空闲超时毫秒=配置项['streamIdleTimeoutMs']#空闲超时
        看门狗=空闲看门狗(上游,空闲超时毫秒,流空闲超时码)#空闲看门狗
        try:#打开上游并消费翻译后的流
            对话=选项['messages']#对话
            含图片=False#对话是否含图片
            for 消息 in 对话:#先扫一遍对话，决定要不要附件服务
                内容=消息['content']#内容
                if llm.内容含图片(内容):#见到图片即可停
                    含图片=True#含图片
                    break#已判定
            输入=取模型字段(模型,'input')#输入模态
            if 含图片 and 'image' not in 输入:#模型目录没声明 image 模态
                标识=取模型字段(模型,'id')#模型id
                raise llm.大模型错误('pi-ai model "'+str(标识)+'" does not support image input','UNSUPPORTED_CONTENT')#不支持图片
            附件=None#附件服务
            if 含图片:#有图片才解析附件钩子
                解析附件=自身.配置.get('resolveAttachments')#可选附件钩子
                if 解析附件 is not None:#插件装了附件钩子才调用
                    附件=解析附件()#有图片才解析附件服务
            if 含图片 and 附件 is None:#需要图片却没有持久附件服务
                raise llm.大模型错误('pi-ai image input requires the durable attachment service','UNSUPPORTED_CONTENT')#缺少附件服务
            if 附件 is None:#没有附件则走同步纯文本转换
                上下文=转派上下文(选项)#同步纯文本
            else:#有附件则解析图片
                上下文=转派上下文(选项,附件)#解析图片
            流选项=配置流选项(配置项,推理,密钥)#配置旋钮
            温度=选项.get('temperature')#温度
            if 温度 is not None:#请求给了温度才带上
                流选项['temperature']=温度#有温度才带上
            上限=选项.get('maxTokens')#上限
            if 上限 is not None:#请求给了上限才带上
                流选项['maxTokens']=上限#有上限才带上
            会话=选项.get('sessionId')#会话
            if 会话 is not None:#有会话 id 才写入流选项
                流选项['sessionId']=str(会话)#有会话才带上
            流选项['signal']=看门狗.信号#看门狗信号
            流选项['headers']=请求头(配置项.get('headers'))#合并头
            窗口=取模型字段(模型,'contextWindow')#窗口
            事件=快照['models'].streamSimple(模型,上下文,流选项)#打开pi-ai流
            翻译=转流块(事件,窗口)#翻译后的生成器
            迭代器=iter(翻译)#翻译后的迭代器
            耗尽=False#是否正常耗尽
            try:#带空闲监视地消费翻译迭代器
                while True:#直到上游 done
                    结果=看门狗.下一步(迭代器)#带空闲监视的下一步
                    超时=取超时(看门狗.信号,流空闲超时码)#空闲超时
                    if 超时 is not None:#空闲看门狗到期则抛超时原因
                        raise 超时#超时则抛
                    if 结果['done']:#上游正常结束
                        耗尽=True#正常耗尽
                        return#结束生成器
                    yield 结果['value']#让出一块
            finally:#生成器结束
                if not 耗尽:#调用方提前停消费则中止上游
                    消费方.中止('pi-ai stream consumer stopped')#中止消费方
                    try:#通知上游取消
                        翻译.close()#关闭迭代器
                    except Exception:#吞掉拆除期中止
                        pass#稳定信号已拥有SDK终止；return时的中止不能再添第二种结果
        except Exception as 错误:#读取或打开失败
            if 取超时(看门狗.信号,流空闲超时码) is not None:#空闲超时优先于其它失败
                raise llm.大模型错误('pi-ai stream idle timeout after '+str(空闲超时毫秒)+'ms','TIMEOUT',{'cause':错误})#超时
            if 调用方信号 is not None and 源已中止(调用方信号):#调用方中止
                raise llm.大模型错误('pi-ai request aborted by caller','ABORTED',{'cause':错误})#中止
            raise 错误#其余原样抛
        finally:#生成器结束
            消费方.中止('pi-ai stream consumer stopped')#中止消费方
            看门狗.释放()#释放看门狗定时器
