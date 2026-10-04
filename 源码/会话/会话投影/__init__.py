'会话投影注册表服务'
from .异常 import 会话投影错误#本包异常
from .注册表 import 会话投影注册表#注册表实现
from .类型 import 会话投影映射,会话投影状态映射#类型表
__all__=[
    '包名','名称','默认','会话投影注册表','会话投影错误','会话投影映射','会话投影状态映射',
]
包名='@deepseek-ai/dsh-session-projection'
名称='session-projection'

默认=会话投影注册表
name=名称#框架槽
default=默认#框架槽
