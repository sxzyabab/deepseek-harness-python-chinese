import re
from .原始工具调用 import 解析工具调用

__all__=['图像卡模型']

图像信封=re.compile(r'^<path>[^\n]*</path>\n<type>image</type>\n<content>\n[\s\S]*\n</content>$')
图像媒体类型=frozenset(['image/png','image/jpeg','image/webp','image/gif'])

def 正整数(值):
    '大于 0 的整数'
    return isinstance(值,int) and not isinstance(值,bool) and 值>0

def 是图像媒体类型(值):
    '四种耐久图像媒体类型'
    return 值 in 图像媒体类型

def 图像元数据(元数据):
    '只要非空 path。嵌套调用可以没有元数据'
    if not isinstance(元数据,dict):
        return None
    路径=元数据.get('path')
    if not isinstance(路径,str) or 路径=='':
        return None
    return {'path':路径}

def 图像引用(内容):
    '按结果顺序收图像块。任一畸形图像块则整卡放弃'
    引用表=[]
    for 部分 in 内容:
        if not isinstance(部分,dict):
            continue
        if 部分.get('type')!='image':
            continue
        附件=部分.get('attachment')
        if not isinstance(附件,dict):
            return None
        标识=附件.get('attachmentId')
        媒体=附件.get('mediaType')
        if not isinstance(标识,str) or 标识=='':
            return None
        if not isinstance(媒体,str) or not 是图像媒体类型(媒体):
            return None
        if not 正整数(附件.get('bytes')) or not 正整数(附件.get('width')) or not 正整数(附件.get('height')):
            return None
        if 'name' in 附件 and not isinstance(附件.get('name'),str):
            return None
        条目={
            'attachmentId':标识,
            'mediaType':媒体,
            'bytes':附件['bytes'],
            'width':附件['width'],
            'height':附件['height'],
        }
        if 'name' in 附件:
            条目['name']=附件['name']
        if 'originalDimensions' in 附件:
            原始=附件['originalDimensions']
            if not isinstance(原始,dict):
                return None
            if not 正整数(原始.get('width')) or not 正整数(原始.get('height')):
                return None
            条目['originalDimensions']={'width':原始['width'],'height':原始['height']}
        引用表.append(条目)
    if len(引用表)==0:
        return None
    return 引用表

def 额外文本(内容):
    '信封以外的文本块按顺序接上'
    段=[]
    for 部分 in 内容:
        if not isinstance(部分,dict) or 部分.get('type')!='text':
            continue
        文本=部分.get('text')
        if isinstance(文本,str) and 图像信封.search(文本) is None:
            段.append(文本)
    if len(段)==0:
        return None
    return '\n'.join(段)

def 全部可画(内容):
    '每一块都是带文本的 text 或 image'
    for 部分 in 内容:
        if not isinstance(部分,dict):
            return False
        类型=部分.get('type')
        if 类型=='image':
            continue
        if 类型=='text' and isinstance(部分.get('text'),str):
            continue
        return False
    return True

def 图像卡模型(块):
    '已结算 read_image。运行中、错误或信封不完整则 None'
    if 'kind' not in 块 or 块.get('isError') is True:
        return None
    已解析=解析工具调用(块)
    if 已解析 is None or 已解析['name']!='read_image':
        return None
    文件路径=已解析['args'].get('file_path')
    if not isinstance(文件路径,str) or 文件路径.strip()=='':
        return None
    元路径=None
    元=图像元数据(块.get('meta'))
    if 元 is not None:
        元路径=元['path']
    if 元路径 is not None:
        路径=元路径
    elif 块.get('parentCallId') is not None:
        路径=文件路径
    else:
        return None
    内容=块['content']
    if not 全部可画(内容):
        return None
    引用=图像引用(内容)
    if 引用 is None:
        return None
    有信封=False
    for 部分 in 内容:
        if isinstance(部分,dict) and 部分.get('type')=='text' and isinstance(部分.get('text'),str) and 图像信封.search(部分['text']) is not None:
            有信封=True
            break
    if not 有信封:
        return None
    图像=[]
    for 引用项 in 引用:
        图像.append({'attachment':引用项})
    return {'path':路径,'images':图像,'extraText':额外文本(内容)}
