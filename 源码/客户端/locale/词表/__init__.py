"""公共命名空间词表对。中文是键集权威。



对齐上游 `locale/src/locales/index.ts`。公开面仅中文公开名。

"""

from .中文 import 中文#中文公共词表

from .英文 import 英文#英文公共词表

from .设置 import 设置中文,设置英文#设置行词表



__all__=['中文','英文','设置中文','设置英文']#仅中文公开名


