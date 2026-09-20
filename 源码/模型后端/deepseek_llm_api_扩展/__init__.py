"""DeepSeek 官方请求扩展字段注册表。"""
import copy#结构化克隆
from ...依赖 import cordis#外部依赖胶水
服务=cordis.服务#服务基类
from ..llm import 若已中止则抛出#中止原语

__all__=['扩展错误','深度seek官方请求扩展注册表','默认']#仅中文公开名

class 扩展错误(Exception):
    """DeepSeek LLM API 扩展注册与接纳失败。"""

def 深冻结json(值):
    """递归复制 JSON 形值；dict 与 list 拆离，标量原样。"""
    if isinstance(值,dict):#对象
        return {键:深冻结json(子) for 键,子 in 值.items()}#递归
    if isinstance(值,list):#数组
        return [深冻结json(子) for 子 in 值]#递归
    return 值#标量

class 深度seek官方请求扩展注册表(服务):#扩展字段注册表
    """每个顶层字段只允许一个提供方。"""
    def __init__(自身,上下文):
        """以 deepseekLlmApiExtensions 名安装服务。"""
        super().__init__(上下文,'deepseekLlmApiExtensions')#服务名
        自身.提供方表={}#字段名→提供方

    def 注册(自身,字段,提供方):
        """副作用作用域内占字段；重复字段抛错。"""
        字段名=str(字段)#字段键
        if 字段名.strip()!=字段名 or 字段名=='':#空白或首尾空白
            raise 扩展错误('deepseek-llm-api-extensions: field must be a non-blank trimmed string')#拒绝
        表=自身.提供方表#闭包表
        擦除=提供方#类型擦除
        def 装寿命():
            """占字段并在拆除时释放。"""
            if 字段名 in 表:#重复
                raise 扩展错误('deepseek-llm-api-extensions: field '+repr(字段名)+' is already registered')#冲突
            表[字段名]=擦除#登记
            def 拆():
                """拆除时释放字段。"""
                表.pop(字段名,None)#释放
            return 拆#插件拆除时释放字段占用
        拆除=自身.ctx.副作用(装寿命,'deepseekLlmApiExtensions.register('+repr(字段名)+')')#登记到副作用寿命
        return 拆除#返回拆除回调

    def 准备(自身,请求):
        """准备失败在 HTTP 前拒绝；字段值深拷贝并冻结。请求为 dict。"""
        信号=请求['signal'] if 'signal' in 请求 else None#取消信号
        若已中止则抛出(信号)#已取消则抛中止
        条目列表=list(自身.提供方表.items())#快照
        已准备=[]#并行准备结果
        for 字段,提供方 in 条目列表:#逐个准备
            结果=提供方.prepare(请求)#提供方 prepare 已是同步
            已准备.append((字段,结果))#记下
        字段表={}#输出字段
        回调列表=[]#accept 回调
        for 字段,结果 in 已准备:#按登记顺序组装字段与回调
            if 结果 is None:#本请求无值
                continue#跳过
            字段表[字段]=深冻结json(copy.deepcopy(结果['value']))#克隆
            if 'accept' in 结果:#有回调
                接受=结果['accept']#可选 accept
                if 接受 is not None:#有回调
                    回调列表.append(接受)#延后到 joint accept
        已接纳=False#惰性 joint accept
        def 接纳():
            """全部 accept 成功后才算完成。"""
            nonlocal 已接纳#闭包状态
            if 已接纳:#已跑过
                return None#复用成功
            错误列表=[]#本批 accept 失败
            for 回调 in 回调列表:#逐个
                try:#执行
                    回调()#accept 已是同步
                except Exception as 错误:#accept 回调契约未收窄抛出类型
                    错误列表.append(错误)#记下失败
            if len(错误列表)==1:#单个失败
                raise 错误列表[0]#原样抛
            if len(错误列表)>1:#多个失败
                raise 扩展错误('DeepSeek LLM API extension acceptance failed: '+'; '.join(str(错误) for 错误 in 错误列表))#聚合
            已接纳=True#成功
            return None#完成
        return {'fields':字段表,'accept':接纳}#准备结果

默认=深度seek官方请求扩展注册表
default=深度seek官方请求扩展注册表#框架槽
