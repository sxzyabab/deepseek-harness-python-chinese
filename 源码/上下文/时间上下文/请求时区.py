"""单次打开的请求回合所用的浏览器时区推导与面向模型的策略文本。"""
import json,re#JSON诊断片段与IANA形态校验
from zoneinfo import ZoneInfo as 区时#Intl等价的规范时区解析
from ...模型后端.llm import 断言永不#导入穷尽检查

IANA时区形态=re.compile(r'^[A-Za-z][A-Za-z0-9_+.-]*(?:/[A-Za-z0-9_+.-]+)+$')#IANA Area/Location形态
编码=json.dumps#JSON编码别名

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 有自有(对象,键):#对齐来源字段是否自有
    """对齐来源字段是否自有。"""
    if 对象 is None:#空对象
        return False#没有
    if isinstance(对象,dict):#映射
        return 键 in 对象#映射键
    字典=getattr(对象,'__dict__',None)#实例字典
    if 字典 is None:#没有字典
        return False#没有
    return 键 in 字典#自有

def 浏览器时区(消息):#抽取单条消息的浏览器时区
    """从一条普通 user-rpc 消息读取并校验宿主已规范化的浏览器时区。"""
    来源=取字段(消息,'source')#消息来源
    if (取字段(来源,'kind')=='user'#仅用户来源才可能带客户端时区
        and 有自有(来源,'rpcId')#须带rpcId才算user-rpc
        and isinstance(取字段(来源,'rpcId'),str)#rpcId必须是字符串
        and 有自有(来源,'clientTimeZone')#须声明客户端时区字段
        and isinstance(取字段(来源,'clientTimeZone'),str)):#时区必须是字符串
        值=取字段(来源,'clientTimeZone')#取出宿主给出的时区
    else:#非user-rpc或不带时区
        值=None#没有时区
    if 值 is None:#没有时区则跳过
        return None#缺席
    if 值!='UTC' and IANA时区形态.fullmatch(值) is None:#既非UTC也非IANA形态则拒绝
        raise TypeError('browser time zone must be canonical UTC or IANA Area/Location: '+编码(值,ensure_ascii=False))#诊断原文不翻译
    try:#尝试让ZoneInfo解析该时区
        规范=区时(值).key#用ZoneInfo解析规范名
    except Exception as 错误:#ZoneInfo不支持该时区
        raise TypeError('browser time zone is unsupported: '+编码(值,ensure_ascii=False)) from 错误#包装为TypeError
    if 规范!=值:#解析名与输入不一致则非规范
        raise TypeError('browser time zone must be canonical: '+编码(值,ensure_ascii=False))#拒绝非规范写法
    return 值#返回已校验的规范时区

def 推导浏览器时区上下文(消息们):#推导本回合浏览器时区上下文
    """推导一轮打开回合的唯一、混合或缺失浏览器时区。排序去重后的浏览器时区事实；某条 user-rpc 来源携带非法或非规范时区时抛 TypeError。"""
    时区表=[]#收集时区
    for 消息 in 消息们:#逐条
        时区=浏览器时区(消息)#抽取该消息时区
        if 时区 is not None:#有则贡献
            时区表.append(时区)#收下
    时区们=sorted(set(时区表))#去重后按字典序排序
    if len(时区们)==0:#一个都没有
        return {'kind':'missing'}#缺失
    if len(时区们)==1:#恰好一个
        return {'kind':'resolved','timeZone':时区们[0]}#唯一已解析时区
    return {'kind':'mixed','timeZones':时区们}#多个互异时区

def 渲染浏览器时区上下文(上下文):#渲染浏览器时区策略文本
    """渲染一种浏览器时区上下文对应的模型指令，返回一条持久策略行。"""
    种类=取字段(上下文,'kind')#三态标签
    if 种类=='resolved':#唯一时区
        return ('Browser time zone for this request: '+取字段(上下文,'timeZone')+'. '#策略行前半
            +'Interpret otherwise-unqualified dates and times in this zone.')#无限定日期按此时区理解
    if 种类=='mixed':#多个时区
        return ('Browser time zone for this request: mixed '+编码(取字段(上下文,'timeZones'),ensure_ascii=False)+'. '#列出全部时区
            +'Ask the user to clarify otherwise-unqualified dates and times.')#无限定日期须向用户确认
    if 种类=='missing':#缺失时区
        return ('Browser time zone for this request: unavailable. '#声明不可用
            +'Ask the user to clarify otherwise-unqualified dates and times.')#无限定日期须向用户确认
    return 断言永不(上下文,'BrowserTimeZoneContext')#封闭联合穷尽检查
