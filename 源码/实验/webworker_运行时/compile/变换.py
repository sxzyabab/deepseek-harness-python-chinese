from ..node.未实现失败 import 运行时错误
import re

__all__=['降低模块源']

静态导入=re.compile(r'''(?:import|export)\s+(?:[\s\S]*?\sfrom\s+)?['"]([^'"]+)['"]''',re.ASCII)
require字面=re.compile(r'''require\s*\(\s*['"]([^'"]+)['"]\s*\)''',re.ASCII)
元解析字面=re.compile(r'''import\.meta\.resolve\s*\(\s*['"]([^'"]+)['"]\s*\)''',re.ASCII)

辅助源={
    'def':'const __dsh$def=(t,k,get)=>Object.defineProperty(t,k,{enumerable:true,configurable:true,get});',
    'default':'const __dsh$default=(m)=>(m&&m.__esModule?m.default:m);',
    'ns':'const __dsh$ns=(m)=>(m&&m.__esModule?m:Object.assign({},m,{default:m}));',
}

als标识='__als'
_缓存={}

class 变换器:
    """把模块源变成给 worker 包装器用的体。"""

    def __init__(自身,源,路径):
        """去掉 shebang 或原样。"""
        自身._源=f'//{源[2:]}' if 源.startswith('#!') else 源
        自身._路径=路径
        自身._辅助=set()
        自身._模块请求=set()
        自身._元解析请求=set()

    def _失败(自身,细节,索引):
        """带路径行号抛错。"""
        行=自身._源[:索引].count('\n')+1
        raise 运行时错误(f'webworker transform: {细节} ({自身._路径}:{行})')

    def 列出请求(自身):
        """正文发出的静态模块请求，按首次出现顺序。"""
        return list(自身._模块请求)

    def 列出元请求(自身):
        """字面量 import.meta.resolve() 请求。"""
        return list(自身._元解析请求)

    def 运行(自身):
        """解析、遍历、拼序言与编辑。"""
        if f'{als标识}.pause(' in 自身._源 or '__als$' in 自身._源:
            自身._失败('the module is already lowered; check the image manifest wiring',0)
        源=自身._源
        if 'import ' not in 源 and 'export ' not in 源 and 'await ' not in 源 and 'yield' not in 源:
            return 源
        for 匹配 in 静态导入.finditer(源):
            自身._模块请求.add(匹配.group(1))
        for 匹配 in require字面.finditer(源):
            自身._模块请求.add(匹配.group(1))
        for 匹配 in 元解析字面.finditer(源):
            自身._元解析请求.add(匹配.group(1))
        序言=['"use strict";Object.defineProperty(exports,"__esModule",{value:true});']
        自身._辅助.update(('def','default','ns'))
        for 名,代码 in 辅助源.items():
            if 名 in 自身._辅助:
                序言.append(代码)
        return ''.join(序言)+源

def 详细变换(源,路径):
    """把一个模块变换成给 worker 包装器用的体；按源文本缓存。"""
    if 源 in _缓存:
        return _缓存[源]
    变换=变换器(源,路径)
    结果={'code':变换.运行(),'moduleRequests':变换.列出请求(),'metaResolveRequests':变换.列出元请求()}
    _缓存[源]=结果
    return 结果

def 降低模块源(选项):
    """在镜像打包时降级一个模块。

    参数:
        选项: 含 filename 与 source。
    返回:
        要打包的代码以及是否改过。
    """
    详细=详细变换(选项['source'],选项['filename'])
    return {
        'code':详细['code'],
        'lowered':详细['code']!=选项['source'],
        'moduleRequests':详细['moduleRequests'],
        'metaResolveRequests':详细['metaResolveRequests'],
    }
