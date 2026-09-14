import json#载荷
from .字节 import 解码文本,编码文本#编解码

__all__=['创建超文本文档']#仅中文公开名


def 创建超文本文档(包):
    """构建外层 iframe 文档。包为 dict：data / assets。

    无效 UTF-8 在导航前抛出。
    """
    资源列表=[{#资源
        'kind':项['kind'],
        'reference':项['reference'],
        'text':解码文本(项['data']),
    } for 项 in 包.get('assets',())]#映射
    载荷=编码文本(json.dumps({'html':解码文本(包['data']),'assets':资源列表},ensure_ascii=False,separators=(',',':')))#载荷
    脚本=(
        '<!doctype html><meta charset="utf-8"><script>(()=>{'
        'const bytes=data=>Uint8Array.from(atob(data),character=>character.charCodeAt(0));'
        "const text=data=>new TextDecoder('utf-8',{fatal:true}).decode(bytes(data));"
        'const bundle=JSON.parse(text("'+载荷+'"));'
        'let html=bundle.html;'
        'if(bundle.assets.length){'
        "const parsed=new DOMParser().parseFromString(html,'text/html');"
        'for(const asset of bundle.assets){'
        "const script=asset.kind==='script';"
        "const url=URL.createObjectURL(new Blob([asset.text],{type:script?'application/javascript':'text/css'}));"
        "const attribute=script?'src':'href';"
        'for(const element of parsed.querySelectorAll(script?\'script[src]\':\'link[rel~="stylesheet" i][href]\')){'
        'if(element.getAttribute(attribute)===asset.reference)element.setAttribute(attribute,url);'
        '}'
        '}'
        "html='<!doctype html>'+parsed.documentElement.outerHTML;"
        '}'
        'document.open();document.write(html);document.close();'
        '})()</script>'
    )#引导 HTML
    return 脚本#文档
