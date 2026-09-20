"""校验过的当前布局快照；撤销历史归活动窗口。"""
import json#JSON

__all__=['侧栏持久化前缀','读侧栏布局','写侧栏布局','清侧栏布局']#仅中文公开名

侧栏持久化前缀='dsh.sidebar-right.v1'#持久化前缀
空历史={'past':[],'future':[]}#空撤销历史

def 读侧栏布局(会话标识,存储=None):
    """恢复一份校验过的会话布局，并配上全新的窗口内撤销历史。存储需 getItem。"""
    if 存储 is None:#无存储
        return None#缺失
    原文=存储.getItem(侧栏持久化前缀+'.'+会话标识)
    if 原文 is None:
        return None
    try:
        信封=json.loads(原文)
        会话表=信封['bySession'] if 'bySession' in 信封 and 信封['bySession'] is not None else {}
        已存=会话表[会话标识] if 会话标识 in 会话表 else None
        if 已存 is None:
            return None
        return {'layout':已存['layout'],'minted':已存['minted'],'history':dict(空历史)}
    except (json.JSONDecodeError,KeyError,TypeError):
        清侧栏布局(会话标识,存储)#清坏数据
        return None#失败

def 写侧栏布局(会话标识,表面,存储=None):
    """持久化当前布局与身份分配，不保留撤销条目。"""
    if 存储 is None:#无存储
        return#空
    已存={'bySession':{会话标识:{'layout':表面['layout'],'minted':表面['minted']}}}#信封
    try:#写
        存储.setItem(侧栏持久化前缀+'.'+会话标识,json.dumps(已存,ensure_ascii=False,separators=(',',':'),allow_nan=False))
    except (TypeError,ValueError,AttributeError,OSError) as 错误:
        print('侧栏布局持久化失败:',错误)

def 清侧栏布局(会话标识,存储=None):
    """只移除一个会话的已持久化布局。"""
    if 存储 is None:#无存储
        return#空
    try:#删
        存储.removeItem(侧栏持久化前缀+'.'+会话标识)
    except (TypeError,AttributeError,OSError):
        pass
