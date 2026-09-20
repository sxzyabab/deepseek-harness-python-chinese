"""进程域对 koffi 的首次访问。"""
from ...工具.惰性导入 import 创建惰性导入#成功结果缓存

__all__=('取koffi',)#仅中文公开名

取koffi=创建惰性导入('koffi',__file__)#首次 Win32 原生操作时加载
