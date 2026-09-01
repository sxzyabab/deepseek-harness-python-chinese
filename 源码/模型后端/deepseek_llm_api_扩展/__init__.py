"""DeepSeek 官方请求扩展字段注册表。

对齐上游 `@deepseek-ai/dsh-deepseek-llm-api-extensions`。公开面仅中文名。
"""
import copy#结构化克隆
from ...依赖 import cordis#外部依赖胶水
服务=cordis.服务#服务基类

__all__=['深度seek官方请求扩展注册表','默认']#仅中文公开名

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 信号已中止(信号):#对齐 AbortSignal
    """信号是否已中止。"""
    if 信号 is None:#无信号
        return False#未中止
    if 取字段(信号,'aborted') is True:#英文
        return True#已中止
    if 取字段(信号,'已中止') is True:#中文
        return True#已中止
    if hasattr(信号,'throwIfAborted'):#可抛中止
        try:信号.throwIfAborted()#检查
        except Exception:return True#已中止
    return False#未中止

def 深冻结json(值):#递归冻结 JSON 形值
    """返回冻结后的副本。"""
    if isinstance(值,dict):#对象
        冻结={键:深冻结json(子) for 键,子 in 值.items()}#递归
        return type('F',(),{'__getitem__':lambda 自身,键:冻结[键],'items':lambda:冻结.items(),'__iter__':lambda:iter(冻结)})() if False else 冻结#dict
    if isinstance(值,list):#数组
        return [深冻结json(子) for 子 in 值]#递归
    return 值#标量

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待
    return 值#同步值

class 深度seek官方请求扩展注册表(服务):#扩展字段注册表
    """每个顶层字段只允许一个提供方。"""
    def __init__(自身,上下文):#构造服务
        """登记为 ctx.deepseekLlmApiExtensions。"""
        super().__init__(上下文,'deepseekLlmApiExtensions')#服务名
        自身.提供方表={}#字段名→提供方

    def 注册(自身,字段,提供方):#注册单一字段提供方
        """effect 作用域；重复字段抛错。"""
        字段名=str(字段)#字段键
        if 字段名.strip()!=字段名 or 字段名=='':#空白或首尾空白
            raise Exception('deepseek-llm-api-extensions: field must be a non-blank trimmed string')#拒绝
        表=自身.提供方表#闭包表
        擦除=提供方#类型擦除
        def 装寿命():#effect 体
            """占字段并在拆除时释放。"""
            if 字段名 in 表:#重复
                raise Exception('deepseek-llm-api-extensions: field '+repr(字段名)+' is already registered')#冲突
            表[字段名]=擦除#登记
            def 拆():表.pop(字段名,None)#释放
            return 拆#拆除器
        拆除=自身.ctx.effect(装寿命,'deepseekLlmApiExtensions.register('+repr(字段名)+')')#登记
        return 拆除#返回拆除器

    def 准备(自身,请求):#准备全部已注册字段
        """准备失败在 HTTP 前拒绝；字段值深拷贝并冻结。"""
        if 信号已中止(取字段(请求,'signal')):#已取消
            raise Exception('aborted')#中止
        条目们=list(自身.提供方表.items())#快照
        已准备=[]#并行准备结果
        for 字段,提供方 in 条目们:#逐个准备
            结果=解开(提供方.prepare(请求))#调用提供方
            已准备.append((字段,结果))#记下
        字段们={}#输出字段
        回调们=[]#accept 回调
        for 字段,结果 in 已准备:#收集
            if 结果 is None:#本请求无值
                continue#跳过
            字段们[字段]=深冻结json(copy.deepcopy(取字段(结果,'value')))#克隆并冻结
            接受=取字段(结果,'accept')#可选 accept
            if 接受 is not None:#有回调
                回调们.append(接受)#收集
        接纳承诺=None#惰性 joint accept
        def 接纳():#联合 accept
            """全部 accept 成功后才算完成。"""
            nonlocal 接纳承诺#闭包状态
            if 接纳承诺 is not None:#已跑过
                return 解开(接纳承诺)#复用
            错误们=[]#失败收集
            for 回调 in 回调们:#逐个
                try:解开(回调())#执行
                except Exception as 错误:错误们.append(错误)#收集
            if len(错误们)==1:#单个失败
                raise 错误们[0]#原样抛
            if len(错误们)>1:#多个失败
                raise Exception('DeepSeek LLM API extension acceptance failed: '+'; '.join(str(错误) for 错误 in 错误们))#聚合
            接纳承诺=已兑现(None)#成功
            return None#完成
        return {'fields':字段们,'accept':接纳}#准备结果

def 已兑现(值=None):#立刻兑现的简单结果
    """供 准备/接纳 内部使用。"""
    class 任务:#简易 thenable
        def wait(自身,超时=None):return 值#等待
        def 等待(自身,超时=None):return 值#中文别名
    return 任务()#返回

默认=深度seek官方请求扩展注册表#默认导出
default=深度seek官方请求扩展注册表#Cordis 默认导出
