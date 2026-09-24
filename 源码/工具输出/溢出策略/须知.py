"""溢出策略持久须知的浏览器安全格式化与识别。"""
import re
from ...工具.输出保留 import 描述省略

开='('
闭=')'
定位=' Full formatted result stored at: '
指引分隔='. '
分隔='\n\n'
精确省略=描述省略({'kind':'exact','count':0},'bytes')
计数偏移=精确省略.find('0')
计数后缀=精确省略[计数偏移+1:]

def 格式化溢出须知(省略,引用,图像数=0):
    """格式化接到持留预览后的须知，拼写与持久文本一致。"""
    图像句=(' Omitted '+str(图像数)+' images.') if 图像数>0 else ''
    return 开+描述省略(省略,'bytes')+图像句+定位+str(引用['locator'])+指引分隔+str(引用['retrievalHint'])+闭

def 是否省略句(文本):
    """文本是否为描述省略产生的省略句。"""
    图像须知=re.search(r' Omitted ([1-9][0-9]*) images\.$',文本)
    if 图像须知 is not None:
        数字=int(图像须知.group(1))
        if isinstance(数字,bool) or 数字>9007199254740991:
            return False
        文本=文本[:图像须知.start()]
    if 文本==描述省略({'kind':'none'},'bytes') or 文本==描述省略({'kind':'unknown'},'bytes'):
        return True
    计数文本=文本[计数偏移:len(文本)-len(计数后缀)]
    try:
        计数=int(计数文本)
    except ValueError:
        return False
    return 计数>=0 and 文本==描述省略({'kind':'exact','count':计数},'bytes')

def 含溢出须知(文本):
    """识别持久文本末尾是否有完整溢出策略须知。"""
    if not 文本.endswith(闭):
        return False
    起点=0
    while True:
        下一段=文本.find(分隔+开,起点)
        候选=文本[起点:(-len(闭) if 下一段<0 else 下一段)]
        定位处=候选.find(定位,len(开))
        if 候选.startswith(开) and 定位处>=0 and 是否省略句(候选[len(开):定位处]):
            return 文本.find(指引分隔,起点+定位处+len(定位))>=0
        if 下一段<0:
            return False
        起点=下一段+len(分隔)

__all__=['格式化溢出须知','含溢出须知']
