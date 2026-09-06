"""compaction-basic 的加载时校验与路由模型政策解析。"""
import math#有限数判定
from ...模型后端.llm import 深冻结,结构化克隆#导入深冻结与拆离克隆

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

class 基础压缩错误(Exception):
    """基础压缩包的异常基类。"""

class 目标压力配置错误(基础压缩错误):
    """目标特有压力配置失败，可抑制重复警告。"""

    def __init__(自身,目标键,消息):
        """记下用作警告键的精确提供方/模型路由与可操作的配置失败细节。"""
        super().__init__(消息)#交给基类
        自身.targetKey=目标键#警告键
        自身.message=消息#诊断文案
        自身.name='TargetPressureConfigError'#错误名

def 是否有限数(值):
    """有限实数，排除布尔。"""
    if isinstance(值,bool):#布尔不是数字
        return False#排除
    if isinstance(值,(int,float)):#数字
        return math.isfinite(值)#有限
    return False#其它

def 校验非空字符串(名称,值):
    """字段须为非空字符串。"""
    if (not isinstance(值,str)) or len(值)==0:#空或非字符串
        raise 基础压缩错误(名称+' must be a non-empty string')#须为非空字符串

def 校验正整数(名称,值):
    """字段须为正整数。"""
    是整数=(not isinstance(值,bool)) and (isinstance(值,int) or (isinstance(值,float) and 值.is_integer()))#排除布尔
    if (not 是整数) or 值<=0:#非正整数
        raise 基础压缩错误(名称+' ('+str(值)+') must be a positive integer')#须为正整数

def 校验非负整数(名称,值):
    """字段须为非负整数。"""
    是整数=(not isinstance(值,bool)) and (isinstance(值,int) or (isinstance(值,float) and 值.is_integer()))#排除布尔
    if (not 是整数) or 值<0:#负或非整数
        raise 基础压缩错误(名称+' ('+str(值)+') must be a non-negative integer')#须为非负整数

def 校验比例(名称,值):
    """字段须为 (0, 1] 内的有限数。"""
    if (not 是否有限数(值)) or 值<=0 or 值>1:#越界或非有限
        raise 基础压缩错误(名称+' ('+str(值)+') must be a number in (0, 1]')#须在 (0,1]

def 校验键集(配置,键集合,名称):
    """拒绝未知键。"""
    for 键 in 配置:#枚举自有键
        if 键 not in 键集合:#未知键
            raise 基础压缩错误(名称+': unknown key "'+str(键)+'"')#未知键失败

def 校验摘要成对(配置,名称):
    """摘要提供方与模型须同为空或同为非空。"""
    提供方=配置['summarizationProvider'] if 'summarizationProvider' in 配置 else None#摘要提供方
    模型=配置['summarizationModel'] if 'summarizationModel' in 配置 else None#摘要模型
    if 提供方 is not None and (not isinstance(提供方,str)):#类型不对
        raise 基础压缩错误(名称+'.summarizationProvider must be a string')#须为字符串
    if 模型 is not None and (not isinstance(模型,str)):#类型不对
        raise 基础压缩错误(名称+'.summarizationModel must be a string')#须为字符串
    if 提供方 is None and 模型 is None:#都省略则继承
        return#放过
    if 提供方 is None or 模型 is None or ((len(提供方)==0)!=(len(模型)==0)):#只写一边或一边空一边非空
        raise 基础压缩错误(#不成对
            名称+': summarizationProvider and summarizationModel must be set together '
            +'as an empty or non-empty pair'#须同为空或同为非空
        )#抛出结束

def 校验政策(配置,名称):
    """校验政策字段类型与互斥保留。"""
    阈值比例=配置['thresholdRatio'] if 'thresholdRatio' in 配置 else None#阈值比例
    保留比例=配置['retainRatio'] if 'retainRatio' in 配置 else None#保留比例
    保留令牌=配置['retainTokens'] if 'retainTokens' in 配置 else None#绝对保留
    最大令牌=配置['maxTokens'] if 'maxTokens' in 配置 else None#生成上限
    压缩重试=配置['compactionRetries'] if 'compactionRetries' in 配置 else None#压缩重试
    溢出重试=配置['maxOverflowRetries'] if 'maxOverflowRetries' in 配置 else None#溢出重试
    if 阈值比例 is not None:#写了阈值
        校验比例(名称+'.thresholdRatio',阈值比例)#校验阈值比例
    if 保留比例 is not None:#写了保留比例
        校验比例(名称+'.retainRatio',保留比例)#校验保留比例
    if 保留令牌 is not None:#写了绝对保留
        校验非负整数(名称+'.retainTokens',保留令牌)#校验绝对保留
    if 保留比例 is not None and 保留令牌 is not None:#两种保留同时出现
        raise 基础压缩错误(名称+': retainRatio and retainTokens are mutually exclusive')#互斥
    if 最大令牌 is not None:#写了生成上限
        校验正整数(名称+'.maxTokens',最大令牌)#校验生成上限
    if 压缩重试 is not None:#写了压缩重试
        校验非负整数(名称+'.compactionRetries',压缩重试)#须为非负整数
    if 溢出重试 is not None:#写了溢出重试
        校验非负整数(名称+'.maxOverflowRetries',溢出重试)#须为非负整数
    校验摘要成对(配置,名称)#摘要提供方与模型成对

def 校验模型政策(源,名称):
    """校验一条不受信任的精确目标覆盖。"""
    if not isinstance(源,dict):#须为对象
        raise 基础压缩错误(名称+' must be an object')#须为对象
    校验键集(源,模型政策键集合,名称)#拒绝未知键
    校验非空字符串(名称+'.provider',源['provider'] if 'provider' in 源 else None)#提供方非空
    校验非空字符串(名称+'.model',源['model'] if 'model' in 源 else None)#模型非空
    校验政策(源,名称)#校验政策字段

def 解析模型政策表(已配置):
    """校验精确目标表。"""
    if 已配置 is None:#未配置则空表
        return []#空表
    if not isinstance(已配置,list):#类型不对
        raise 基础压缩错误('BasicCompactionConfig: modelPolicies must be an array')#须为数组
    已见=set()#已见提供方\\0模型
    结果=[]#拷贝表
    for 下标,源 in enumerate(已配置):#逐条校验并拷贝
        名称='BasicCompactionConfig: modelPolicies['+str(下标)+']'#错误名前缀
        校验模型政策(源,名称)#收窄并校验
        键=str(源['provider'])+'\u0000'+str(源['model'])#去重键
        if 键 in 已见:#重复目标
            raise 基础压缩错误(#加载失败
                'BasicCompactionConfig: duplicate model policy for '
                +str(源['provider'])+'/'+str(源['model'])#重复政策
            )#抛出结束
        已见.add(键)#记下已见
        结果.append(dict(源))#浅拷贝分离
    return 结果#已解析表

def 解析保留(配置,回退):
    """恰好一种保留形态。"""
    if 'retainTokens' in 配置 and 配置['retainTokens'] is not None:#绝对优先
        return {'retainTokens':配置['retainTokens']}#按绝对 token
    if 'retainRatio' in 配置 and 配置['retainRatio'] is not None:#否则比例
        return {'retainRatio':配置['retainRatio']}#按比例
    return dict(回退)#都没写则继承

def 校验比例保留(阈值比例,保留,名称):
    """比例保留不得压过阈值。"""
    if 'retainRatio' in 保留 and 保留['retainRatio'] is not None and 保留['retainRatio']>=阈值比例:#比例保留压过阈值
        raise 基础压缩错误(#加载失败
            名称+': retainRatio ('+str(保留['retainRatio'])+') must be less than '
            +'the resolved thresholdRatio ('+str(阈值比例)+')'#比例须小于阈值
        )#抛出结束

def 解析配置(配置=None):
    """返回分离的不可变默认值与已校验精确目标覆盖。"""
    if 配置 is None:#缺省空配置
        配置={}#空配置
    校验键集(配置,基础压缩配置键集合,'BasicCompactionConfig')#拒绝未知键
    校验政策(配置,'BasicCompactionConfig')#校验政策字段
    自动=配置['auto'] if 'auto' in 配置 else None#auto 字段
    if 自动 is not None and (not isinstance(自动,bool)):#auto 类型不对
        raise 基础压缩错误('BasicCompactionConfig: auto must be a boolean')#auto 须为布尔
    阈值比例=默认阈值比例 if ('thresholdRatio' not in 配置 or 配置['thresholdRatio'] is None) else 配置['thresholdRatio']#解析阈值比例
    保留=解析保留(配置,{'retainRatio':默认保留比例})#解析保留形态
    校验比例保留(阈值比例,保留,'BasicCompactionConfig')#比例保留不得压过阈值
    模型政策列表=解析模型政策表(配置['modelPolicies'] if 'modelPolicies' in 配置 else None)#解析精确目标表
    for 下标,政策 in enumerate(模型政策列表):#逐条覆盖再校验保留
        覆盖阈值=阈值比例 if ('thresholdRatio' not in 政策 or 政策['thresholdRatio'] is None) else 政策['thresholdRatio']#覆盖或继承阈值
        校验比例保留(#覆盖后的阈值与保留
            覆盖阈值,#阈值
            解析保留(政策,保留),#覆盖或继承保留
            'BasicCompactionConfig: modelPolicies['+str(下标)+']',#带下标的错误名前缀
        )#单条保留校验结束
    提供方=配置['summarizationProvider'] if 'summarizationProvider' in 配置 else None#摘要提供方
    模型=配置['summarizationModel'] if 'summarizationModel' in 配置 else None#摘要模型
    已解析={#组装已解析配置
        'thresholdRatio':阈值比例,#阈值比例
        **保留,#保留形态
        'summarizationProvider':'' if 提供方 is None else 提供方,#摘要提供方，空则继承对话目标
        'summarizationModel':'' if 模型 is None else 模型,#摘要模型，空则继承
        'maxTokens':8192 if ('maxTokens' not in 配置 or 配置['maxTokens'] is None) else 配置['maxTokens'],#生成上限
        'compactionRetries':1 if ('compactionRetries' not in 配置 or 配置['compactionRetries'] is None) else 配置['compactionRetries'],#压缩重试
        'maxOverflowRetries':1 if ('maxOverflowRetries' not in 配置 or 配置['maxOverflowRetries'] is None) else 配置['maxOverflowRetries'],#溢出重试
        'modelPolicies':模型政策列表,#精确目标表
        'auto':True if 自动 is None else 自动,#默认自动
    }#已解析结束
    return 深冻结(结构化克隆(已解析))#冻结已解析配置

def 解析目标政策(配置,目标):
    """返回模型容量缩放之前的分离不可变政策。"""
    覆盖=None#精确匹配覆盖
    政策列表=配置['modelPolicies'] if 'modelPolicies' in 配置 and 配置['modelPolicies'] is not None else []#精确目标表
    for 政策 in 政策列表:#找精确匹配
        if 政策['provider']==目标['provider'] and 政策['model']==目标['model']:#双键全等
            覆盖=政策#命中
            break#停止
    if 'retainTokens' not in 配置 or 配置['retainTokens'] is None:#服务级按比例
        继承保留={'retainRatio':配置['retainRatio']}#按比例
    else:#服务级按绝对 token
        继承保留={'retainTokens':配置['retainTokens']}#按绝对
    源=覆盖 if 覆盖 is not None else {}#覆盖或空
    已合并={#冻结合并结果前组装
        'target':{'provider':目标['provider'],'model':目标['model']},#精确目标
        'thresholdRatio':配置['thresholdRatio'] if ('thresholdRatio' not in 源 or 源['thresholdRatio'] is None) else 源['thresholdRatio'],#覆盖或默认阈值
        **解析保留(源,继承保留),#覆盖或继承保留
        'summarizationProvider':配置['summarizationProvider'] if ('summarizationProvider' not in 源 or 源['summarizationProvider'] is None) else 源['summarizationProvider'],#摘要提供方
        'summarizationModel':配置['summarizationModel'] if ('summarizationModel' not in 源 or 源['summarizationModel'] is None) else 源['summarizationModel'],#摘要模型
        'maxTokens':配置['maxTokens'] if ('maxTokens' not in 源 or 源['maxTokens'] is None) else 源['maxTokens'],#生成上限
        'compactionRetries':配置['compactionRetries'] if ('compactionRetries' not in 源 or 源['compactionRetries'] is None) else 源['compactionRetries'],#压缩重试
        'maxOverflowRetries':配置['maxOverflowRetries'] if ('maxOverflowRetries' not in 源 or 源['maxOverflowRetries'] is None) else 源['maxOverflowRetries'],#溢出重试
    }#已合并结束
    return 深冻结(结构化克隆(已合并))#冻结合并结果

def 解析压缩规格(政策,上下文窗口):
    """返回分离的不可变压力与保留预算。"""
    目标=政策['target']#精确目标
    目标键=str(目标['provider'])+'/'+str(目标['model'])#警告键
    窗口是整数=(not isinstance(上下文窗口,bool)) and (isinstance(上下文窗口,int) or (isinstance(上下文窗口,float) and 上下文窗口.is_integer()))#排除布尔
    if (not 窗口是整数) or 上下文窗口<=0:#窗口非法
        raise 目标压力配置错误(#可抑制警告的配置错误
            目标键,#目标键
            'BasicCompactionConfig: contextWindow ('+str(上下文窗口)+') must be a positive integer',#窗口须为正整数
        )#抛出结束
    阈值令牌=int(上下文窗口*政策['thresholdRatio'])#阈值 token；对齐 Math.floor
    if 'retainTokens' not in 政策 or 政策['retainTokens'] is None:#按比例
        保留令牌=int(上下文窗口*政策['retainRatio'])#按比例取整
    else:#已是绝对预算
        保留令牌=政策['retainTokens']#绝对
    if 保留令牌>=阈值令牌:#保留不小于阈值则永远压不住
        raise 目标压力配置错误(#可抑制警告的配置错误
            目标键,#目标键
            'BasicCompactionConfig: '+str(目标['provider'])+'/'
            +str(目标['model'])+' retainTokens '
            +'('+str(保留令牌)+') must be less than threshold tokens '+str(阈值令牌),#保留须小于阈值
        )#抛出结束
    规格={#冻结规格前组装
        'target':dict(目标),#精确目标副本
        'contextWindow':上下文窗口,#窗口
        'thresholdRatio':政策['thresholdRatio'],#阈值比例
        'thresholdTokens':阈值令牌,#阈值 token
        'retainTokens':保留令牌,#保留 token
        'summarizationProvider':政策['summarizationProvider'],#摘要提供方
        'summarizationModel':政策['summarizationModel'],#摘要模型
        'maxTokens':政策['maxTokens'],#生成上限
        'compactionRetries':政策['compactionRetries'],#压缩重试
        'maxOverflowRetries':政策['maxOverflowRetries'],#溢出重试
    }#规格结束
    return 深冻结(结构化克隆(规格))#冻结规格
