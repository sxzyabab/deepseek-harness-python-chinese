"""compaction-basic 的加载时校验与路由模型政策解析。"""
import math#有限数判定
from llm import 深冻结,结构化克隆#导入深冻结与拆离克隆
from .类型 import (#仅作词汇对照；运行时用字典
    基础压缩配置字段,#顶层允许键参照
)#本包类型词汇

默认阈值比例=0.8#每个路由模型的默认请求压力比例
默认保留比例=0.16#每个路由模型的默认逐字尾部比例

政策配置键=(#顶层默认值与精确目标覆盖共用的字段
    'thresholdRatio',#压力阈值比例
    'retainRatio',#保留比例
    'retainTokens',#绝对保留 token
    'summarizationProvider',#摘要提供方
    'summarizationModel',#摘要模型
    'maxTokens',#生成上限
    'compactionRetries',#压缩重试
    'maxOverflowRetries',#溢出重试
)#政策配置键结束

基础压缩配置键集合=frozenset(政策配置键+('modelPolicies','auto'))#完整的公开顶层配置键集
模型政策键集合=frozenset(('provider','model')+政策配置键)#完整的精确目标覆盖键集

class 目标压力配置错误(Exception):#目标特有压力配置失败，可抑制重复警告
    """目标特有压力配置失败，可抑制重复警告。"""
    def __init__(自身,目标键,消息):#构造目标键错误
        """记下用作警告键的精确提供方/模型路由与可操作的配置失败细节。"""
        super().__init__(消息)#交给 Exception
        自身.targetKey=目标键#警告键
        自身.message=消息#诊断文案
        自身.name='TargetPressureConfigError'#错误名

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 枚举键(配置):#对齐 Object.keys
    """枚举配置自有键；映射用键，其它对象用可公开属性名。"""
    if isinstance(配置,dict):#映射
        return list(配置.keys())#自有键
    return [名 for 名 in dir(配置) if not 名.startswith('_')]#粗略公开属性

def 是否未知记录(值):#是否普通对象
    """非 null、非数组的对象记录。"""
    return isinstance(值,dict)#Python 侧以 dict 收窄

def 是否整数(值):#对齐 JS Number.isInteger，排除布尔
    """对齐 JS Number.isInteger，排除布尔。"""
    if isinstance(值,bool):#布尔不是数字
        return False#布尔不是整数
    if isinstance(值,int):#整数
        return True#是整数
    if isinstance(值,float) and 值.is_integer():#整值浮点
        return True#是整数
    return False#其它类型

def 是否有限数(值):#对齐 Number.isFinite
    """有限实数，排除布尔。"""
    if isinstance(值,bool):#布尔不是数字
        return False#排除
    if isinstance(值,(int,float)):#数字
        return math.isfinite(值)#有限
    return False#其它

def 断言非空字符串(名称,值):#断言非空字符串
    """字段须为非空字符串。"""
    if (not isinstance(值,str)) or len(值)==0:#空或非字符串
        raise Exception(名称+' must be a non-empty string')#须为非空字符串

def 断言正整数(名称,值):#断言正整数
    """字段须为正整数。"""
    if (not 是否整数(值)) or 值<=0:#非正整数
        raise Exception(名称+' ('+str(值)+') must be a positive integer')#须为正整数

def 断言非负整数(名称,值):#断言非负整数
    """字段须为非负整数。"""
    if (not 是否整数(值)) or 值<0:#负或非整数
        raise Exception(名称+' ('+str(值)+') must be a non-negative integer')#须为非负整数

def 断言比例(名称,值):#断言 (0,1] 比例
    """字段须为 (0, 1] 内的有限数。"""
    if (not 是否有限数(值)) or 值<=0 or 值>1:#越界或非有限
        raise Exception(名称+' ('+str(值)+') must be a number in (0, 1]')#须在 (0,1]

def 校验键集(配置,键集合,名称):#在默认值掩盖之前拒绝过时或拼错的键
    """拒绝未知键。"""
    for 键 in 枚举键(配置):#枚举自有键
        if 键 not in 键集合:#未知键
            raise Exception(名称+': unknown key "'+str(键)+'"')#未知键失败

def 校验摘要成对(配置,名称):#要求同一作用域省略、清空或成对替换摘要目标
    """摘要提供方与模型须同为空或同为非空。"""
    提供方=取字段(配置,'summarizationProvider')#摘要提供方
    模型=取字段(配置,'summarizationModel')#摘要模型
    if 提供方 is not None and (not isinstance(提供方,str)):#类型不对
        raise Exception(名称+'.summarizationProvider must be a string')#须为字符串
    if 模型 is not None and (not isinstance(模型,str)):#类型不对
        raise Exception(名称+'.summarizationModel must be a string')#须为字符串
    if 提供方 is None and 模型 is None:#都省略则继承
        return#放过
    if 提供方 is None or 模型 is None or ((len(提供方)==0)!=(len(模型)==0)):#只写一边或一边空一边非空
        raise Exception(#不成对
            名称+': summarizationProvider and summarizationModel must be set together '
            +'as an empty or non-empty pair'#须同为空或同为非空
        )#抛出结束

def 校验政策(配置,名称):#校验默认值与精确目标部分覆盖共用的字段
    """校验政策字段类型与互斥保留。"""
    阈值比例=取字段(配置,'thresholdRatio')#阈值比例
    保留比例=取字段(配置,'retainRatio')#保留比例
    保留令牌=取字段(配置,'retainTokens')#绝对保留
    最大令牌=取字段(配置,'maxTokens')#生成上限
    压缩重试=取字段(配置,'compactionRetries')#压缩重试
    溢出重试=取字段(配置,'maxOverflowRetries')#溢出重试
    if 阈值比例 is not None:#写了阈值
        断言比例(名称+'.thresholdRatio',阈值比例)#校验阈值比例
    if 保留比例 is not None:#写了保留比例
        断言比例(名称+'.retainRatio',保留比例)#校验保留比例
    if 保留令牌 is not None:#写了绝对保留
        断言非负整数(名称+'.retainTokens',保留令牌)#校验绝对保留
    if 保留比例 is not None and 保留令牌 is not None:#两种保留同时出现
        raise Exception(名称+': retainRatio and retainTokens are mutually exclusive')#互斥
    if 最大令牌 is not None:#写了生成上限
        断言正整数(名称+'.maxTokens',最大令牌)#校验生成上限
    if 压缩重试 is not None:#写了压缩重试
        断言非负整数(名称+'.compactionRetries',压缩重试)#须为非负整数
    if 溢出重试 is not None:#写了溢出重试
        断言非负整数(名称+'.maxOverflowRetries',溢出重试)#须为非负整数
    校验摘要成对(配置,名称)#摘要提供方与模型成对

def 断言模型政策(源,名称):#断言是合法覆盖
    """校验一条不受信任的精确目标覆盖。"""
    if not 是否未知记录(源):#须为对象
        raise Exception(名称+' must be an object')#须为对象
    校验键集(源,模型政策键集合,名称)#拒绝未知键
    断言非空字符串(名称+'.provider',取字段(源,'provider'))#提供方非空
    断言非空字符串(名称+'.model',取字段(源,'model'))#模型非空
    校验政策(源,名称)#校验政策字段

def 解析模型政策表(已配置):#解析、分离并拒绝重复的精确目标政策
    """校验精确目标表。"""
    if 已配置 is None:#未配置则空表
        return []#空表
    if not isinstance(已配置,list):#类型不对
        raise Exception('BasicCompactionConfig: modelPolicies must be an array')#须为数组
    已见=set()#已见提供方\\0模型
    结果=[]#拷贝表
    for 下标,源 in enumerate(已配置):#逐条校验并拷贝
        名称='BasicCompactionConfig: modelPolicies['+str(下标)+']'#错误名前缀
        断言模型政策(源,名称)#收窄并校验
        键=str(取字段(源,'provider'))+'\u0000'+str(取字段(源,'model'))#去重键
        if 键 in 已见:#重复目标
            raise Exception(#加载失败
                'BasicCompactionConfig: duplicate model policy for '
                +str(取字段(源,'provider'))+'/'+str(取字段(源,'model'))#重复政策
            )#抛出结束
        已见.add(键)#记下已见
        结果.append(dict(源))#浅拷贝分离
    return 结果#已解析表

def 解析保留(配置,回退):#选择显式保留形态，或继承已解析回退
    """恰好一种保留形态。"""
    if 取字段(配置,'retainTokens') is not None:#绝对优先
        return {'retainTokens':取字段(配置,'retainTokens')}#按绝对 token
    if 取字段(配置,'retainRatio') is not None:#否则比例
        return {'retainRatio':取字段(配置,'retainRatio')}#按比例
    return dict(回退)#都没写则继承

def 校验比例保留(阈值比例,保留,名称):#在插件加载时拒绝与容量无关的保留冲突
    """比例保留不得压过阈值。"""
    if 取字段(保留,'retainRatio') is not None and 取字段(保留,'retainRatio')>=阈值比例:#比例保留压过阈值
        raise Exception(#加载失败
            名称+': retainRatio ('+str(取字段(保留,'retainRatio'))+') must be less than '
            +'the resolved thresholdRatio ('+str(阈值比例)+')'#比例须小于阈值
        )#抛出结束

def 解析配置(配置=None):#解析并校验服务默认值以及精确目标的部分覆盖
    """返回分离的不可变默认值与已校验精确目标覆盖。"""
    if 配置 is None:#缺省空配置
        配置={}#空配置
    校验键集(配置,基础压缩配置键集合,'BasicCompactionConfig')#拒绝未知键
    校验政策(配置,'BasicCompactionConfig')#校验政策字段
    自动=取字段(配置,'auto')#auto 字段
    if 自动 is not None and (not isinstance(自动,bool)):#auto 类型不对
        raise Exception('BasicCompactionConfig: auto must be a boolean')#auto 须为布尔
    阈值比例=默认阈值比例 if 取字段(配置,'thresholdRatio') is None else 取字段(配置,'thresholdRatio')#解析阈值比例
    保留=解析保留(配置,{'retainRatio':默认保留比例})#解析保留形态
    校验比例保留(阈值比例,保留,'BasicCompactionConfig')#比例保留不得压过阈值
    模型政策们=解析模型政策表(取字段(配置,'modelPolicies'))#解析精确目标表
    for 下标,政策 in enumerate(模型政策们):#逐条覆盖再校验保留
        覆盖阈值=阈值比例 if 取字段(政策,'thresholdRatio') is None else 取字段(政策,'thresholdRatio')#覆盖或继承阈值
        校验比例保留(#覆盖后的阈值与保留
            覆盖阈值,#阈值
            解析保留(政策,保留),#覆盖或继承保留
            'BasicCompactionConfig: modelPolicies['+str(下标)+']',#带下标的错误名前缀
        )#单条保留校验结束
    已解析={#组装已解析配置
        'thresholdRatio':阈值比例,#阈值比例
        **保留,#保留形态
        'summarizationProvider':'' if 取字段(配置,'summarizationProvider') is None else 取字段(配置,'summarizationProvider'),#摘要提供方，空则继承对话目标
        'summarizationModel':'' if 取字段(配置,'summarizationModel') is None else 取字段(配置,'summarizationModel'),#摘要模型，空则继承
        'maxTokens':8192 if 取字段(配置,'maxTokens') is None else 取字段(配置,'maxTokens'),#生成上限
        'compactionRetries':1 if 取字段(配置,'compactionRetries') is None else 取字段(配置,'compactionRetries'),#压缩重试
        'maxOverflowRetries':1 if 取字段(配置,'maxOverflowRetries') is None else 取字段(配置,'maxOverflowRetries'),#溢出重试
        'modelPolicies':模型政策们,#精确目标表
        'auto':True if 自动 is None else 自动,#默认自动
    }#已解析结束
    return 深冻结(结构化克隆(已解析))#冻结已解析配置

def 解析目标政策(配置,目标):#把精确提供方/模型覆盖合并到已校验默认政策上
    """返回模型容量缩放之前的分离不可变政策。"""
    覆盖=None#精确匹配覆盖
    for 政策 in 取字段(配置,'modelPolicies') or []:#找精确匹配
        if 取字段(政策,'provider')==取字段(目标,'provider') and 取字段(政策,'model')==取字段(目标,'model'):#双键全等
            覆盖=政策#命中
            break#停止
    if 取字段(配置,'retainTokens') is None:#服务级按比例
        继承保留={'retainRatio':取字段(配置,'retainRatio')}#按比例
    else:#服务级按绝对 token
        继承保留={'retainTokens':取字段(配置,'retainTokens')}#按绝对
    源=覆盖 if 覆盖 is not None else {}#覆盖或空
    已合并={#冻结合并结果前组装
        'target':{'provider':取字段(目标,'provider'),'model':取字段(目标,'model')},#精确目标
        'thresholdRatio':取字段(配置,'thresholdRatio') if 取字段(源,'thresholdRatio') is None else 取字段(源,'thresholdRatio'),#覆盖或默认阈值
        **解析保留(源,继承保留),#覆盖或继承保留
        'summarizationProvider':取字段(配置,'summarizationProvider') if 取字段(源,'summarizationProvider') is None else 取字段(源,'summarizationProvider'),#摘要提供方
        'summarizationModel':取字段(配置,'summarizationModel') if 取字段(源,'summarizationModel') is None else 取字段(源,'summarizationModel'),#摘要模型
        'maxTokens':取字段(配置,'maxTokens') if 取字段(源,'maxTokens') is None else 取字段(源,'maxTokens'),#生成上限
        'compactionRetries':取字段(配置,'compactionRetries') if 取字段(源,'compactionRetries') is None else 取字段(源,'compactionRetries'),#压缩重试
        'maxOverflowRetries':取字段(配置,'maxOverflowRetries') if 取字段(源,'maxOverflowRetries') is None else 取字段(源,'maxOverflowRetries'),#溢出重试
    }#已合并结束
    return 深冻结(结构化克隆(已合并))#冻结合并结果

def 解析压缩规格(政策,上下文窗口):#把一条路由政策按模型容量缩成具体 token 预算
    """返回分离的不可变压力与保留预算。"""
    目标键=str(取字段(取字段(政策,'target'),'provider'))+'/'+str(取字段(取字段(政策,'target'),'model'))#警告键
    if (not 是否整数(上下文窗口)) or 上下文窗口<=0:#窗口非法
        raise 目标压力配置错误(#可抑制警告的配置错误
            目标键,#目标键
            'BasicCompactionConfig: contextWindow ('+str(上下文窗口)+') must be a positive integer',#窗口须为正整数
        )#抛出结束
    阈值令牌=int(上下文窗口*取字段(政策,'thresholdRatio'))#阈值 token；对齐 Math.floor
    if 取字段(政策,'retainTokens') is None:#按比例
        保留令牌=int(上下文窗口*取字段(政策,'retainRatio'))#按比例取整
    else:#已是绝对预算
        保留令牌=取字段(政策,'retainTokens')#绝对
    if 保留令牌>=阈值令牌:#保留不小于阈值则永远压不住
        raise 目标压力配置错误(#可抑制警告的配置错误
            目标键,#目标键
            'BasicCompactionConfig: '+str(取字段(取字段(政策,'target'),'provider'))+'/'
            +str(取字段(取字段(政策,'target'),'model'))+' retainTokens '
            +'('+str(保留令牌)+') must be less than threshold tokens '+str(阈值令牌),#保留须小于阈值
        )#抛出结束
    规格={#冻结规格前组装
        'target':dict(取字段(政策,'target')),#精确目标副本
        'contextWindow':上下文窗口,#窗口
        'thresholdRatio':取字段(政策,'thresholdRatio'),#阈值比例
        'thresholdTokens':阈值令牌,#阈值 token
        'retainTokens':保留令牌,#保留 token
        'summarizationProvider':取字段(政策,'summarizationProvider'),#摘要提供方
        'summarizationModel':取字段(政策,'summarizationModel'),#摘要模型
        'maxTokens':取字段(政策,'maxTokens'),#生成上限
        'compactionRetries':取字段(政策,'compactionRetries'),#压缩重试
        'maxOverflowRetries':取字段(政策,'maxOverflowRetries'),#溢出重试
    }#规格结束
    return 深冻结(结构化克隆(规格))#冻结规格
