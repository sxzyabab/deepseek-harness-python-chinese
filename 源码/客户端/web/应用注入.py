import pywebbridge
from json import dumps as 编码#未知行的诊断文本
from .异常 import 网页错误#本包失败


def 应用索引注入(行表,加载脚本,窗口):
    '按表顺序执行索引注入行。加载脚本负责 script-src，同步返回后再下一行'
    文档=窗口.document#文档
    for 行 in 行表:#逐行，顺序不能换
        种类=行['kind']#行种类
        if 种类=='global':#全局
            窗口[行['name']]=行['value']#写到页面全局
        elif 种类=='script':#内联脚本
            节点=文档.createElement('script')#script
            节点.textContent=行['text']#正文
            if 行['placement']=='head':#头部
                文档.head.append(节点)#插入 head
            else:#身体
                文档.body.append(节点)#插入 body
        elif 种类=='script-src':#外链脚本
            加载脚本(行['src'])#由调用方的传输去加载，这里等它返回
        elif 种类=='script-preload':#有的传输不能只预加载不执行
            pass#真正的请求归加载脚本
        elif 种类=='style':#样式
            节点=文档.createElement('style')#style
            节点.textContent=行['text']#正文
            文档.head.append(节点)#插入 head
        elif 种类=='html':#原始片段
            if 行['placement']=='head':#头部
                文档.head.insertAdjacentHTML('beforeend',行['html'])#插到 head 末尾
            else:#身体
                文档.body.insertAdjacentHTML('beforeend',行['html'])#插到 body 末尾
        else:#没有这种行
            raise 网页错误('网页启动：未知的索引注入行 '+编码(行,ensure_ascii=False))#失败
