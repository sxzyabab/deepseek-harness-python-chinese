"""一次包操作按何顺序询问哪些注册表，以及失败未能触及什么。"""
import re
from urllib.parse import urlparse,urlunparse

官方npm注册表='https://registry.npmjs.org/'
npmmirror注册表='https://registry.npmmirror.com/'
注册表网址=re.compile(r'^https?://\S+\Z',re.ASCII)
下一注册表种类=frozenset(('network','timeout','not-found','no-matching-version'))
错误行=re.compile(r'ERR_|ERROR|\berror\b|fatal:|Could not resolve|unable to access|ssh:|\bE[A-Z]{4,}\b',re.ASCII)

__all__=[
    '官方npm注册表','npmmirror注册表','注册表网址',
    '规范化注册表','注册表计划','归因失败',
]

class 注册表错误(Exception):
    """插件装载注册表解析失败。"""

def 规范化注册表(网址):
    """解析为 pnpm 比较用形态：小写主机、尾斜杠。"""
    try:
        解析=urlparse(网址)
    except ValueError:
        解析=None
    if 解析 is None or 解析.scheme not in ('http','https'):
        raise 注册表错误('a registry must be an http(s) URL: '+网址)
    路径=解析.path
    if not 路径.endswith('/'):
        路径=路径+'/'
    return urlunparse((解析.scheme,解析.netloc.lower(),路径,解析.params,解析.query,解析.fragment))

def 注册表计划(请求,已配置):
    """一次操作从先到后询问的注册表，永不为空。"""
    自身值=None if 已配置['resolved'] is None else 规范化注册表(已配置['resolved'])
    回退=[规范化注册表(项) for 项 in 已配置['fallbackRegistries']]
    自身公开=自身值 is not None and (自身值==官方npm注册表 or 自身值 in 回退)
    def 键(注册表):
        """pnpm 自有注册表在已知时代表它所命名的网址。"""
        return 自身值 if 注册表 is None else 规范化注册表(注册表)
    已知=[]
    键表=[]
    for 注册表 in [已配置['registry']]+list(已配置['fallbackRegistries']):
        if 注册表 is None and not 自身公开:
            continue
        当前键=键(注册表)
        if 当前键 in 键表:
            continue
        已知.append(None if 注册表 is None else 规范化注册表(注册表))
        键表.append(当前键)
    第一=已配置['registry'] if 请求 is None else 请求
    第一键=键(第一)
    规范第一=None if 第一 is None else 规范化注册表(第一)
    if (第一 is None or 第一键==自身值) and not 自身公开:
        return [规范第一]
    if 第一键 not in 键表:
        return [规范第一]
    return [规范第一]+[项 for 下标,项 in enumerate(已知) if 键表[下标]!=第一键]

def 归因失败(种类,日志,规格):
    """失败未能触及或得到回答的对象：registry / spec-host / other。"""
    if 种类 not in 下一注册表种类:
        return 'other'
    主机=None
    if 规格['kind'] in ('git','tarball') and 'host' in 规格 and 规格['host'] is not None:
        主机=规格['host'].lower()
    if 主机 is None:
        return 'registry'
    点名=False
    for 行 in 日志.split('\n'):
        if 错误行.search(行) is not None and 主机 in 行.lower():
            点名=True
            break
    return 'spec-host' if 点名 else 'registry'
