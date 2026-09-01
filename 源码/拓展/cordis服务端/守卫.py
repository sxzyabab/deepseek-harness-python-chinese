"""沙箱宿主半与真实运行时之间的登记边界（Python 侧精简实现）。

对齐上游 `拓展/cordis-host-runner/src/guard.ts` 的公开面：isPlugin、normalizeHandler、guardedPlugin。
完整跨 realm JSON 克隆与 schema 归一在 Python 侧用 json 往返近似。
"""
import json#跨边界 JSON 往返
from copy import deepcopy as 深拷贝#普通对象拷贝

__all__=['是否插件','归一处理器','守卫插件','插件名','沙箱定义工具','沙箱登记工具']#仅中文公开名

动态工具标记='_cordis_dynamic_tool'#动态工具标记键

def 是否插件(值):#是否插件形态
    """函数，或带 apply 函数的对象。"""
    if callable(值) and not isinstance(值,type):#函数插件
        return True#是
    if isinstance(值,dict) and callable(值.get('apply')):#对象带 apply
        return True#是
    return hasattr(值,'apply') and callable(getattr(值,'apply',None))#对象属性 apply

def 插件名(插件):#插件显示名
    """其 name 属性，否则匿名。"""
    if isinstance(插件,dict):#映射
        名=插件.get('name')#可能的 name
    else:#对象
        名=getattr(插件,'name',None)#可能的 name
    if isinstance(名,str) and 名!='':#非空字符串
        return 名#用之
    return '<anonymous>'#否则匿名

def 克隆JSON(值,路径='value'):#跨边界 JSON 克隆
    """不允许非 JSON；失败抛教学错误。"""
    try:#往返
        return json.loads(json.dumps(值,ensure_ascii=False))#物化
    except (TypeError,ValueError) as 错误:#无法序列化
        raise Exception(f'{路径} must be lossless JSON data (objects, arrays, strings, numbers, booleans, null) — not a class instance, function, Map/Set, Date, or undefined. Return a plain object built from the values you need, or `return null` when the caller needs no value back.') from 错误#教学错误

def 归一处理器(方法,函数):#归一 handle
    """方法名必须是非空字符串，处理函数必须是函数。"""
    if not isinstance(方法,str) or 方法=='':#方法名
        raise Exception('harness.handle(method, fn) needs a non-empty string method name')#必须非空字符串
    if not callable(函数):#处理函数
        raise Exception(f'harness.handle("{方法}") needs a handler function as its second argument')#第二参必须是函数
    def 处理(参数):#克隆返回
        """跨边界物化。"""
        return 克隆JSON(函数(参数),f'harness.handle("{方法}") result')#物化
    return {'method':方法,'handler':处理}#包装后的登记

def 沙箱定义工具(选项):#沙箱 defineTool 最小实现
    """打上动态工具标记；完整 schema 归一留给 tools 包。"""
    if not isinstance(选项,dict):#选项必须是对象
        raise Exception('harness.defineTool options must be an object')#教学错误
    工具=深拷贝(选项)#拷贝
    工具[动态工具标记]=True#打标记
    return 工具#带标记的定义

def 沙箱登记工具(上下文,工具):#沙箱 registerTool
    """必须带标记。"""
    if not isinstance(工具,dict) or 工具.get(动态工具标记) is not True:#没有标记
        raise Exception('dynamic tool registration must use a tool returned by harness.defineTool(...)')#必须走 defineTool
    return 上下文.tools.register(工具)#交给真实注册表

def 守卫插件(插件,报告失败):#守卫后的插件
    """包装插件，使 apply 拿到沙箱上下文门面（Python 侧：原样转发并捕获守卫报告）。"""
    def 报告并抛(消息):#报告守卫失败并抛出
        """同一份错误。"""
        错误=Exception(消息)#同一份错误
        报告失败(错误)#先报告
        raise 错误#再抛
    if callable(插件) and not isinstance(插件,dict):#函数插件
        def 应用(上下文,配置=None):#apply
            """把门面交给原函数（Python 侧暂用原上下文）。"""
            try:#调用
                return 插件(上下文,配置) if 配置 is not None else 插件(上下文)#原函数
            except Exception as 错误:#守卫/运行失败
                报告失败(错误)#报告
                raise#再抛
        return {'name':插件名(插件),'apply':应用}#对象插件
    原应用=插件.get('apply') if isinstance(插件,dict) else getattr(插件,'apply',None)#原 apply
    def 应用(上下文,配置=None):#apply
        """把门面交给原 apply。"""
        try:#调用
            return 原应用(上下文,配置) if 配置 is not None else 原应用(上下文)#原 apply
        except Exception as 错误:#失败
            报告失败(错误)#报告
            raise#再抛
    if isinstance(插件,dict):#映射
        return {**插件,'apply':应用}#浅拷贝后换 apply
    return {'name':插件名(插件),'apply':应用,'inject':getattr(插件,'inject',None)}#对象包装
