from ....模块.客户端.通告 import 取握手窗口
import re
from .字节 import 解码文本
from ..面 import 已中止

__all__=['打包超文本']

单资源上限=4*1024*1024
总计上限=32*1024*1024
数量上限=64
绝对前缀=re.compile(r'^(?:[a-z][a-z\d+.-]*:|[/\\#?])',re.IGNORECASE)
脚本类型=('','text/javascript','application/javascript')

def 是否相对(引用):
    '能否相对原文档读取。空、协议、绝对、空字节都不行'
    return len(引用)>0 and 绝对前缀.search(引用) is None and '\0' not in 引用

def 打包超文本(数据,相对读取,信号):
    '收集直接的 .js 与 .css。有 base[href] 时不打包依赖。超限或读取失败抛错'
    if 已中止(信号):
        raise RuntimeError('已中止')
    总计=len(数据)
    if 总计>总计上限:
        raise ValueError('HTML package exceeds its total byte limit')
    模板=取握手窗口().document.createElement('template')
    模板.innerHTML=解码文本(数据)
    资源=[]
    if 模板.content.querySelector('base[href]') is not None:
        return {'data':数据,'assets':资源}
    见过=set()
    for 元素 in 模板.content.querySelectorAll('script[src],link[href]'):
        是脚本=元素.localName=='script'
        类型=(元素.getAttribute('type') or '').strip().lower()
        if 是脚本 and 类型 not in 脚本类型:
            continue
        if not 是脚本:
            关系=(元素.getAttribute('rel') or '').lower().split()
            if 'stylesheet' not in 关系:
                continue
        引用=元素.getAttribute('src' if 是脚本 else 'href')
        切=len(引用)
        for 符 in ('?','#'):
            位=引用.find(符)
            if 位!=-1 and 位<切:
                切=位
        路径=引用 if 切==len(引用) else 引用[:切]
        if not 是否相对(引用):
            continue
        if 是脚本 and not 路径.lower().endswith('.js'):
            continue
        if not 是脚本 and not 路径.lower().endswith('.css'):
            continue
        种类='script' if 是脚本 else 'stylesheet'
        键=种类+':'+引用
        if 键 in 见过:
            continue
        if len(资源)>=数量上限:
            raise ValueError('HTML package exceeds its asset count limit')
        if 已中止(信号):
            raise RuntimeError('已中止')
        待=相对读取(引用,信号)
        项=待.等待() if hasattr(待,'等待') else 待
        if 已中止(信号):
            raise RuntimeError('已中止')
        大小=len(项['data'])
        if 大小>单资源上限:
            raise ValueError('HTML asset exceeds its byte limit')
        总计=总计+大小
        if 总计>总计上限:
            raise ValueError('HTML package exceeds its total byte limit')
        解码文本(项['data'])
        资源.append({'kind':种类,'reference':引用,'data':项['data']})
        见过.add(键)
    return {'data':数据,'assets':资源}
