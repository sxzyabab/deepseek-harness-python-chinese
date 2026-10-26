'宿主侧只让装载器能挂上浏览器包'
from . import 客户端

__all__=['客户端','名称','应用']

名称='ui-entry-customization'

def 应用():
    '宿主入口不增加行为'
    return None

name=名称
apply=应用
default=应用
