import json#跨边界 JSON 往返
from copy import deepcopy as 深拷贝#普通对象拷贝

__all__=['是否插件','归一处理方法','包装沙箱插件','插件名','沙箱定义工具','沙箱登记工具']#仅中文公开名

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
        raise Exception(f'{路径} 必须是无损 JSON 数据（对象、数组、字符串、数字、布尔、null），不能是类实例、函数、Map/Set、Date 或 undefined。请返回由所需值组成的普通对象；调用方不需要返回值时用 `return null`。') from 错误#教学错误

def 归一处理方法(方法,函数):#归一 handle
    """方法名必须是非空字符串，处理函数必须是函数。"""
    if not isinstance(方法,str) or 方法=='':#方法名
        raise Exception('harness.handle(method, fn) 需要非空字符串方法名')#必须非空字符串
    if not callable(函数):#处理函数
        raise Exception(f'harness.handle("{方法}") 的第二个参数必须是处理函数')#第二参必须是函数
    def 处理(参数):#克隆返回
        """跨边界物化。"""
        return 克隆JSON(函数(参数),f'harness.handle("{方法}") result')#物化
    return {'method':方法,'handler':处理}#包装后的登记

def 沙箱定义工具(选项):#沙箱 defineTool 最小实现
    """打上动态工具标记；完整 schema 归一留给 tools 包。"""
    if not isinstance(选项,dict):#选项必须是对象
        raise Exception('harness.defineTool 的 options 必须是对象')#教学错误
    工具=深拷贝(选项)#拷贝
    工具[动态工具标记]=True#打标记
    return 工具#带标记的定义

def 沙箱登记工具(上下文,工具):#沙箱 registerTool
    """必须带标记。"""
    if not isinstance(工具,dict) or 工具.get(动态工具标记) is not True:#没有标记
        raise Exception('动态工具登记必须使用 harness.defineTool(...) 返回的工具')#必须走 defineTool
    return 上下文.tools.register(工具)#交给真实注册表

def 包装沙箱插件(插件,报告失败):#包装后的插件
    """包装插件，使 apply 拿到沙箱上下文门面（Python 侧：原样转发并捕获门面报告）。"""
    def 报告并抛(消息):#报告门面失败并抛出
        """同一份错误。"""
        错误=Exception(消息)#同一份错误
        报告失败(错误)#先报告
        raise 错误#再抛
    if callable(插件) and not isinstance(插件,dict):#函数插件
        def 应用(上下文,配置=None):#apply
            """把门面交给原函数（Python 侧暂用原上下文）。"""
            try:#调用
                return 插件(上下文,配置) if 配置 is not None else 插件(上下文)#原函数
            except Exception as 错误:#门面/运行失败
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
