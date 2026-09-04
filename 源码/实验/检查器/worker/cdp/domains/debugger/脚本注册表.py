"""连接本地从 CDP ScriptId 到 realm 源后端的路由。"""
#对齐上游 worker/cdp/domains/debugger/script-registry.ts

from ...标识 import cdp字符串id#CDP脚本id

__all__=['cdp脚本id','调试器脚本注册表']#仅中文公开名

def cdp脚本id(脚本键):#脚本键转CDP id
    """规范化脚本键为连接可见 ScriptId。"""
    return cdp字符串id(脚本键,'scriptId')#品牌id

class 调试器脚本注册表:#调试器脚本注册表
    """跟踪活动与已退役脚本，不暴露源传输 id。"""
    def __init__(自身):#构造
        """初始化路由表。"""
        自身._路由={}#路由表
        自身._已退役不支持=set()#已退役不支持

    def 注册(自身,路由):#注册
        """在其全局唯一的 Runtime 脚本键下注册一个 realm 脚本。"""
        脚本id=cdp脚本id(路由['script']['scriptKey'])#脚本id
        当前=自身._路由.get(脚本id)#已有
        if 当前 is not None and 当前['realm'] is not 路由['realm']:#冲突
            raise ValueError(f'Inspector realms produced the same script key {脚本id}')#抛错
        自身._路由[脚本id]=路由#写入
        return {'scriptId':脚本id,'fresh':当前 is None}#返回

    def 解析(自身,脚本id):#解析
        """解析一个活动的 CDP ScriptId。"""
        return 自身._路由.get(cdp字符串id(脚本id,'scriptId'))#取路由

    def 按url(自身,url):#按URL
        """按精确 URL 解析脚本。"""
        for 路由 in 自身._路由.values():#扫路由
            if 路由['script']['url']==url:#命中
                return 路由#返回
        return None#未找到

    def 按哈希(自身,哈希):#按哈希
        """按精确内容哈希解析脚本。"""
        for 路由 in 自身._路由.values():#扫路由
            if 路由['script'].get('hash')==哈希:#命中
                return 路由#返回
        return None#未找到

    def 按url模式(自身,模式):#按URL模式
        """解析 URL 匹配断点正则表达式的第一个脚本。"""
        import re#正则
        表达式=re.compile(模式)#编译
        for 路由 in 自身._路由.values():#扫路由
            if 表达式.search(路由['script']['url']):#命中
                return 路由#返回
        return None#未找到

    def 曾不支持(自身,脚本id):#是否曾不支持
        """测试一个已断连脚本是否属于无活动调试的 realm。"""
        return cdp字符串id(脚本id,'scriptId') in 自身._已退役不支持#查询

    def 移除realm(自身,realm):#移除realm
        """忘记一个已关闭 realm 的脚本，同时保留其不支持身份。"""
        for 脚本id in list(自身._路由.keys()):#扫路由
            路由=自身._路由[脚本id]#取路由
            if 路由['realm'] is not realm:#非本realm
                continue#跳过
            del 自身._路由[脚本id]#删除
            if 路由['realm'].debugger.get('state')=='unsupported':#不支持
                自身._已退役不支持.add(脚本id)#记不支持

    def 清空(自身):#清空
        """忘记全部脚本状态。"""
        自身._路由.clear()#清路由
        自身._已退役不支持.clear()#清退役
