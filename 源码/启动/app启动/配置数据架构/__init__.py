"""配置档模式生成：组合诊断、运行时解析与无启动发现。"""
import json
from ..配置档 import 组合条目,读配置清单,创建配置解析世代
from .收集 import 收集配置数据架构

__all__=['生成配置数据架构','跳过的配置组合包']

def 跳过的配置组合包(配置档,清单):
    """选出未产出已加载层的组合包名。"""
    段=((清单 or {}).get('dsh') or {}).get('profile') or {}
    已选=段.get('bundles') or []
    已加载=set(层['packageName'] for 层 in (配置档 or {}).get('layers') or [])
    return set(名 for 名 in 已选 if 名 not in 已加载)

def 生成配置数据架构(二进制名,配置档,各层,安装锚点):
    """为已准备配置档的有序补丁层生成 JSON Schema，不挂载插件、不求值表达式。"""
    诊断=[]
    清单=读配置清单(二进制名,配置档['dir'])
    for 包名 in 跳过的配置组合包(配置档,清单):
        诊断.append({
            'level':'error',
            'message':'Selected profile bundle '+json.dumps(包名,ensure_ascii=False,separators=(',',':'),allow_nan=False)+' could not be loaded; repair or remove its bundle selection.',
        })
    def 记警告(消息):
        """组合警告。"""
        诊断.append({'level':'warning','message':消息})
    条目=组合条目(各层,记警告)
    解析=创建配置解析世代({'installAnchor':安装锚点})
    return 收集配置数据架构(配置档,条目,解析,诊断)
