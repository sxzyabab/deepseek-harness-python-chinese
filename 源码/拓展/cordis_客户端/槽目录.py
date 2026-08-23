"""客户端槽位编译期约定目录。

对齐上游 `拓展/cordis-client-runner/src/client/slot-catalog.ts`。
纯字符串数据、无客户端导入；从原版相对路径整表加载。公开面仅中文名。
"""
import os#路径
from ..cordis工具.字面量解析 import 提取导出常量数组,解析数组字面量#复用解析器

__all__=['客户端说明','客户端槽目录','上游槽目录路径','查询槽目录']#公开面

_本目录=os.path.dirname(os.path.abspath(__file__))#本包
上游槽目录路径=os.path.normpath(os.path.join(
    _本目录,'..','..','..','..','..','..','project','dsh分析','源码','拓展','cordis-client-runner','src','client','slot-catalog.ts',
))#原版槽目录

def _加载():#读文件并解析
    """抽出 CLIENT_NOTES 与 CLIENT_SLOT_API。"""
    with open(上游槽目录路径,'r',encoding='utf-8') as 文件:#读
        源=文件.read()#全文
    return (#两表
        解析数组字面量(提取导出常量数组(源,'CLIENT_NOTES')),#说明
        解析数组字面量(提取导出常量数组(源,'CLIENT_SLOT_API')),#槽
    )#返回

客户端说明,客户端槽目录=_加载()#导入时物化

def 查询槽目录(键=None,槽们=None):#查询槽
    """紧凑目录，或一条精确槽约定。"""
    if 槽们 is None:#缺省
        槽们=客户端槽目录#模块
    if 键 is None:#列目录
        return {#压缩
            'mode':'catalog',#模式
            'notes':list(客户端说明),#贡献规则
            'slots':[{#每条
                'key':槽['key'],#键
                'kind':槽['kind'],#基数
                'scope':槽['scope'],#作用域
                'summary':槽['summary'],#摘要
                'replaceRisk':槽['replaceRisk'],#替换风险
            } for 槽 in 槽们],#map
        }#目录
    槽=None#按键找
    for 候选 in 槽们:#查找
        if 候选['key']==键:#命中
            槽=候选#记下
            break#结束
    if 槽 is None:#未知
        raise Exception('no catalogued Slot named "'+键+'"')#失败
    return {'mode':'slot','slot':槽,'notes':list(客户端说明)}#精确约定
