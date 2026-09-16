from ...依赖.schemastery import 字符串字段,列表字段,数字字段,布尔字段,整数字段,复合类型字段#配置字段
from ...计算机操作.计算机操作.标识构造 import 计算机操作提供方名#提供方名
from ...mcp import mcp客户端#MCP 客户端

__all__=['名称','注入','配置','应用']#仅中文公开名

名称='experimental-computer-use-cua-driver-mcp'#插件名
注入=['computerUse','tools']#依赖

配置=复合类型字段({#可执行与重连
    'command':字符串字段(默认值='cua-driver'),#命令
    'args':列表字段(字符串字段(),默认值=['mcp']),#参数
    'toolCallTimeoutMs':数字字段(最小=1),#超时
    'reconnect':复合类型字段({#重连
        'enabled':布尔字段(),#启用
        'initialDelayMs':数字字段(最小=1),#初延迟
        'maxDelayMs':数字字段(最小=1),#上限
        'maxAttempts':整数字段(最小=1),#次数
    }),#重连结束
})#配置结束

def 应用(上下文,配置值):#占用计算机操作并激活 MCP
    """初始连接或发现失败拒绝激活并回滚。"""
    连接={#stdio 客户端
        'command':配置值['command'],#命令
        'args':配置值['args'],#参数
        'reconnect':配置值['reconnect'],#重连
        'transport':'stdio',#传输
        'serverName':'cua-driver-mcp',#命名空间
        'failOnStartupError':True,#启动失败致命
    }#连接
    if 配置值.get('toolCallTimeoutMs') is not None:#超时
        连接['toolCallTimeoutMs']=配置值['toolCallTimeoutMs']#超时
    子=None#光纤
    def 连接寿命():#先关子再放登记
        """同一 effect 保序。"""
        nonlocal 子#改
        撤销=上下文.computerUse.登记(计算机操作提供方名('cua-driver-mcp'))#占用
        子=上下文.启动插件(mcp客户端,连接)#子插件
        def 卸():#拆除
            """先子后登记。"""
            if hasattr(子,'dispose'):#光纤
                子.dispose()#拆
            撤销()#放
        return 卸#拆除器
    上下文.副作用(连接寿命,'computer-use-cua-driver-mcp.connection')#寿命
    if 子 is not None and hasattr(子,'await'):#等激活
        子.await()#等
    elif 子 is not None and hasattr(子,'等待'):#中文
        子.等待()#等

name=名称#框架槽
inject=注入#框架槽
apply=应用#框架槽
Config=配置#框架槽
