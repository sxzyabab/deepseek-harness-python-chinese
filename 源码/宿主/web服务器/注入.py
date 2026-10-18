'结构化索引注入：插件往启动 HTML 里填的行，而不是裸 tapIndex 字符串变换'
import json,re#行文本与标签定位
from .异常 import 网页服务器错误#未知行

__all__=['渲染索引注入']#本文件公开名

就绪标记='<script>(globalThis.__DSH_BOOT_READY__ ??= Promise.withResolvers()).resolve()</script>'#启动就绪尾脚本

def 转义属性(值):
    '放进引号属性前转义 & " < >'
    文本=值.replace('&','&amp;')#先转 &
    文本=文本.replace('"','&quot;')#引号
    文本=文本.replace('<','&lt;')#左尖
    文本=文本.replace('>','&gt;')#右尖
    return 文本#属性文本

def 拼接(页面,位置,标记):
    '在下标处插入标记'
    return 页面[:位置]+标记+页面[位置:]#前后接上

def 渲染索引注入(页面,行表):
    '头行紧跟 head 开标签，体行紧跟 body 开标签，体行后再加就绪尾'
    头=''#头标记
    体=''#体标记
    for 行 in 行表:#逐行
        种类=行['kind']#行种类
        if 种类=='global':#全局赋值
            名=json.dumps(行['name'],ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')#名
            if 'value' not in 行:#缺值是 undefined
                值文本='undefined'#脚本字面量
            else:#有值
                值文本=json.dumps(行['value'],ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')#JSON
            位置名='head'#固定进头
            标记='<script>globalThis['+名+'] = '+值文本+'</script>'#赋值脚本
        elif 种类=='script':#内联脚本
            位置名=行['placement']#调用方指定
            标记='<script>'+行['text']+'</script>'#原样
        elif 种类=='script-src':#外链脚本
            位置名=行['placement']#调用方指定
            标记='<script src="'+转义属性(行['src'])+'"></script>'#src
        elif 种类=='script-preload':#预加载
            位置名='head'#固定进头
            标记='<link rel="preload" as="script" href="'+转义属性(行['src'])+'">'#链接
        elif 种类=='style':#样式
            位置名='head'#固定进头
            标记='<style>'+行['text']+'</style>'#原样
        elif 种类=='html':#原始片段
            位置名=行['placement']#调用方指定
            标记=行['html']#原样
        else:#没有这种行
            raise 网页服务器错误('webserver: unknown index injection row '+json.dumps(行,ensure_ascii=False,separators=(',',':')))#未知行
        if 位置名=='head':#头
            头+=标记#接上
        else:#体
            体+=标记#接上
    体+=就绪标记#就绪尾始终跟在体行后面
    输出=页面#工作副本
    if 头!='':#有头行
        开=re.search(r'<head(?:\s[^>]*)?>',输出,re.I)#head 开标签
        if 开 is None:#没有 head
            输出=头+输出#整段前置
        else:#插在开标签后
            输出=拼接(输出,开.end(),头)#插入
    if 体!='':#就绪尾使体标记不会空
        开=re.search(r'<body(?:\s[^>]*)?>',输出,re.I)#body 开标签
        if 开 is None:#没有 body
            输出=输出+体#整段后置
        else:#插在开标签后
            输出=拼接(输出,开.end(),体)#插入
    return 输出#渲染结果
