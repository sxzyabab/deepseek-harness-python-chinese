"""LLM 服务：带瀑布可拦截流式调用 API 的适配器注册表。

对齐上游 `llm/src/index.ts`。公开面仅中文名；ctx 槽 `llm`、事件名与失败码字面量保持上游。
无英文别名。中文消费方别名（大模型／超出）保留供下游包导入。
"""
import math,threading#有限数与后台观察
from ...依赖 import cordis#外部依赖胶水
from ...依赖.工具 import 获取内部数据#读事件总线内部成员
服务=cordis.服务#服务基类
from .归属 import 应用身份,用户代理,归属头#再导出归属
from .标识构造 import (
    消息标识,#消息身份品牌
    调用标识,#工具调用品牌
    提供方请求标识,#提供方请求品牌
    尝试标识,#流式尝试品牌
    推理力度标识,#推理力度品牌
)
from .永不 import 断言永不#再导出穷尽辅助
from .错误 import (
    装备错误,#错误基类
    上下文窗口溢出码,#上下文溢出码
    配额耗尽码,#配额耗尽码
    空响应码,#空响应码
    非法凭证码,#非法凭证码
    图片卸载必需码,#图片卸载尚未满足码
    是否上下文窗口溢出,#溢出分类
    是否配额耗尽,#配额分类
    错误链,#错误链渲染
    是否装备错误,#实例判定
    上下文窗口超出码,#消费方别名
    配额超出码,#消费方别名
    是否上下文窗口超出错误,#消费方别名
    是否配额超出错误,#消费方别名
)
from .密钥 import 规范化密钥#再导出密钥判定
from .类型 import *#再导出类型词表
from .内容 import (#再导出内容辅助
    内容含图片,#内容含图片
    内容含文件,#内容含文件
    仅文本图片文案,#仅文本占位
    请求图片句柄文案,#句柄文案
    卸载图片文案,#卸载占位
    文件句柄文案,#文件句柄
    投影文件为文本,#文件投影
    投影图片为仅文本,#仅文本投影
    卸载图片前缀张数,#卸载前缀
    按政策卸载请求图片,#按政策卸载
    投影卸载图片,#投影已卸载出现
    必需图片卸载,#还需卸载张数
    解析图片附件访问,#访问解析
)#内容辅助
from .消息 import (
    上下文摘要最大字符,#摘要上限
    截上下文摘要,#截摘要
    冻结消息,#冻结消息
    创建消息,#创建消息
    创建用户消息,#创建用户消息
    创建助手消息,#创建助手消息
    创建系统消息,#创建系统消息
    创建工具结果消息,#创建工具结果消息
    是否词增量,#是否可见增量
)
from .重试政策 import 解析重试政策,重试政策错误#再导出重试政策
from .组装器 import 块组装器#再导出块组装器
from .助手流 import (#再导出助手流
    助手流累积器,#紧凑累积器
    助手流累加器,#约定别名
    展开助手流,#展开为带时块
    是否令牌增量,#令牌增量判定
    是否可见块,#可见块判定
    块是否含可见文本,#可见文本判定
    块含可见文本,#简名
    游程首令牌时间,#游程首令牌
    游程首可见时间,#游程首可见
    助手流首令牌时间,#流首令牌
    助手流是否有可见内容,#流可见内容
    助手流有可见内容,#简名
    助手流是否有可见文本,#流可见文本
    助手流有可见文本,#简名
    末条助手流块,#末条原始块
    末次助手流块,#约定别名
    助手流块列表,#全部原始块
    拼接助手流文本,#拼接文本
    组装助手流,#喂入组装器
)#助手流导出结束
from .调用配置 import (
    调用配置相等,#配置相等
    深冻结,#深冻结
    标记循环请求,#标记循环请求
    是否循环请求,#是否循环请求
    是否冻结,#是否已冻结
    结构化克隆,#拆离克隆
    可弱引用映射,#可弱引用映射
    冻结映射,#冻结映射
)
from .适配器失败 import 归一化语言模型失败#导入适配器失败归一化

__all__=(#仅中文公开名；无英文别名
    '应用身份','用户代理','归属头',
    '消息标识','调用标识','提供方请求标识','尝试标识','推理力度标识',
    '断言永不','装备错误','上下文窗口溢出码','配额耗尽码','空响应码','非法凭证码','图片卸载必需码',
    '是否上下文窗口溢出','是否配额耗尽','错误链','是否装备错误',
    '上下文窗口超出码','配额超出码','是否上下文窗口超出错误','是否配额超出错误',
    '规范化密钥','断言可用密钥','断言可用接口密钥',
    '中止信号','内容含图片','内容含文件','仅文本图片文案','请求图片句柄文案','卸载图片文案',
    '文件句柄文案','投影文件为文本','投影图片为仅文本','投影卸载图片','必需图片卸载',
    '卸载图片前缀张数','按政策卸载请求图片','解析图片附件访问',
    '语言模型失败','文本块','推理块','图片块','工具调用块','工具结果块',
    '文本模态','图片模态','模型模态','正常停止','工具调用停止','达到令牌上限',
    '令牌用量','提供方信息','可配置提供方','模型发现请求','发现到的模型',
    '模型信息','模型上下文','推理力度信息','模型推理信息','已解析模型信息',
    '系统提示词更新','图片请求预算','回放信封','工具模式','生成选项',
    '上下文摘要最大字符','截上下文摘要','冻结消息',
    '创建消息','创建用户消息','创建助手消息','创建系统消息','创建工具结果消息','是否词增量',
    '解析重试政策','重试政策错误','重试政策模式','块组装器',
    '助手流累积器','助手流累加器','展开助手流','是否令牌增量','是否可见块','块是否含可见文本','块含可见文本',
    '游程首令牌时间','游程首可见时间','助手流首令牌时间','助手流是否有可见内容','助手流有可见内容',
    '助手流是否有可见文本','助手流有可见文本','末条助手流块','末次助手流块','助手流块列表','拼接助手流文本','组装助手流',
    '调用配置相等','深冻结','标记循环请求','是否循环请求','是否冻结','结构化克隆',
    '可弱引用映射','冻结映射','归一化语言模型失败',
    '语言模型错误','语言模型适配器','适配器注册句柄','目录注册句柄','语言模型运行时',
    '已中止','若已中止则抛出',
    '大模型错误','大模型适配器','大模型运行时',
    '图片请求定价','文件请求文本',
)#公开面结束

def 已中止(信号):
    """信号是否已中止。无信号视为未中止。"""
    if 信号 is None:#无信号
        return False#未中止
    return 信号._事件.is_set()#Event 置位

class 语言模型错误(装备错误):#LLM 相关失败的有类型错误
    """LLM 相关失败的有类型错误。"""
    def __init__(自身,消息,码,选项=None):#校验可序列化事实并冻结 failure
        """校验可序列化事实并冻结 failure。"""
        if not isinstance(消息,str) or len(消息)==0:#消息非法
            raise 装备错误('LlmError message must be a non-empty string','INVALID_ERROR')#消息必须非空
        if not isinstance(码,str) or len(码)==0:#code 非法
            raise 装备错误('LlmError code must be a non-empty string','INVALID_ERROR')#code 必须非空
        if 选项 is None:#无选项
            选项={}#无选项
        if 'status' in 选项:#有 HTTP 状态
            状态=选项['status']#HTTP 状态
            是整数=isinstance(状态,(int,float)) and not isinstance(状态,bool) and math.isfinite(状态) and 状态==int(状态)#合法整数
            if not 是整数 or 状态<100 or 状态>599:#状态越界
                raise 装备错误('LlmError status must be an integer from 100 through 599','INVALID_ERROR')#状态越界
        if 'providerRetryAfterMs' in 选项:#有建议等待
            等待=选项['providerRetryAfterMs']#建议等待
            if not (isinstance(等待,(int,float)) and not isinstance(等待,bool) and math.isfinite(等待) and 等待>0):#等待非法
                raise 装备错误('LlmError providerRetryAfterMs must be a positive finite number','INVALID_ERROR')#等待非法
        if 'requestId' in 选项:#有请求 id
            请求=选项['requestId']#请求 id
            if not isinstance(请求,str) or len(请求)==0:#请求 id 非法
                raise 装备错误('LlmError requestId must be a non-empty string','INVALID_ERROR')#请求 id 非法
        if 'offloadImages' in 选项:#有还需卸载张数
            卸载=选项['offloadImages']#还需卸载张数
            是正安全=isinstance(卸载,(int,float)) and not isinstance(卸载,bool) and 卸载==int(卸载) and 卸载>0#正安全整数
            if not 是正安全:#张数非法
                raise 装备错误('LlmError offloadImages must be a positive safe integer','INVALID_ERROR')#张数非法
        装备错误.__init__(自身,消息,码,选项)#交给装备错误
        自身.name='LlmError'#固定类名
        事实={'message':消息,'code':码}#可序列化事实
        if 'status' in 选项:#有状态才写入
            事实['status']=选项['status']#有状态才带上
        if 'providerRetryAfterMs' in 选项:#有等待才写入
            事实['providerRetryAfterMs']=选项['providerRetryAfterMs']#有等待才带上
        if 'requestId' in 选项:#有请求 id 才写入
            事实['requestId']=选项['requestId']#有请求 id 才带上
        if 'offloadImages' in 选项:#有还需卸载张数
            事实['offloadImages']=选项['offloadImages']#有张数才带上
        自身.failure=深冻结(事实)#冻结可序列化事实

def 若已中止则抛出(信号):
    """已中止则抛出信号上承载的异常。"""
    if not 已中止(信号):#未中止
        return#继续
    原因=信号._异常#异常对象承载原因
    if 原因 is None:#无原因
        raise 语言模型错误('aborted','ABORTED')#默认中止
    raise 原因#原样抛出

def 断言可用密钥(原始,包名,引用):#接受已提供凭证或拒绝
    """接受一条已提供凭证，或因其无法使用而拒绝。"""
    判定=规范化密钥(原始)#判定已提供密钥
    if 'ok' in 判定 and 判定['ok']:#通过
        return 判定['value']#通过则返回修剪后的密钥
    if 'reason' in 判定 and 判定['reason']=='empty':#空密钥
        文案=包名+': the API key resolved from '+引用+' is blank; set '+引用+' to the raw key (the web Models page writes it) or export it in the launching environment'#空密钥诊断
    else:#非法字符
        文案=包名+': the API key resolved from '+引用+' contains characters no HTTP header can carry; set '+引用+' to the raw key alone (the web Models page writes it)'#非法字符诊断
    raise 语言模型错误(文案,非法凭证码)#按原因抛出非法凭证

class 语言模型适配器:#面向 harness 消息与流词表的提供方线路适配器
    """面向 harness 消息与流词表的提供方线路适配器。"""
    def 提供方信息(自身,提供方):#描述本适配器拥有的一条提供方路由
        """描述本适配器拥有的一条提供方路由。"""
        return {'id':提供方,'name':提供方}#默认 id 与 name 同路由名

    def 提供方重试政策(自身,提供方):#返回随本路由捕获的提供方拥有重试政策
        """返回随本路由捕获的提供方拥有重试政策。"""
        return None#缺省交给运行时填普通默认

    def 图片请求定价(自身,提供方,模型):#图片请求定价
        """解析一条精确模型路由的提供方侧请求图定价；默认声明无。"""
        return None#默认无

    def 列出模型(自身,提供方):#列出本适配器当前能为一条所拥有提供方通告的模型
        """列出本适配器当前能为一条所拥有提供方通告的模型。"""
        return []#默认空目录

    def 解析模型(自身,提供方,模型,信号=None):#解析某一精确模型的全部可用元数据
        """解析某一精确模型的全部可用元数据。"""
        return {'provider':提供方,'id':模型,'name':模型}#默认身份等于所给 id

    def 准备调用(自身,提供方,模型,信号=None):#把模型元数据与派发绑到同一代适配器
        """把精确模型元数据与最终派发绑到同一代适配器事实。"""
        return {
            'model':自身.解析模型(提供方,模型,信号),#本代模型元数据
            'stream':自身.流式,#本代流入口
        }#已准备适配器调用

    def 流式(自身,选项):#把一次模型调用流成原始块
        """把一次模型调用流成原始块。唯一必需的方法。"""
        raise NotImplementedError('LlmAdapter.stream')#子类必须实现

class 适配器注册句柄:#适配器注册的拆除与原子路由替换
    """适配器注册的拆除与原子路由替换。"""
    def __init__(自身,拆除,替换):#保存拆除与替换回调
        """保存拆除与替换回调。"""
        自身._拆除=拆除#拆除回调
        自身.替换=替换#替换回调

    def __call__(自身):#释放本注册当前持有的每条路由
        """释放本注册当前持有的每条路由。"""
        自身._拆除()#同步拆除

class 目录注册句柄:#可配置提供方注册的拆除与原子替换
    """可配置提供方注册的拆除与原子替换。"""
    def __init__(自身,拆除,替换):#保存拆除与替换回调
        """保存拆除与替换回调。"""
        自身._拆除=拆除#拆除回调
        自身.替换=替换#替换回调

    def __call__(自身):#撤回本注册当前持有的每条条目
        """撤回本注册当前持有的每条条目。"""
        自身._拆除()#同步拆除

class 语言模型运行时(服务):#抽象的 llm 服务
    """抽象的 llm 服务：适配器注册表外加经 llm/stream 瀑布可拦截的流式模型调用 API。"""
    def __init__(自身,ctx,配置=None):#以 llm 名注册服务
        """以 llm 名注册服务。"""
        服务.__init__(自身,ctx,'llm')#注册服务
        自身.适配器表={}#提供方路由到注册
        自身.目录={}#可配置提供方目录
        自身.发现表={}#设置命名空间到发现函数

    def 发出适配器已更新(自身):#通知拓扑观察者
        """通知拓扑观察者，不让一个坏监听器否决提交。"""
        参数=['llm/adapters-updated']#派发参数
        事件总线=获取内部数据(自身.ctx,'属性链')['事件']#事件总线，不经壳
        监听器列表=获取内部数据(事件总线,'解析监听器')(事件总线,'emit',参数)#逐个监听器
        不变量失败=None#记下第一个不变量失败
        for 监听器 in 监听器列表:#逐个监听器
            try:#独立收住
                监听器()#同步调用
            except Exception as 错误:#监听器契约未收窄抛出类型，按 code 字段识别不变量
                if getattr(错误,'code',None)=='INVARIANT':#不变量失败
                    if 不变量失败 is None:#只保留第一个
                        不变量失败=错误#只保留第一个
                    continue#继续其余监听器
                自身.警告适配器监听失败(错误)#其余失败只记日志
        if 不变量失败 is not None:#有不变量失败
            raise 不变量失败#提交后再抛不变量失败

    def 警告适配器监听失败(自身,错误):#记下监听器失败
        """同步与异步失败路径共用的、已收住监听器诊断。"""
        自身.ctx.日志.警告('llm: an llm/adapters-updated listener failed')#警告文案
        自身.ctx.日志.警告(错误)#附带错误

    def 注册适配器(自身,提供方列表,适配器):#为给定提供方路由注册适配器
        """为给定提供方路由注册适配器。全有或全无，随光纤拆除。"""
        持有=set()#本注册持有的路由
        已释放=False#是否已拆除
        def 执行体():#随光纤的 effect
            """随光纤的 effect。"""
            if len(提供方列表)==0:#初次注册为空
                raise 语言模型错误('an adapter must register at least one provider','INVALID_ADAPTER')#初次注册不得为空
            自身.提交路由(持有,自身.准备路由(提供方列表,适配器,持有))#校验并提交
            def 拆除():#拆除回调
                """拆除回调。"""
                nonlocal 已释放#改外层标记
                已释放=True#标记已释放
                for 提供方 in list(持有):#逐条释放
                    自身.适配器表.pop(提供方,None)#从表里去掉
                持有.clear()#清空持有
                自身.发出适配器已更新()#通知观察者
            yield 拆除#登记拆除
        释放=自身.ctx.副作用(执行体,'llm.registerAdapter()')#绑到本运行时
        def 同步拆除():#丢掉 effect 返回值的同步拆除
            """丢掉 effect 返回值的同步拆除。"""
            释放()#拆除
        def 替换(下一批):#原子替换路由
            """原子替换路由。"""
            if 已释放:#已拆除
                raise 语言模型错误('a disposed adapter registration cannot replace its routes','REGISTRATION_DISPOSED')#不得再替换
            自身.提交路由(持有,自身.准备路由(下一批,适配器,持有))#校验并提交新路由
        return 适配器注册句柄(同步拆除,替换)#返回句柄

    def 准备路由(自身,提供方列表,适配器,持有):#为适配器校验候选路由集合
        """为适配器校验一份候选路由集合，不做变更。"""
        已见=set()#本批已见路由
        注册列表=[]#待提交注册
        for 提供方 in 提供方列表:#逐条候选
            if len(提供方)==0:#名为空
                raise 语言模型错误('adapter provider names must be non-empty','INVALID_ADAPTER')#名不得空
            if 提供方 in 已见 or (提供方 in 自身.适配器表 and 提供方 not in 持有):#冲突
                raise 语言模型错误('an adapter for provider "'+提供方+'" is already registered','DUPLICATE_ADAPTER')#冲突
            信息=适配器.提供方信息(提供方)#适配器给出的元数据
            if 'id' not in 信息 or not isinstance(信息['id'],str) or 信息['id']!=提供方 or 'name' not in 信息 or not isinstance(信息['name'],str) or len(信息['name'])==0:#元数据非法
                raise 语言模型错误('adapter metadata for provider "'+提供方+'" must preserve its id and have a non-empty name','INVALID_ADAPTER')#元数据非法
            已见.add(提供方)#记下本批已见
            政策=适配器.提供方重试政策(提供方)#适配器给出的政策
            if 政策 is None:#缺省
                政策=解析重试政策(None,'llm: provider "'+提供方+'" retryPolicy')#缺省则普通默认
            注册列表.append({#一条待提交注册
                'adapter':适配器,#适配器实例
                'provider':{'id':信息['id'],'name':信息['name']},#拆离展示元数据
                'retryPolicy':政策,#已解析政策
            })#一条待提交注册
        return 注册列表#全部通过后返回

    def 提交路由(自身,持有,注册列表):#同步交换本注册的路由
        """在一段同步区里把本注册的路由换成已准备好的那些。"""
        for 提供方 in list(持有):#先释放旧路由
            自身.适配器表.pop(提供方,None)#先释放旧路由
        持有.clear()#清空持有
        for 注册 in 注册列表:#再挂上新的
            路由=注册['provider']['id']#提供方 id
            自身.适配器表[路由]=注册#写入表
            持有.add(路由)#记入持有
        自身.发出适配器已更新()#通知观察者

    def 列出提供方(自身):#描述已注册适配器的提供方路由
        """描述已注册适配器的提供方路由。"""
        结果=[]#拆离副本
        for 注册 in 自身.适配器表.values():#按注册顺序
            提供方=注册['provider']#展示元数据
            结果.append({'id':提供方['id'],'name':提供方['name']})#拆离
        return 结果#按注册顺序

    def 注册可配置提供方(自身,条目列表):#声明可通过配置激活的提供方路由
        """声明适配器插件可通过配置激活的提供方路由。"""
        持有=[]#本注册当前持有
        已拆除=False#是否已拆除
        def 提交(候选):#相对本注册尚未持有的一切完整校验候选集合
            """相对本注册尚未持有的一切完整校验候选集合，然后发布。"""
            nonlocal 持有#改外层持有
            拆离=[]#拆离后的候选
            本有=set()#本注册已持有的提供方
            for 条目 in 持有:#已持有
                本有.add(条目['provider'])#已持有
            for 条目 in 候选:#逐条候选
                if len(条目['provider'])==0 or len(条目['displayName'])==0 or len(条目['settingsNs'])==0:#必填字段空
                    raise 语言模型错误('configurable providers need a non-empty provider, displayName, and settingsNs','INVALID_DIRECTORY')#目录条目非法
                for 段 in 条目['settingsPath']:#路径段
                    if len(段)==0:#路径段有空
                        raise 语言模型错误('configurable provider "'+条目['provider']+'" has an empty settingsPath segment','INVALID_DIRECTORY')#路径非法
                冲突=条目['provider'] in 自身.目录 and 条目['provider'] not in 本有#被别人占用
                if not 冲突:#再查批内重复
                    for 已见 in 拆离:#批内已拆离
                        if 已见['provider']==条目['provider']:#批内重复
                            冲突=True#批内重复
                            break#找到即停
                if 冲突:#冲突
                    raise 语言模型错误('configurable provider "'+条目['provider']+'" is already declared','DUPLICATE_DIRECTORY')#冲突
                副本=dict(条目)#拆离副本
                副本['settingsPath']=list(条目['settingsPath'])#路径副本
                拆离.append(副本)#记下
            for 条目 in 持有:#先释放旧条目
                自身.目录.pop(条目['provider'],None)#先释放旧条目
            for 条目 in 拆离:#再挂上新的
                自身.目录[条目['provider']]=条目#再挂上新的
            持有=拆离#更新持有
            自身.发出适配器已更新()#通知观察者
        def 执行体():#随光纤的 effect
            """随光纤的 effect。"""
            if len(条目列表)==0:#初次注册为空
                raise 语言模型错误('a configurable-provider registration must declare at least one provider','INVALID_DIRECTORY')#不得为空
            提交(条目列表)#提交初集
            def 拆除():#拆除回调
                """拆除回调。"""
                nonlocal 已拆除,持有#改外层
                已拆除=True#标记已拆除
                for 条目 in 持有:#从目录去掉
                    自身.目录.pop(条目['provider'],None)#从目录去掉
                持有=[]#清空持有
                自身.发出适配器已更新()#通知观察者
            yield 拆除#登记拆除
        释放=自身.ctx.副作用(执行体,'llm.registerConfigurableProviders()')#绑到本运行时
        def 同步拆除():#同步拆除
            """同步拆除。"""
            释放()#拆除
        def 替换(下一批):#原子替换条目
            """原子替换条目。"""
            if 已拆除:#已拆除
                raise 语言模型错误('this configurable-provider registration was disposed','REGISTRATION_DISPOSED')#不得再替换
            提交(下一批)#校验并提交
        return 目录注册句柄(同步拆除,替换)#返回句柄

    def 列出可配置提供方(自身):#列出每个已声明的可配置提供方
        """列出每个已声明的可配置提供方，无论已注册还是休眠。"""
        结果=[]#拆离副本
        for 条目 in 自身.目录.values():#按声明顺序
            副本=dict(条目)#拆离
            副本['settingsPath']=list(条目['settingsPath'])#路径副本
            结果.append(副本)#记下
        return 结果#按声明顺序

    def 注册模型发现(自身,设置命名空间,发现):#注册模型发现
        """主动为这个插件拥有的设置命名空间询问提供方端点。"""
        def 执行体():#随光纤的 effect
            """随光纤的 effect。"""
            if len(设置命名空间)==0:#命名空间空
                raise 语言模型错误('model discovery needs a non-empty settings namespace','INVALID_DISCOVERY')#非法发现
            if 设置命名空间 in 自身.发现表:#已被占用
                raise 语言模型错误('model discovery for "'+设置命名空间+'" is already registered','DUPLICATE_DISCOVERY')#重复发现
            自身.发现表[设置命名空间]=发现#记下要约
            def 拆除():#撤回要约
                """撤回要约。"""
                自身.发现表.pop(设置命名空间,None)#撤回要约
            yield 拆除#登记拆除
        释放=自身.ctx.副作用(执行体,'llm.registerModelDiscovery()')#绑到本运行时
        def 同步拆除():#同步拆除
            """同步拆除。"""
            释放()#拆除
        return 同步拆除#disposer

    def 列出模型发现命名空间(自身):#列出可询问端点的命名空间
        """列出可以询问端点的设置命名空间，让界面只在可用之处提供该动作。"""
        return list(自身.发现表.keys())#按登记顺序的命名空间

    def 发现模型(自身,设置命名空间,请求):#发现端点模型
        """询问一个提供方端点它所通告的模型。"""
        发现=自身.发现表.get(设置命名空间)#取出发现回调
        if 发现 is None:#没有要约
            raise 语言模型错误('no model discovery is registered for "'+设置命名空间+'"','NO_DISCOVERY')#未注册发现
        路由=请求.get('provider') or ''#可选路由
        端点=请求.get('baseURL') or ''#可选端点
        if len(路由)==0 and len(端点)==0:#路由与端点都空
            raise 语言模型错误('model discovery needs a provider route or a baseURL','INVALID_DISCOVERY')#缺少目标
        通告=发现(请求)#发现回调已是同步，直取通告
        已见=set()#已见 id
        模型列表=[]#去重结果
        for 模型 in 通告:#逐个通告
            标识=模型.get('id')#模型 id
            if not isinstance(标识,str) or len(标识)==0 or 标识 in 已见:#非法或重复
                continue#非法或重复则跳过
            已见.add(标识)#记下已见
            候选={'id':标识}#拆离候选
            if 'name' in 模型:#有名字
                候选['name']=模型['name']#有名字才带上
            if 'contextWindow' in 模型:#有窗口
                候选['contextWindow']=模型['contextWindow']#有窗口才带上
            if 'maxTokens' in 模型:#有上限
                候选['maxTokens']=模型['maxTokens']#有上限才带上
            模型列表.append(候选)#记下
        return 模型列表#去重后的候选

    def 提供方重试政策(自身,提供方):#取出提供方政策
        """解析一条提供方路由注册时捕获的重试政策。"""
        return 自身.取注册(提供方)['retryPolicy']#从注册读取

    def 图片请求定价(自身,提供方,模型):#图片请求定价
        """解析一条精确路由的提供方侧请求图定价；未注册或声明无时为 None。"""
        注册=自身.适配器表.get(提供方)#可选注册
        if 注册 is None:#未注册
            return None#无
        return 注册['adapter'].图片请求定价(提供方,模型)#问适配器

    def 文件请求文本(自身,引用):#文件请求文本
        """解析某一持久文件出现处贡献给每条提供方请求的精确文本。"""
        return 文件句柄文案(引用,自身._文件读路径(引用))#句柄

    def _文件读路径(自身,引用):#文件读路径
        """经已挂载附件与文件系统提供方解析执行世界读路径。"""
        try:#附件可能抛畸形引用
            附件=自身.ctx.获取服务('attachments')#可选附件
            if 附件 is None:#无
                return None#无
            宿主路径=附件.文件宿主路径(引用) if hasattr(附件,'文件宿主路径') else None#宿主
        except Exception:#畸形引用
            return None#降级无路径
        if 宿主路径 is None:#无映射
            return None#无
        文件系统=自身.ctx.获取服务('fs')#可选 fs
        if 文件系统 is None or not hasattr(文件系统,'从宿主路径到进程路径'):#无映射面
            映射=getattr(文件系统,'processPathFromHostPath',None) if 文件系统 is not None else None#英文面
            return 映射(宿主路径) if 映射 is not None else None#映射或无
        return 文件系统.从宿主路径到进程路径(宿主路径)#中文面

    def 拆离模态(自身,模态):#拆离模态列表
        """拆离有类型的适配器拥有模态元数据。"""
        if 模态 is None:#无模态
            return None#无模态
        return list(模态)#有则复制

    def 列出模型(自身,提供方):#发现一条已注册提供方通告的模型
        """发现一条已注册提供方通告的模型。"""
        适配器=自身.取注册(提供方)['adapter']#取出适配器
        模型列表=适配器.列出模型(提供方)#列出模型已是同步，直取目录
        已见=set()#已见 id
        结果=[]#拆离结果
        for 模型 in 模型列表:#逐个模型
            描述非法='description' in 模型 and not isinstance(模型['description'],str)#描述类型错
            非法=not isinstance(模型.get('provider'),str) or 模型.get('provider')!=提供方 or not isinstance(模型.get('id'),str) or len(模型.get('id') or '')==0 or not isinstance(模型.get('name'),str) or len(模型.get('name') or '')==0 or 描述非法 or 模型.get('id') in 已见#元数据非法或重复
            if 非法:#目录非法
                raise 语言模型错误('adapter returned invalid or duplicate model metadata for provider "'+提供方+'"','INVALID_CATALOG')#目录非法
            已见.add(模型['id'])#记下已见
            输入模态=自身.拆离模态(模型['inputModalities'] if 'inputModalities' in 模型 else None)#拆离输入模态
            信息={'provider':模型['provider'],'id':模型['id'],'name':模型['name']}#拆离模型信息
            if 'description' in 模型:#有描述
                信息['description']=模型['description']#有描述才带上
            if 输入模态 is not None:#有模态
                信息['inputModalities']=输入模态#有模态才带上
            结果.append(信息)#记下
        return 结果#按适配器偏好顺序

    def 解析模型信息(自身,提供方,模型,信号=None):#解析精确模型信息
        """从拥有一条精确路由的适配器解析并校验全部元数据。"""
        return 自身.按注册解析模型信息(自身.取注册(提供方),模型,信号)#绑到当前注册

    def 按注册解析模型信息(自身,注册,模型,信号=None):#按已捕获注册解析模型信息
        """按已捕获注册解析模型信息。"""
        提供方=注册['provider']['id']#注册的提供方 id
        已解析=注册['adapter'].解析模型(提供方,模型,信号)#解析模型已是同步，直取元数据
        描述非法='description' in 已解析 and not isinstance(已解析['description'],str)#描述类型错
        if not isinstance(已解析.get('provider'),str) or 已解析.get('provider')!=提供方 or not isinstance(已解析.get('id'),str) or 已解析.get('id')!=模型 or not isinstance(已解析.get('name'),str) or len(已解析.get('name') or '')==0 or 描述非法:#身份非法
            raise 语言模型错误('adapter returned invalid exact model metadata for provider "'+提供方+'" model "'+模型+'"','INVALID_MODEL_INFO')#精确模型元数据非法
        上下文=已解析.get('context') if 'context' in 已解析 else None#可选上下文
        if 上下文 is not None:#有上下文
            窗口=上下文.get('contextWindow')#窗口
            是整数=isinstance(窗口,(int,float)) and not isinstance(窗口,bool) and math.isfinite(窗口) and 窗口==int(窗口)#整数
            if not 是整数 or 窗口<=0:#窗口非法
                raise 语言模型错误('adapter returned invalid context metadata for provider "'+提供方+'" model "'+模型+'"','INVALID_MODEL_CONTEXT')#上下文元数据非法
        输入模态=自身.拆离模态(已解析['inputModalities'] if 'inputModalities' in 已解析 else None)#拆离输入模态
        系统提示词更新=已解析.get('systemPromptUpdate') if 'systemPromptUpdate' in 已解析 else None#可选系统提示词更新
        if 系统提示词更新 is not None and 系统提示词更新!='in-history':#非法模式
            raise 语言模型错误('adapter returned invalid system prompt update mode for provider "'+提供方+'" model "'+模型+'"','INVALID_MODEL_INFO')#系统提示词更新非法
        默认上限=已解析.get('defaultMaxTokens') if 'defaultMaxTokens' in 已解析 else None#可选默认最大 token
        if 默认上限 is not None:#有默认上限
            是安全整数=isinstance(默认上限,(int,float)) and not isinstance(默认上限,bool) and math.isfinite(默认上限) and 默认上限==int(默认上限) and abs(默认上限)<=9007199254740991#正安全整数
            if not 是安全整数 or 默认上限<=0:#上限非法
                raise 语言模型错误('adapter returned invalid default maxTokens for provider "'+提供方+'" model "'+模型+'"','INVALID_MODEL_MAX_TOKENS')#默认 maxTokens 非法
        信息={'provider':提供方,'id':模型,'name':已解析['name']}#基础已解析信息
        if 'description' in 已解析:#有描述
            信息['description']=已解析['description']#有描述才带上
        if 输入模态 is not None:#有模态
            信息['inputModalities']=输入模态#有模态才带上
        if 上下文 is not None:#有窗口
            信息['context']={'contextWindow':上下文['contextWindow']}#有窗口才带上
        if 默认上限 is not None:#有上限
            信息['defaultMaxTokens']=默认上限#有上限才带上
        if 系统提示词更新 is not None:#有更新模式
            信息['systemPromptUpdate']=系统提示词更新#有更新模式才带上
        推理=已解析.get('reasoning') if 'reasoning' in 已解析 else None#可选推理元数据
        if 推理 is None:#没有推理
            return 信息#没有推理则到此
        if len(推理['efforts'])==0:#力度列表空
            raise 语言模型错误('adapter returned invalid reasoning metadata for provider "'+提供方+'" model "'+模型+'"','INVALID_MODEL_REASONING')#推理元数据非法
        已见=set()#已见力度 id
        力度列表=[]#拆离力度
        for 力度 in 推理['efforts']:#逐档力度
            力度描述非法='description' in 力度 and not isinstance(力度['description'],str)#描述类型错
            非法=not isinstance(力度.get('id'),str) or len(力度.get('id') or '')==0 or not isinstance(力度.get('name'),str) or len(力度.get('name') or '')==0 or 力度描述非法 or 力度.get('id') in 已见#力度元数据非法或重复
            if 非法:#力度非法
                raise 语言模型错误('adapter returned invalid or duplicate reasoning effort metadata for provider "'+提供方+'" model "'+模型+'"','INVALID_MODEL_REASONING')#力度元数据非法
            已见.add(力度['id'])#记下已见
            条目={'id':力度['id'],'name':力度['name']}#拆离力度
            if 'description' in 力度:#有描述
                条目['description']=力度['description']#有描述才带上
            力度列表.append(条目)#记下
        if 'defaultEffort' in 推理 and 推理['defaultEffort'] not in 已见:#未知默认力度
            raise 语言模型错误('adapter returned an unknown default reasoning effort for provider "'+提供方+'" model "'+模型+'"','INVALID_MODEL_REASONING')#未知默认力度
        信息['reasoning']={'efforts':力度列表}#推理元数据
        if 'defaultEffort' in 推理:#有默认
            信息['reasoning']['defaultEffort']=推理['defaultEffort']#有默认才带上
        return 信息#带上推理

    def 解析调用配置(自身,配置,信号=None):#校验并物化调用配置
        """对照精确模型能力校验一次对话调用配置，并物化适配器配置的默认值。"""
        return 自身.按注册解析调用(自身.取注册(配置['provider']),配置,信号)['config']#只返回配置

    def 按注册解析调用(自身,注册,配置,信号=None):#按已捕获注册解析调用
        """按已捕获注册解析调用。"""
        信息=自身.按注册解析模型信息(注册,配置['model'],信号)#精确模型信息
        if 'maxTokens' not in 配置 and 'defaultMaxTokens' in 信息:#物化默认上限
            已默认=dict(配置)#物化默认上限
            已默认['maxTokens']=信息['defaultMaxTokens']#写入上限
        else:#保持原样
            已默认=配置#保持原样
        推理=信息.get('reasoning') if 'reasoning' in 信息 else None#可选推理能力
        请求力度=已默认.get('reasoningEffort') if 'reasoningEffort' in 已默认 else None#调用方请求的力度
        生效配置=已默认#当前生效配置
        if 推理 is None:#不支持推理
            if 请求力度 is not None:#却请求了力度
                raise 语言模型错误('provider "'+配置['provider']+'" model "'+配置['model']+'" does not support reasoning effort "'+str(请求力度)+'"','UNSUPPORTED_REASONING_EFFORT')#不支持的推理力度
        else:#支持推理
            生效=请求力度 if 请求力度 is not None else 推理.get('defaultEffort')#请求或默认
            if 生效 is not None:#有生效力度
                命中=False#是否在能力列表
                for 力度 in 推理['efforts']:#查能力列表
                    if 力度['id']==生效:#命中
                        命中=True#命中
                        break#找到即停
                if not 命中:#不支持
                    raise 语言模型错误('provider "'+配置['provider']+'" model "'+配置['model']+'" does not support reasoning effort "'+str(生效)+'"','UNSUPPORTED_REASONING_EFFORT')#不支持的推理力度
                if 请求力度!=生效:#物化默认力度
                    生效配置=dict(已默认)#物化默认力度
                    生效配置['reasoningEffort']=生效#写入力度
        结果={'config':生效配置}#已解析结果
        if 'context' in 信息:#有上下文
            结果['context']=信息['context']#有上下文才带上
        结果['modelInfo']=信息#带上已解析模型信息
        return 结果#返回

    def 准备调用(自身,配置,信号=None):#解析一次调用并返回一次性句柄
        """在其当前适配器注册下解析一次调用，返回一次性句柄。"""
        注册=自身.取注册(配置['provider'])#捕获当前注册
        已解析=自身.按注册解析调用(注册,配置,信号)#解析配置
        已解析配置=深冻结(结构化克隆(已解析['config']))#拆离并冻结配置
        if 'context' not in 已解析:#无上下文
            上下文=None#保持缺省
        else:#有上下文
            上下文=深冻结(结构化克隆(已解析['context']))#拆离并冻结上下文
        适配器默认={}#标记哪些字段来自适配器
        if 'reasoningEffort' not in 配置 and 'reasoningEffort' in 已解析配置:#力度被物化
            适配器默认['reasoningEffort']=True#标记力度
        if 'maxTokens' not in 配置 and 'maxTokens' in 已解析配置:#上限被物化
            适配器默认['maxTokens']=True#标记上限
        适配器默认=深冻结(适配器默认)#冻结标记
        已分派=False#是否已分派
        def 分派(选项):#一次性分派
            """一次性分派。"""
            nonlocal 已分派#改外层标记
            if 已分派:#已经分派过
                raise 语言模型错误('a prepared LLM call can only be dispatched once','INVALID_PREPARED_CALL')#不得复用
            if not 调用配置相等(选项,已解析配置):#配置已变
                raise 语言模型错误('prepared LLM call config changed before adapter dispatch','INVALID_PREPARED_CALL')#分派前配置被改
            已分派=True#记下已分派
            return 自身.带注册流出(选项,{'registration':注册,'config':已解析配置})#经捕获注册流出
        句柄={'config':已解析配置,'retryPolicy':注册['retryPolicy'],'adapterDefaults':适配器默认,'stream':分派}#一次性句柄
        if 上下文 is not None:#有上下文
            句柄['context']=上下文#有上下文才带上
        模型信息=已解析['modelInfo']#同一次解析的模型信息
        if 'inputModalities' in 模型信息:#有模态
            句柄['inputModalities']=tuple(模型信息['inputModalities'])#冻结模态
        if 'systemPromptUpdate' in 模型信息:#有更新模式
            句柄['systemPromptUpdate']=模型信息['systemPromptUpdate']#带上更新模式
        return 深冻结(句柄)#冻结一次性句柄

    def 取注册(自身,提供方):#按路由取注册
        """按路由取注册。"""
        注册=自身.适配器表.get(提供方)#查表
        if 注册 is None:#未注册
            raise 语言模型错误('no adapter registered for provider "'+提供方+'"','NO_ADAPTER')#未注册
        return 注册#已捕获注册

    def 按适配器过滤(自身,选项,适配器):#去掉他适配器拥有的回放状态
        """去掉其历史路由由另一适配器拥有的回放状态。"""
        消息列表=[]#过滤后的消息
        原消息=选项['messages']#原列表
        for 消息 in 原消息:#逐条消息
            来源=消息['source']#来源
            if 消息.get('role')!='assistant' or 来源.get('kind')!='model' or 'replayState' not in 来源:#无需过滤
                消息列表.append(消息)#无需过滤
            elif 自身.适配器表.get(来源.get('provider'),{}).get('adapter') is 适配器:#同一适配器
                消息列表.append(消息)#同一适配器实例则保留
            else:#剥掉回放状态
                新来源={'kind':'model','provider':来源['provider'],'model':来源['model']}#不含 replayState
                新消息=dict(消息)#其余字段
                新消息['source']=新来源#写回来源
                消息列表.append(冻结消息(新消息))#剥掉回放状态
        下标=0#核对身份
        全同=True#默认无改动
        while 下标<len(消息列表):#尚未比完
            if 消息列表[下标] is not 原消息[下标]:#身份变了
                全同=False#身份变了
                break#找到即停
            下标+=1#下一条
        if 全同:#没有任何改动
            return 选项#没有任何改动
        过滤后=dict(选项)#带过滤后的消息
        过滤后['messages']=消息列表#写入消息
        if 是否冻结(选项):#原请求冻结
            return 深冻结(过滤后)#原请求冻结则结果也冻结
        return 过滤后#可变请求

    def 适配器流(自身,选项,已准备=None):#最终适配器边界
        """最终适配器边界。选择、分派与迭代失败都变成终止失败块。"""
        迭代器=None#适配器迭代器
        try:#选择并打开流
            if 已准备 is None:#未经 prepare
                注册=自身.取注册(选项['provider'])#现查注册
            else:#已准备
                注册=已准备['registration']#捕获的注册
            if 已准备 is None:#现解析配置
                已解析配置=自身.按注册解析调用(注册,选项,选项.get('signal'))['config']#现解析配置
            else:#用准备好的配置
                已解析配置=已准备['config']#用准备好的配置
            if 已准备 is not None and not 调用配置相等(选项,已解析配置):#已准备但配置变了
                raise 语言模型错误('prepared LLM call config changed before adapter dispatch','INVALID_PREPARED_CALL')#分派前配置被改
            if 调用配置相等(选项,已解析配置):#配置已一致
                已解析选项=选项#原请求
            elif 是否冻结(选项):#原请求已冻结
                合并=dict(选项)#合并后冻结
                合并.update(已解析配置)#写入配置字段
                已解析选项=深冻结(合并)#冻结
            else:#合并可变请求
                已解析选项=dict(选项)#合并可变请求
                已解析选项.update(已解析配置)#写入配置字段
            适配器=注册['adapter']#目标适配器
            #文件永不原生分派：每条路由都收到句柄文本；仅文本路由再投影图片
            投影消息=已解析选项['messages']#消息
            if any(内容含文件(消息.get('content') or []) for 消息 in 投影消息):#含文件
                投影消息=投影文件为文本(投影消息,lambda 引用:自身._文件读路径(引用))#文件投影
            模型信息=None#可选已解析模型信息
            if 已准备 is not None and 'modelInfo' in 已准备:#准备携带
                模型信息=已准备['modelInfo']#模型信息
            模态=模型信息.get('inputModalities') if isinstance(模型信息,dict) else None#输入模态
            if (模态 is not None and 'image' not in 模态
                and any(内容含图片(消息.get('content') or []) for 消息 in 投影消息)):#仅文本却含图
                投影消息=投影图片为仅文本(投影消息)#仅文本投影
            if 投影消息 is 已解析选项['messages']:#无投影
                分派选项=已解析选项#原样
            elif 是否冻结(已解析选项):#冻结
                分派选项=深冻结({**已解析选项,'messages':投影消息})#冻结投影
            else:#可变
                分派选项={**已解析选项,'messages':投影消息}#可变投影
            流=适配器.流式(自身.按适配器过滤(分派选项,适配器))#流式已是同步生成器，直取
            迭代器=iter(流)#取出迭代器
        except Exception as 错误:#适配器契约未收窄抛出类型，一律收成终止失败块
            yield 适配器失败块(错误,选项.get('signal'))#变成终止失败块
            return#结束生成器
        已完成=False#迭代是否已正常结束
        try:#消费适配器迭代器
            while True:#直到 done
                try:#取下一块
                    值=next(迭代器)#适配器下一步
                    项={'done':False,'value':值}#还有值
                except StopIteration:#适配器结束
                    项={'done':True}#终止
                except Exception as 错误:#适配器契约未收窄抛出类型，一律收成终止失败块
                    已完成=True#不再交还迭代器
                    yield 适配器失败块(错误,选项.get('signal'))#变成终止失败块
                    return#结束生成器
                if 项.get('done'):#适配器结束
                    已完成=True#正常完成
                    return#结束生成器
                yield 项['value']#让出一块
        finally:#生成器被提前关掉
            if not 已完成 and 迭代器 is not None:#迭代尚未完成
                关闭=getattr(迭代器,'close',None)#可选的 close
                if 关闭 is not None:#有 close
                    关闭()#通知适配器取消

    def 流式(自身,选项):#公开流式调用
        """把一次模型调用流成原始块。"""
        return 自身.带注册流出(选项)#未经 prepare 的现查注册

    def 带注册流出(自身,选项,已准备=None):#经可选捕获注册流出
        """经可选捕获注册流出。"""
        def 内层(*位置参数):#最终适配器边界
            """最终适配器边界；忽略瀑布多余参数，对齐 JS 函数。"""
            return 自身.适配器流(选项,已准备)#适配器流
        return 自身.ctx.链式拦截(自身,'llm/stream',选项,内层)#走 llm/stream 瀑布

def 适配器失败块(错误,信号=None):#把适配器抛出转换成终止结果
    """把一次适配器抛出转换成流协议的终止结果。"""
    失败=归一化语言模型失败(错误)#归一化为失败事实
    调用方中止=已中止(信号)#调用方中止
    if 调用方中止 or ('code' in 失败 and 失败['code']=='ABORTED'):#中止
        原因={'kind':'aborted','failure':失败}#中止
    else:#错误
        原因={'kind':'error','failure':失败}#错误
    return {'type':'finish','reason':原因}#终止 finish

断言可用接口密钥=断言可用密钥#中文消费方别名（下游 llm_deepseek 等）
大模型错误=语言模型错误#中文消费方别名
大模型适配器=语言模型适配器#中文消费方别名
大模型运行时=语言模型运行时#中文消费方别名
默认=语言模型运行时#默认导出运行时
