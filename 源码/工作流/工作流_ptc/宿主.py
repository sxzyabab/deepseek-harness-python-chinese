"""经共享沙箱 PTC 执行器的工作流子归属与进度。"""
import json,threading#程序字面量与清理线程
from urllib.parse import quote as 百分号编码#data URL
from ...内核.会话 import 会话标识#子 id 品牌
from ...内核.工具.json模式 import 断言对象json模式#对象 JSON 模式
from ...工具.超时 import 中止控制器,已中止,若已中止则抛出,等待中止#中止
from ...工具.值 import 断言永不,快照json值#穷尽与 JSON 边界
from .宾客源码 import 工作流宾客源码#自包含宾客 JS
from .领域 import 渲染抛出#拆除失败文本
from .运行时 import 任务,全部并发,全部结算,赛跑#本包并发

__all__=['ptc工作流运行']#仅中文公开名

编码=json.dumps#JSON 编码

宾客网址='data:text/javascript,'+百分号编码(工作流宾客源码,safe="-_.!~*'()")#data URL
程序=('const { runWorkflowGuest } = await import('
    +编码(宾客网址,ensure_ascii=False,separators=(',',':'),allow_nan=False)
    +'); return await runWorkflowGuest(workflowHost);')#注入宾客的 JS 程序体

def 对象(值):#绑定参数必须是对象
    """绑定参数必须是非数组对象。"""
    if 值 is None or type(值) is not dict:#不是对象
        raise RuntimeError('workflow binding requires an object')#拒绝
    return 值#对象

def 文本(值,名称):#必须字符串
    """字段必须是字符串。"""
    if type(值) is not str:#不是串
        raise RuntimeError('workflow '+名称+' must be a string')#拒绝
    return 值#字符串

def json值(值):#无损 JSON
    """快照为无损 JSON，否则拒绝。"""
    结果=快照json值(值)#快照
    if 结果 is None:#有损
        raise RuntimeError('workflow binding value must be lossless JSON')#拒绝
    return 结果#JSON

def 子请求(值):#ChildStartRequest
    """从绑定参数抽出子启动请求。"""
    请求=对象(值)#对象
    提示词=文本(请求['prompt'] if 'prompt' in 请求 else None,'prompt')#提示词
    提供方=文本(请求['provider'],'provider') if 'provider' in 请求 and 请求['provider'] is not None else None#提供方
    模型=文本(请求['model'],'model') if 'model' in 请求 and 请求['model'] is not None else None#模型
    模式=None#可选 schema
    if 'schema' in 请求 and 请求['schema'] is not None:#有模式
        候选=对象(请求['schema'])#对象
        断言对象json模式(候选)#子集
        模式=候选#收下
    结果={'prompt':提示词}#提示词
    if 提供方 is not None:#有提供方
        结果['provider']=提供方#带上
    if 模型 is not None:#有模型
        结果['model']=模型#带上
    if 模式 is not None:#有模式
        结果['schema']=模式#带上
    return 结果#请求

def 智能体信息(值):#WorkflowAgentInfo
    """从绑定参数抽出智能体身份。"""
    信息=对象(值)#对象
    序号=信息['seq'] if 'seq' in 信息 else None#序号
    if type(序号) is bool or type(序号) is not int or 序号<1:#必须正整数
        raise RuntimeError('workflow agent sequence must be a positive integer')#拒绝
    结果={#身份
        'seq':序号,#序号
        'label':文本(信息['label'] if 'label' in 信息 else None,'agent label'),#标签
        'childId':会话标识(文本(信息['childId'] if 'childId' in 信息 else None,'child id')),#子 id
    }#身份结束
    if 'phase' in 信息 and 信息['phase'] is not None:#有阶段
        结果['phase']=文本(信息['phase'],'agent phase')#阶段
    return 结果#信息

def 进度(值):#一条进度事件
    """校验一条进度事件。"""
    事件=对象(值)#对象
    种类=事件['type'] if 'type' in 事件 else None#类型
    if 种类=='phase':#阶段
        return {'type':'phase','title':文本(事件['title'] if 'title' in 事件 else None,'phase')}#阶段
    if 种类=='log':#日志
        return {'type':'log','message':文本(事件['message'] if 'message' in 事件 else None,'log')}#日志
    if 种类=='agent-start':#开始
        return {'type':'agent-start','info':智能体信息(事件['info'] if 'info' in 事件 else None)}#开始
    if 种类=='agent-end':#结束
        信息=对象(事件['info'] if 'info' in 事件 else None)#信息
        结局=信息['outcome'] if 'outcome' in 信息 else None#结局
        if 结局 not in ('completed','failed','cancelled'):#非法
            raise RuntimeError('invalid workflow agent outcome')#拒绝
        合并=智能体信息(信息)#身份
        合并['outcome']=结局#结局
        return {'type':'agent-end','info':合并}#结束
    raise RuntimeError('invalid workflow progress event')#未知

def 进度批(值):#进度数组
    """校验一批进度事件。"""
    if type(值) is not list:#必须数组
        raise RuntimeError('workflow progress requires an array of events')#拒绝
    return [进度(项) for 项 in 值]#逐条

def 工作流结果值(值):#WorkflowResult
    """校验 PTC 完成值为工作流结果。"""
    结果=对象(值)#对象
    原因=结果['stopReason'] if 'stopReason' in 结果 else None#停止原因
    if 原因 not in ('completed','error','cancelled'):#非法
        raise RuntimeError('invalid workflow stop reason')#拒绝
    计数=结果['agentsStarted'] if 'agentsStarted' in 结果 else None#计数
    if type(计数) is bool or type(计数) is not int or 计数<0:#非法
        raise RuntimeError('invalid workflow agent count')#拒绝
    if 'value' not in 结果:#缺完成值
        raise RuntimeError('workflow result is missing its value')#拒绝
    规范化={'value':结果['value'],'stopReason':原因,'agentsStarted':计数}#必填
    if 'error' in 结果 and 结果['error'] is not None:#有错误
        规范化['error']=文本(结果['error'],'error')#错误
    return 规范化#结果

class ptc工作流运行:#持有者所有的工作流
    """取消立刻停程序；结算等待受管进程与每个已接纳子的启动/拆除。引擎卸载不使捕获的运行时或子智能体句柄失效。"""
    def __init__(自身,上下文,子智能体,运行时,标识,元数据,父,初始化,提供方,政策,观察器,信号=None):#钉字段并开跑
        """记下捕获的服务句柄并在后台驱动。"""
        自身.ctx=上下文#上下文
        自身._子智能体=子智能体#子智能体服务
        自身._运行时=运行时#PTC 运行时
        自身.id=标识#运行标识
        自身.meta=元数据#元数据
        自身._父=父#父智能体
        自身._初始化=初始化#boot 输入
        自身._提供方=提供方#子提供方名
        自身._政策=政策#沙箱政策
        自身._观察器=观察器#进度观察
        自身._信号=信号#外部中止
        自身._控制器=中止控制器()#本运行中止
        自身._子表={}#callId 到记录
        自身._未决=[]#进行中的绑定任务
        自身._活智能体={}#seq 到信息
        自身._已启动=0#子计数
        自身._终态=False#已有终态
        自身._取消原因=None#首次取消原因
        自身._已拆=None#共享拆除任务
        自身.结果=任务()#永不拒绝
        def 外部中止():#外部信号
            """外部中止则取消运行。"""
            自身.取消('workflow signal aborted')#取消
        自身._外部中止=外部中止#保存以便摘掉
        if 信号 is not None:#有外部信号
            if 已中止(信号):#已经中止
                外部中止()#立刻
            else:#监视
                def 等外部():#后台
                    """等到外部中止。"""
                    等待中止(信号)#等待
                    外部中止()#取消
                threading.Thread(target=等外部,daemon=True).start()#监视
        def 开跑():#后台驱动
            """驱动并兑现结果。"""
            自身.结果.兑现(自身._驱动())#永不拒绝
        threading.Thread(target=开跑,daemon=True).start()后才挂记录

    def 取消(自身,原因='workflow cancelled'):#停脚本并中止子
        """停脚本并中止待完成与已发布子。首次请求获胜。"""
        if 自身._终态 or 自身._取消原因 is not None:#已终态或已取消
            return#忽略
        自身._取消原因=原因#记下
        自身._控制器.中止(RuntimeError(原因))#中止
        for 记录 in list(自身._子表.values()):#已发布
            自身._拆除子(记录)#拆除

    def 销毁(自身):#取消未完成并等待清理
        """取消未完成工作并等待程序与子清理。重复调用共享同一完成。"""
        自身.取消('workflow disposed')#取消
        if 自身._已拆 is None:#首次
            完成=任务()#拆除任务
            自身._已拆=完成#共享
            def 等结果():#等运行结果
                """结果落定即拆除完成。"""
                try:#等待
                    自身.结果.等待()#结果
                except BaseException:#不应拒绝
                    pass#吞掉
                完成.兑现()#拆除完成
            threading.Thread(target=等结果,daemon=True).start()#后台
        自身._已拆.等待()#等到
        return None#拆除完成

    def _要求活动(自身):#已中止则抛
        """已中止则抛出原因。"""
        若已中止则抛出(自身._控制器.信号)#抛

    def _跟踪(自身,函数):#登记未决绑定
        """跑一路绑定并跟踪未决。函数无参。"""
        完成=任务()#本次
        自身._未决.append(完成)#登记
        def 在线程执行():#后台
            """执行并摘掉。"""
            try:#执行
                完成.兑现(函数())#成功
            except BaseException as 错误:#失败
                完成.拒绝(错误)#拒绝
            if 完成 in 自身._未决:#仍在
                自身._未决.remove(完成)#摘掉
        threading.Thread(target=在线线程执行,daemon=True).start()
        return 完成.等待()#等本路

    def _绑定(自身):#workflowHost 函数表
        """PTC 绑定函数。"""
        def 开始(输入):#begin
            """返回初始化 JSON。"""
            自身._要求活动()#活动
            return json值(自身._初始化)#初始化
        def 启动子(值):#startChild
            """启动一个子。"""
            def 在线程执行():#本路
                """启动子。"""
                return 自身._启动子(子请求(值))#启动
            return 自身._跟踪(在线线程执行)#跟踪
        def 子结果绑定(值):#childResult
            """等一个子的结果。"""
            def 在线程执行():#本路
                """等子结果。"""
                return 自身._子结果(自身._子(值))#结果
            return 自身._跟踪(在线线程执行)#跟踪
        def 拆除子绑定(值):#disposeChild
            """拆除一个子。"""
            自身._拆除子(自身._子(值))#拆除
            return None#null
        def 进度绑定(值):#progress
            """分派一批进度。"""
            for 事件 in 进度批(值):#逐条
                自身._当进度(事件)#分派
            return None#null
        return {'begin':开始,'startChild':启动子,'childResult':子结果绑定,'disposeChild':拆除子绑定,'progress':进度绑定}#函数表

    def _子(自身,值):#按 callId 取记录
        """按 callId 取活动子记录。"""
        自身._要求活动()#活动
        请求=对象(值)#对象
        调用标识=请求['callId'] if 'callId' in 请求 else None#id
        if type(调用标识) is bool or type(调用标识) is not int:#必须整数
            raise RuntimeError('workflow child call id must be an integer')#拒绝
        if 调用标识 not in 自身._子表:#不活动
            raise RuntimeError('workflow child call is not active')#拒绝
        return 自身._子表[调用标识]#记录

    def _启动子(自身,请求):#发布一个子
        """经配置提供方启动一个子。"""
        自身._要求活动()#活动
        自身._已启动+=1#计数
        调用标识=自身._已启动#callId
        启动={'prompt':[{'type':'text','text':请求['prompt']}],'parent':自身._父,'signal':自身._控制器.信号}#启动请求
        if 'schema' in 请求:#有模式
            启动['outputSchema']=请求['schema']#输出模式
        if 'provider' in 请求 or 'model' in 请求:#有覆盖
            选项={}#agentOptions
            if 'provider' in 请求:#提供方
                选项['provider']=请求['provider']#带上
            if 'model' in 请求:#模型
                选项['model']=请求['model']#带上
            启动['agentOptions']=选项#覆盖
        跑=自身._子智能体.启动(自身._提供方,启动)#发布
        记录={'callId':调用标识,'run':跑}#记录
        自身._子表[调用标识]=记录#登记
        if 已中止(自身._控制器.信号):#启动期间已取消
            自身._拆除子(记录)#拆除
            raise RuntimeError('workflow child started after cancellation')#拒绝
        return {'callId':调用标识,'childId':跑.id}#引用

    def _子结果(自身,记录):#等子终态
        """与中止赛跑，等子终态 JSON。"""
        若已中止则抛出(自身._控制器.信号)#已中止
        def 等子():#子结果
            """等提供方结果。"""
            return 记录['run'].result.等待()#子结果
        def 等中止():#中止
            """等到中止再抛。"""
            等待中止(自身._控制器.信号)#等待
            若已中止则抛出(自身._控制器.信号)#抛原因
            raise RuntimeError('The operation was aborted')#默认
        结果=赛跑([等子,等中止])#先到
        投影={'output':结果['output'],'stopReason':结果['stopReason']}#必填
        if 'structured' in 结果 and 结果['structured'] is not None:#有结构化
            投影['structured']=结果['structured']#带上
        return json值(投影)#JSON

    def _拆除子(自身,记录):#共享拆除
        """所有清理路径共享的子拆除。"""
        if 'disposal' in 记录 and 记录['disposal'] is not None:#已有
            记录['disposal'].等待()#加入
            return None#结束
        完成=任务()#本次拆除
        记录['disposal']=完成#共享
        def 跑拆除():#后台
            """调用提供方拆除。"""
            try:#拆除
                记录['run'].销毁()#销毁
            except BaseException as 错误:#失败
                自身.ctx.日志.警告('workflow-ptc: child dispose failed: '+渲染抛出(错误))#警告
            finally:#摘掉
                自身._子表.pop(记录['callId'],None)#移除
                完成.兑现()#完成
        threading.Thread(target=跑拆除,daemon=True).start()
        完成.等待()#等到
        return None#结束

    def _当进度(自身,事件):#分派进度
        """把一条进度交给观察器。"""
        自身._要求活动()#活动
        种类=事件['type']#类型
        if 种类=='phase':#阶段
            自身._观察器.阶段(事件['title'])#阶段
            return
        if 种类=='log':#日志
            自身._观察器.日志(事件['message'])#日志
            return
        if 种类=='agent-start':#开始
            自身._活智能体[事件['info']['seq']]=事件['info']#记下
            自身._观察器.智能体开始(事件['info'])#开始
            return
        if 种类=='agent-end':#结束
            自身._结束智能体(事件['info'])#结束
            return
        断言永不(事件,'workflow progress')#封闭联合

    def _结束智能体(自身,信息):#agent-end
        """成对结束；重复则忽略。"""
        if 信息['seq'] not in 自身._活智能体:#未开始或已结束
            return#忽略
        del 自身._活智能体[信息['seq']]#摘掉
        自身._观察器.智能体结束(信息)#结束

    def _已取消结果(自身):#取消结果
        """构造 cancelled 结果。"""
        return {'value':None,'stopReason':'cancelled','error':'workflow run cancelled: '+str(自身._取消原因),'agentsStarted':自身._已启动}#取消

    def _驱动(自身):#跑 PTC 程序
        """跑 PTC 程序并清理子。"""
        结果=None#终态
        try:#执行
            规格=自身._运行时.解析({'program':程序,'bindings':[{'global':'workflowHost','functions':自身._绑定()}],'cwd':自身._政策['workspaceRoot'],'sandboxPolicy':自身._政策,'timeoutMs':None,'signal':自身._控制器.信号})#解析
            结局=自身._运行时.运行(规格)#运行
            自身._终态=True#终态
            if 自身._取消原因 is not None:#取消获胜
                结果=自身._已取消结果()#取消
            elif 'error' in 结局 and 结局['error'] is not None:#PTC 失败
                结果={'value':None,'stopReason':'error','error':'workflow execution failed ('+结局['error']['kind']+'): '+结局['error']['message'],'agentsStarted':自身._已启动}#错误
            else:#完成值
                结果=工作流结果值(结局['value'] if 'value' in 结局 else None)#结果
        except BaseException as 错误:#执行抛错
            自身._终态=True#终态
            if 自身._取消原因 is None:#非取消
                结果={'value':None,'stopReason':'error','error':渲染抛出(错误),'agentsStarted':自身._已启动}#错误
            else:#取消
                结果=自身._已取消结果()#取消
        finally:#清理
            自身._终态=True#终态
            自身._控制器.中止(RuntimeError('workflow settled'))#结算中止
            for 记录 in list(自身._子表.values()):#已发布
                自身._拆除子(记录)#拆除
            while len(自身._未决)>0:#未决绑定
                全部结算(list(自身._未决))#结算
            拆除表=list(自身._子表.values())#快照
            def 制作拆除(记录):#钉住记录
                """钉住一条拆除。"""
                def 在线程执行():#一路
                    """拆除一路。"""
                    自身._拆除子(记录)#拆除
                return 在线程执行#函数
            if len(拆除表)>0:#还有
                全部并发([制作拆除(记录) for 记录 in 拆除表])#并发拆除
            自身._子表.clear()#清空
            for 信息 in list(自身._活智能体.values()):#未配对结束
                结束=dict(信息)#拷贝
                结束['outcome']='cancelled'#取消
                自身._结束智能体(结束)#合成 cancelled
        return 结果#终态
