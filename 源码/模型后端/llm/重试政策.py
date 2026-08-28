"""提供方拥有的请求重试政策配置与解析。

对齐上游 `llm/src/retry-policy.ts`。公开面仅中文名；mode／字段键保持上游 wire。
无英文别名。
"""
import math#有限数判定
from ...依赖.schemastery import 路径上节点,字符串字段,数字字段,整数字段,列表字段,复合类型字段,常量字段#配置字段
from .错误 import 空响应码#导入空响应失败码
from .调用配置 import 深冻结#导入深冻结

__all__=(#仅中文公开名
    '默认最大重试次数','默认初始延迟毫秒','默认最大延迟毫秒','默认抖动比例',
    '定时器延迟上限毫秒','默认可重试码','重试政策模式','解析重试政策',
)#公开面结束

默认最大重试次数=2#默认最多再试 2 次
默认初始延迟毫秒=500#默认初始延迟毫秒
默认最大延迟毫秒=10000#默认最大延迟毫秒
默认抖动比例=0.1#默认抖动比例
定时器延迟上限毫秒=2147483647#与 timeout 包 MAX_TIMER_DELAY_MS 相同
默认可重试码=深冻结([空响应码,'RATE_LIMIT','SERVER','TIMEOUT','TRANSPORT'])#冻结默认可重试失败码

退避模式=路径上节点({
    'initialDelayMs':数字字段(最大=定时器延迟上限毫秒,默认值=默认初始延迟毫秒),#初始延迟
    'maxDelayMs':数字字段(最大=定时器延迟上限毫秒,默认值=默认最大延迟毫秒),#最大延迟
    'jitterRatio':数字字段(最小=0,最大=1,默认值=默认抖动比例),#抖动比例
})#退避配置模式
普通政策模式=路径上节点({
    'mode':常量字段('normal',可空=False),#必须是 normal
    'maxRetries':整数字段(步进=1,最小=0,最大=9007199254740991,默认值=默认最大重试次数),#非负整数次数
    'retryableCodes':列表字段(字符串字段(),默认值=list(默认可重试码)),#可重试码列表
    'backoff':退避模式,#嵌套退避
})#普通政策模式
始终政策模式=路径上节点({
    'mode':常量字段('always',可空=False),#必须是 always
    'backoff':退避模式,#嵌套退避
})#始终政策模式
重试政策模式=复合类型字段(普通政策模式,始终政策模式)#政策配置联合模式

普通政策键=set(['mode','maxRetries','retryableCodes','backoff'])#普通政策允许的键
始终政策键=set(['mode','backoff'])#始终政策允许的键
退避键=set(['initialDelayMs','maxDelayMs','jitterRatio'])#退避允许的键

def 校验键(值,允许,路径):#拒绝未知键
    """拒绝未知键。"""
    for 键 in 值.keys():#逐键
        if 键 not in 允许:#未知键
            raise Exception(路径+': unknown key "'+键+'"')#未知键则失败

def 解析退避(配置,路径):#解析并校验退避
    """解析并校验退避。"""
    if 配置 is not None:#有配置
        校验键(配置,退避键,路径)#有配置则先拒未知键
    初始=配置.get('initialDelayMs') if 配置 is not None else None#初始延迟
    最大=配置.get('maxDelayMs') if 配置 is not None else None#最大延迟
    抖动=配置.get('jitterRatio') if 配置 is not None else None#抖动
    if 初始 is None:#缺省初始
        初始=默认初始延迟毫秒#默认初始
    if 最大 is None:#缺省最大
        最大=默认最大延迟毫秒#默认最大
    if 抖动 is None:#缺省抖动
        抖动=默认抖动比例#默认抖动
    if not (isinstance(初始,(int,float)) and not isinstance(初始,bool) and math.isfinite(初始) and 初始>0) or 初始>定时器延迟上限毫秒:#初始越界
        raise Exception(路径+'.initialDelayMs must be a positive finite number no greater than '+str(定时器延迟上限毫秒))#初始延迟越界
    if not (isinstance(最大,(int,float)) and not isinstance(最大,bool) and math.isfinite(最大) and 最大>0) or 最大>定时器延迟上限毫秒:#最大越界
        raise Exception(路径+'.maxDelayMs must be a positive finite number no greater than '+str(定时器延迟上限毫秒))#最大延迟越界
    if 初始>最大:#初始超过最大
        raise Exception(路径+'.initialDelayMs must be less than or equal to maxDelayMs')#初始不得超过最大
    if not (isinstance(抖动,(int,float)) and not isinstance(抖动,bool) and math.isfinite(抖动)) or 抖动<0 or 抖动>1:#抖动非法
        raise Exception(路径+'.jitterRatio must be between 0 and 1')#抖动必须在 0 到 1
    return 深冻结({'initialDelayMs':初始,'maxDelayMs':最大,'jitterRatio':抖动})#冻结已解析退避

def 解析重试政策(配置,路径):#校验、填默认并拆离重试政策
    """校验、填默认并拆离一份提供方拥有的重试政策。"""
    if 配置 is None:#缺省普通政策
        退避=解析退避(None,路径+'.backoff')#默认退避
        政策={'mode':'normal','maxRetries':默认最大重试次数,'retryableCodes':默认可重试码}#普通默认
        政策.update(退避)#并入退避字段
        return 深冻结(政策)#冻结
    模式值=配置.get('mode')#模式
    if 模式值=='normal':#普通模式
        校验键(配置,普通政策键,路径)#拒未知键
        次数=配置.get('maxRetries')#次数
        if 次数 is None:#缺省次数
            次数=默认最大重试次数#默认次数
        码列表=配置.get('retryableCodes')#码
        if 码列表 is None:#缺省码
            码列表=list(默认可重试码)#默认副本
        是安全整数=isinstance(次数,(int,float)) and not isinstance(次数,bool) and math.isfinite(次数) and 次数==int(次数) and abs(次数)<=9007199254740991#安全整数
        if not 是安全整数 or 次数<0:#次数非法
            raise Exception(路径+'.maxRetries must be a non-negative safe integer')#必须是非负安全整数
        if len(码列表)==0:#码列表空
            raise Exception(路径+'.retryableCodes must not be empty')#不可为空
        for 码 in 码列表:#逐码
            if not isinstance(码,str) or len(码)==0:#码非法
                raise Exception(路径+'.retryableCodes must contain only non-empty strings')#必须全是非空字符串
        if len(set(码列表))!=len(码列表):#有重复
            raise Exception(路径+'.retryableCodes must not contain duplicates')#不可重复
        政策={'mode':'normal','maxRetries':次数,'retryableCodes':深冻结(list(码列表))}#普通政策
        政策.update(解析退避(配置.get('backoff'),路径+'.backoff'))#解析退避
        return 深冻结(政策)#冻结普通政策
    if 模式值=='always':#始终模式
        校验键(配置,始终政策键,路径)#拒未知键
        政策={'mode':'always'}#始终模式
        政策.update(解析退避(配置.get('backoff'),路径+'.backoff'))#解析退避
        return 深冻结(政策)#冻结始终政策
    raise Exception(路径+'.mode must be "normal" or "always"')#模式必须是 normal 或 always
