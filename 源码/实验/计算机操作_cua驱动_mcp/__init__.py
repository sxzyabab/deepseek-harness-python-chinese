from ...依赖.schemastery import 字符串字段,列表字段,数字字段,布尔字段,整数字段,复合类型字段
from ...计算机操作.计算机操作.标识构造 import 计算机操作提供方名
from ...mcp import mcp客户端

__all__=['名称','依赖','配置','应用']

名称='experimental-computer-use-cua-driver-mcp'
依赖=['computerUse','tools']

配置=复合类型字段({
    'command':字符串字段(默认值='cua-driver'),
    'args':列表字段(字符串字段(),默认值=['mcp']),
    'toolCallTimeoutMs':数字字段(最小=1),
    'reconnect':复合类型字段({
        'enabled':布尔字段(),
        'initialDelayMs':数字字段(最小=1),
        'maxDelayMs':数字字段(最小=1),
        'maxAttempts':整数字段(最小=1),
    }),
})

def 应用(上下文,配置值):
    """初始连接或发现失败拒绝激活并回滚。"""
    连接={
        'command':配置值['command'],
        'args':配置值['args'],
        'reconnect':配置值['reconnect'],
        'transport':'stdio',
        'serverName':'cua-driver-mcp',
        'failOnStartupError':True,
    }
    if 配置值.get('toolCallTimeoutMs') is not None:
        连接['toolCallTimeoutMs']=配置值['toolCallTimeoutMs']
    子=None
    def 连接寿命():
        """同一 effect 保序。"""
        nonlocal 子
        撤销=上下文.computerUse.登记(计算机操作提供方名('cua-driver-mcp'))
        子=上下文.启动插件(mcp客户端,连接)
        def 卸():
            """先子后登记。"""
            if hasattr(子,'dispose'):
                子.dispose()
            撤销()
        return 卸
    上下文.副作用(连接寿命,'computer-use-cua-driver-mcp.connection')
    if 子 is not None and hasattr(子,'等待'):
        子.等待()

name=名称
inject=依赖
apply=应用
Config=配置
