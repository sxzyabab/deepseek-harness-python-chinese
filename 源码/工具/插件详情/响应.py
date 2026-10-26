'宿主路由返回详情文档旁图片的 HTTP 响应'
from typing import TypedDict#图片记录

__all__=[#仅中文公开名
    '详情图片数据','详情图片响应',
]#公开面结束

失败状态={#每种详情失败的 HTTP 状态
    'too-large':413,
    'network':502,
    'denied':403,
    'git-unavailable':503,
    'invalid':400,
}#种类原样

安全策略="sandbox; default-src 'none'; style-src 'unsafe-inline'"#直接打开的 SVG 不能在已认证的 API 源上跑脚本

class 详情图片数据(TypedDict):#详情文档旁读到的一张图片
    '详情文档旁读到的一张图片'
    bytes:bytes#图片字节
    mediaType:str#媒体类型

def 详情图片响应(结果,缓存控制):#图片路由的响应
    """图片路由的响应：有图片时带缓存控制；没有图片时 404；失败时用该失败的状态，正文是失败种类。
    每个响应都带 nosniff 和 sandbox 内容安全策略。只有图片带上缓存控制"""
    if isinstance(结果,dict):#图片
        状态=200#成功
        主体=bytes(结果['bytes'])#拷进一块新的字节，不绑调用方的缓冲
        类型=结果['mediaType']#图片的媒体类型
    elif 结果 is None:#没有这张图片
        状态=404#未找到
        主体='not found'#正文原样
        类型=None#用纯文本
    else:#失败种类
        状态=失败状态[结果]#种类对应的状态
        主体=结果#正文就是种类
        类型=None#用纯文本
    return {#响应字段
        'status':状态,#状态码
        'headers':{#响应头，键原样
            'Content-Type':类型 if 类型 is not None else 'text/plain; charset=utf-8',#图片用自己的类型
            'Cache-Control':缓存控制 if 状态==200 else 'no-store',#失败和 404 不缓存
            'X-Content-Type-Options':'nosniff',#不嗅探
            'Content-Security-Policy':安全策略,#沙箱
        },#头结束
        'body':主体,#图片字节、not found 或失败种类
    }#响应结束
