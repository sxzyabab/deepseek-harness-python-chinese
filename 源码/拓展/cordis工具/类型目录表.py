"""装配类型目录——本包 `类型目录_*.txt`（509 条，对齐上游 TYPE_API）。"""
import os#路径
from .类型条目解析 import 解析类型紧凑文本#紧凑行解析

__all__=['类型目录','类型片段名们','类型本地条数','类型上游条数']#公开面

_本目录=os.path.dirname(os.path.abspath(__file__))#本包
类型上游条数=509#上游 TYPE_API 名数
类型片段名们=[#按序拼接，无重叠
    '类型目录_01.txt',#Adapter–DynamicCordis*
    '类型目录_02.txt',#EditGoal–LlmReasoning*
    '类型目录_03.txt',#LlmResolved–SessionEventType
    '类型目录_04.txt',#SessionEventWindow–ToolDispatch*
    '类型目录_05.txt',#ToolErrorInfo–Workflow*
]#片段

def _装载():#读全部片段
    """逐文件解析并拼接。"""
    合计=[]#条目
    for 名 in 类型片段名们:#每个片段
        路径=os.path.join(_本目录,名)#绝对路径
        with open(路径,'r',encoding='utf-8') as 文件:#读文本
            合计.extend(解析类型紧凑文本(文件.read()))#并入
    return 合计#全表

类型目录=_装载()#导入时物化
类型本地条数=len({条目['name'] for 条目 in 类型目录})#去重名数
