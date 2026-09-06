"""单次打开的请求回合所用的浏览器时区推导与面向模型的策略文本。"""
import json,re#JSON诊断片段与IANA形态校验
from zoneinfo import ZoneInfo as 区时,ZoneInfoNotFoundError as 时区未找到#Intl等价的规范时区解析
from ...模型后端.llm import 断言永不#导入穷尽检查

IANA时区形态=re.compile(r'^[A-Za-z][A-Za-z0-9_+.-]*(?:/[A-Za-z0-9_+.-]+)+\Z',re.ASCII)#IANA Area/Location形态

def 编码(值):
    """诊断用紧凑 JSON。"""
    return json.dumps(值,ensure_ascii=False,separators=(',',':'),allow_nan=False)#JSON

def 浏览器时区(消息):
    """从一条普通 user-rpc 消息读取并校验宿主已规范化的浏览器时区。"""
    if 'source' not in 消息:#无来源
        return None#缺席
    来源=消息['source']#消息来源
    if not isinstance(来源,dict):#非对象
        return None#缺席
    if 来源['kind']!='user':#仅用户来源才可能带客户端时区
        return None#缺席
    if 'rpcId' not in 来源 or not isinstance(来源['rpcId'],str):#须带rpcId才算user-rpc
        return None#缺席
    if 'clientTimeZone' not in 来源 or not isinstance(来源['clientTimeZone'],str):#须声明客户端时区字段
        return None#缺席
    值=来源['clientTimeZone']#取出宿主给出的时区
    if 值!='UTC' and IANA时区形态.fullmatch(值) is None:#既非UTC也非IANA形态则拒绝
        raise TypeError('browser time zone must be canonical UTC or IANA Area/Location: '+编码(值))#诊断原文不翻译
    try:#尝试让ZoneInfo解析该时区
        规范=区时(值).key#用ZoneInfo解析规范名
    except (时区未找到,ValueError,KeyError) as 错误:#ZoneInfo不支持该时区
        raise TypeError('browser time zone is unsupported: '+编码(值)) from 错误#包装为TypeError
    if 规范!=值:#解析名与输入不一致则非规范
        raise TypeError('browser time zone must be canonical: '+编码(值))#拒绝非规范写法
    return 值#返回已校验的规范时区

def 推导浏览器时区上下文(消息列表):
    """推导一轮打开回合的唯一、混合或缺失浏览器时区。"""
    时区表=[]#收集时区
    for 消息 in 消息列表:#逐条
        时区=浏览器时区(消息)#抽取该消息时区
        if 时区 is not None:#有则贡献
            时区表.append(时区)#收下
    时区列表=sorted(set(时区表))#去重后按字典序排序
    if len(时区列表)==0:#一个都没有
        return {'kind':'missing'}#缺失
    if len(时区列表)==1:#恰好一个
        return {'kind':'resolved','timeZone':时区列表[0]}#唯一已解析时区
    return {'kind':'mixed','timeZones':时区列表}#多个互异时区

def 渲染浏览器时区上下文(上下文):
    """渲染一种浏览器时区上下文对应的模型指令，返回一条持久策略行。"""
    种类=上下文['kind']#三态标签
    if 种类=='resolved':#唯一时区
        return ('Browser time zone for this request: '+上下文['timeZone']+'. '
            +'Interpret otherwise-unqualified dates and times in this zone.')#无限定日期按此时区理解
    if 种类=='mixed':#多个时区
        return ('Browser time zone for this request: mixed '+编码(上下文['timeZones'])+'. '
            +'Ask the user to clarify otherwise-unqualified dates and times.')#无限定日期须向用户确认
    if 种类=='missing':#缺失时区
        return ('Browser time zone for this request: unavailable. '
            +'Ask the user to clarify otherwise-unqualified dates and times.')#无限定日期须向用户确认
    return 断言永不(上下文,'BrowserTimeZoneContext')#封闭联合穷尽检查
