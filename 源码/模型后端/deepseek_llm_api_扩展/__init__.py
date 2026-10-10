'DeepSeek 官方请求扩展字段注册表'
import copy,json#结构化克隆与字段名
from ...依赖.cordis.服务 import 服务#服务基类
from ..llm import 已中止,若已中止则抛出#中止原语
from ...依赖.工具 import 聚合错误#多个接纳失败

__all__=['扩展错误','深度seek官方请求扩展注册表','默认']#仅中文公开名

from .异常 import 扩展错误#扩展注册与接纳失败
from . import (
    类型,
)

def 深冻结json(值):
    '递归复制 JSON 形值；dict 与 list 拆离，标量原样'
    if isinstance(值,dict):#对象
        return {键:深冻结json(子) for 键,子 in 值.items()}#递归
    if isinstance(值,list):#数组
        return [深冻结json(子) for 子 in 值]#递归
    return 值#标量

class 深度seek官方请求扩展注册表(服务):#扩展字段注册表
    '每个顶层字段只允许一个提供方'
    def __init__(自身,上下文):
        '以 deepseekLlmApiExtensions 名安装服务'
        super().__init__(上下文,'deepseekLlmApiExtensions')#服务名
        自身.提供方表={}#字段名→提供方
        自身.已警告字段=set()#准备失败已记过日志的字段

    def 注册(自身,字段,提供方):
        '副作用作用域内占字段；重复字段抛错'
        字段名=str(字段)#字段键
        if 字段名.strip()!=字段名 or 字段名=='':#空白或首尾空白
            raise 扩展错误('deepseek-llm-api-extensions: field must be a non-blank trimmed string')#拒绝
        表=自身.提供方表#闭包表
        擦除=提供方#类型擦除
        def 装寿命():
            '占字段并在拆除时释放'
            if 字段名 in 表:#重复
                raise 扩展错误('deepseek-llm-api-extensions: field '+repr(字段名)+' is already registered')#冲突
            表[字段名]=擦除#登记
            def 拆():
                '拆除时释放字段'
                表.pop(字段名,None)#释放
            return 拆#插件拆除时释放字段占用
        拆除=自身.ctx.副作用(装寿命,'deepseekLlmApiExtensions.register('+repr(字段名)+')')#登记到副作用寿命
        return 拆除#返回拆除回调

    def 准备(自身,请求):
        '单个提供方准备失败则省略该字段；只有取消会拒绝整次准备。请求为 dict'
        信号=请求['signal'] if 'signal' in 请求 else None#取消信号
        若已中止则抛出(信号)#已取消则抛中止
        条目列表=list(自身.提供方表.items())#快照
        已准备=[]#按登记顺序的准备结果
        for 字段,提供方 in 条目列表:#逐个准备
            try:#提供方失败则省略
                结果=提供方.prepare(请求)#提供方 prepare 已是同步
                if 结果 is None:#本请求无值
                    已准备.append(None)#无值
                else:#有值
                    已准备.append((字段,深冻结json(copy.deepcopy(结果['value'])),结果))#克隆后记下
            except Exception as 错误:#准备失败
                if 已中止(信号):#取消不是字段失败
                    raise#交给取消
                if 字段 not in 自身.已警告字段:#每个字段只记第一次
                    自身.已警告字段.add(字段)#记下
                    自身.ctx.日志.警告('deepseek-llm-api-extensions: omitting field '+json.dumps(字段,ensure_ascii=False)+' from this request because its preparation failed: '+str(错误))#警告
                已准备.append(None)#省略
        若已中止则抛出(信号)#准备期间取消
        字段表={}#输出字段
        回调列表=[]#accept 回调
        for 项 in 已准备:#按登记顺序组装字段与回调
            if 项 is None:#省略
                continue#跳过
            字段,值,结果=项#拆开
            字段表[字段]=值#克隆值
            if 'accept' in 结果 and 结果['accept'] is not None:#有回调
                回调列表.append(结果['accept'])#延后到 joint accept
        接纳状态={'已跑':False,'错误':None}#失败也复用同一次结果
        def 接纳():
            '全部回调都跑完再报告失败；重复调用复用第一次的结果'
            if 接纳状态['已跑']:#已经跑过
                if 接纳状态['错误'] is not None:#上次失败
                    raise 接纳状态['错误']#复用失败
                return None#复用成功
            接纳状态['已跑']=True#先记下，失败也复用
            错误列表=[]#本批 accept 失败
            for 回调 in 回调列表:#逐个
                try:#执行
                    回调()#accept 已是同步
                except Exception as 错误:#accept 回调契约未收窄抛出类型
                    错误列表.append(错误)#记下失败
            if len(错误列表)==1:#单个失败
                接纳状态['错误']=错误列表[0]#记下
                raise 错误列表[0]#原样抛
            if len(错误列表)>1:#多个失败
                聚合=聚合错误(错误列表,'DeepSeek LLM API extension acceptance failed')#聚合
                接纳状态['错误']=聚合#记下
                raise 聚合#抛出
            return None#完成
        return {'fields':字段表,'accept':接纳}#准备结果

默认=深度seek官方请求扩展注册表
default=深度seek官方请求扩展注册表#框架槽
