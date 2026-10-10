'模组调用入参、抛出文案、JSON 与冻结'
import json,threading#编码与等待期约
from ...模型后端.llm.调用配置 import 冻结映射,冻结列表#就地冻结容器

__all__=['消息','记录','要求字符串','编码json','深冻结值','浅冻结副本','是有限数','是期约','等到期约','兑现','是结果对象']

def 消息(错误):
    '抛出值的给人看的文本：异常用它的消息，其余转成文本'
    if isinstance(错误,BaseException) and len(错误.args)>0:#有消息的异常
        return str(错误.args[0])#第一条消息
    return str(错误)#其余转文本

def 记录(输入):
    '模组调用入参当字段记录；不是对象就当空记录。列表不是字段记录'
    if isinstance(输入,dict):#普通对象
        return 输入#原记录
    return {}#空记录

def 要求字符串(值,什么):
    '要求一个字符串字段'
    if not isinstance(值,str):#不是字符串
        raise TypeError(什么+'必须是字符串')#给人看的类型错误
    return 值#原字符串

def 编码json(值):
    '按 JSON.stringify 能带走的值编码；带不走则 None'
    try:#标准编码
        return json.dumps(值,ensure_ascii=False,separators=(',',':'),allow_nan=False)#紧凑 JSON
    except (TypeError,ValueError):#函数、环、非有限数
        return None#JSON 带不走

def 是有限数(值):
    '有限的数，布尔不算'
    if isinstance(值,bool) or not isinstance(值,(int,float)):#布尔或非数
        return False#不是
    return 值==值 and 值 not in (float('inf'),float('-inf'))#有限

def 浅冻结副本(值):
    '浅拷贝后禁止改键；函数等值原样留在副本里'
    if not isinstance(值,dict):#不是对象
        return 值#原样
    副本=dict(值)#浅拷贝
    副本.__class__=冻结映射#禁止改键
    return 副本#冻结副本

def 深冻结值(值):
    '事件入参按层冻结。函数不包进冻结容器，调用仍可用'
    if not isinstance(值,(dict,list)):#叶子
        return 值#原样
    已见={}#环
    def 走(节点):
        '后序冻结这一层'
        if isinstance(节点,(冻结映射,冻结列表)):#已经冻过
            return 节点#原样
        if not isinstance(节点,(dict,list)):#叶子或函数
            return 节点#原样
        身份=id(节点)#对象身份
        if 身份 in 已见:#环
            return 已见[身份]#已在建的容器
        if isinstance(节点,dict):#对象
            结果={}#先用普通字典装满
            已见[身份]=结果#环指向这一份
            for 键,子 in 节点.items():#逐键
                结果[键]=走(子)#子层先冻结
            结果.__class__=冻结映射#本层禁止改键
            return 结果#冻结对象
        结果=[]#列表
        已见[身份]=结果#环指向这一份
        for 子 in 节点:#逐项
            结果.append(走(子))#子层先冻结
        结果.__class__=冻结列表#本层禁止改项
        return 结果#冻结列表
    return 走(值)#从根走

def 是期约(值):
    '是不是可等待的期约'
    return type(值).__name__ in ('PromiseEX','Promise')#只认期约类型

def 等到期约(期约值):
    '阻塞到期约结算。期约若要靠当前线程才能结算，这里会一直等'
    if 期约值.状态=='fulfilled':#已经兑现
        return 期约值.数据#值
    if 期约值.状态=='rejected':#已经拒绝
        错误=期约值.数据#拒绝原因
        if isinstance(错误,BaseException):#异常
            raise 错误#原样抛出
        raise RuntimeError(消息(错误))#包成运行时错误
    盒={'好':False,'值':None,'错':None}#结算盒
    门=threading.Event()#结算门
    def 成功(数据):
        '兑现'
        盒['好']=True#成功
        盒['值']=数据#值
        门.set()#开门
    def 失败(错误):
        '拒绝'
        盒['错']=错误#原因
        门.set()#开门
    期约值.然后(成功,失败)#挂上结算
    门.wait()#阻塞到结算
    if not 盒['好']:#拒绝
        错误=盒['错']#原因
        if isinstance(错误,BaseException):#异常
            raise 错误#原样抛出
        raise RuntimeError(消息(错误))#包成运行时错误
    return 盒['值']#兑现值

def 兑现(值):
    '期约就等到结算，普通值原样返回'
    if 是期约(值):#期约
        return 等到期约(值)#阻塞等待
    return 值#原样

def 是结果对象(值):
    '钩子结果必须是对象。None 对应 null，算一份答案；字符串和数字不算'
    if 值 is None:#null
        return True#空画面也是答案
    if isinstance(值,(str,bytes,bool)) or type(值) in (int,float):#标量
        return False#没有结果对象
    if callable(值) and not isinstance(值,(dict,list)):#函数
        return False#函数不是结果
    return True#对象或列表
