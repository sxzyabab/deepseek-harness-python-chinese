'会话撰写器在 Safari 上的文本域布局修复'
import re

__all__=['是Safari浏览器','修复Safari文本域布局']

其他苹果浏览器=re.compile(r'\b(?:CriOS|FxiOS|EdgiOS|OPiOS|OPT|DuckDuckGo|Brave)(?:/|\b)')
Safari标记=re.compile(r'\bVersion/[\d.]+.*\bSafari/[\d.]+')

def 是Safari浏览器(身份):
    '厂商是苹果，且用户代理是 Safari 而不是别的 iOS 浏览器'
    return 身份['vendor']=='Apple Computer, Inc.' and Safari标记.search(身份['userAgent']) is not None and 其他苹果浏览器.search(身份['userAgent']) is None

def 修复Safari文本域布局(输入):
    'Safari 把过期的文本域高度沾到滚动口上时，抖一下高度再收回'
    if 输入 is None or 输入.scrollHeight<=输入.clientHeight:
        return
    滚动口=输入.closest('[data-input-scroll]')
    if 滚动口 is None:
        return
    输入高=输入.style.height
    输入.style.height=str(输入.clientHeight+1)+'px'
    输入.offsetHeight
    输入.style.height=输入高
    输入.offsetHeight
    滚动高=滚动口.style.height
    滚动口.style.height=str(滚动口.clientHeight+1)+'px'
    滚动口.offsetHeight
    滚动口.style.height=滚动高
    滚动口.offsetHeight
