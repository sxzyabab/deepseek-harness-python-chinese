'结构化索引注入：插件往启动 HTML 里填的行，而不是裸 tapIndex 字符串变换'
import json,re#编码与标签定位

__all__=['渲染索引注入']#仅中文公开名

就绪标记='<script>(globalThis.__DSH_BOOT_READY__ ??= Promise.withResolvers()).resolve()</script>'#启动就绪尾脚本

def 转义属性(值):#放进引号属性前转义
    '转义 & " < >'
    return 值.replace('&','&amp;').replace('"','&quot;').replace('<','&lt;').replace('>','&gt;')#四字符

def 渲染行(行):#一行变成带位置的标记
    '按 kind 产出 placement 与 markup'
    种类=行['kind']#行种类
    if 种类=='global':#全局赋值
        名=json.dumps(行['name'],ensure_ascii=False).replace('<','\\u003c')#名
        if 'value' not in 行:#缺值是 undefined
            值文本='undefined'#脚本字面量
        else:#有值
            值文本=json.dumps(行['value'],ensure_ascii=False).replace('<','\\u003c')#JSON
        return {'placement':'head','markup':'<script>globalThis['+名+'] = '+值文本+'</script>'}#头
    if 种类=='script':#内联脚本
        return {'placement':行['placement'],'markup':'<script>'+行['text']+'</script>'}#原样
    if 种类=='script-src':#外链脚本
        return {'placement':行['placement'],'markup':'<script src="'+转义属性(行['src'])+'"></script>'}#src
    if 种类=='script-preload':#预加载
        return {'placement':'head','markup':'<link rel="preload" as="script" href="'+转义属性(行['src'])+'">'}#头
    if 种类=='style':#样式
        return {'placement':'head','markup':'<style>'+行['text']+'</style>'}#头
    if 种类=='html':#原始片段
        return {'placement':行['placement'],'markup':行['html']}#原样
    raise RuntimeError('webserver: unknown index injection row '+json.dumps(行,ensure_ascii=False))#未知行

def 拼接(html,位置,标记):#在下标处插入
    'html 的位置处插入标记'
    return html[:位置]+标记+html[位置:]#拼接

def 渲染索引注入(html,行表):#把行渲染进 index.html
    '头行紧跟 head 开标签，体行紧跟 body 开标签，体行后再加就绪尾'
    头=''#头标记
    体=''#体标记
    for 行 in 行表:#逐行
        已渲染=渲染行(行)#标记
        if 已渲染['placement']=='head':#头
            头+=已渲染['markup']#接上
        else:#体
            体+=已渲染['markup']#接上
    体+=就绪标记#就绪尾
    输出=html#工作副本
    if 头!='':#有头行
        开=re.search(r'<head(?:\s[^>]*)?>',输出,re.I)#head 开标签
        输出=头+输出 if 开 is None else 拼接(输出,开.end(),头)#无 head 则前置
    if 体!='':#有体行
        开=re.search(r'<body(?:\s[^>]*)?>',输出,re.I)#body 开标签
        输出=输出+体 if 开 is None else 拼接(输出,开.end(),体)#无 body 则后置
    return 输出#渲染结果
