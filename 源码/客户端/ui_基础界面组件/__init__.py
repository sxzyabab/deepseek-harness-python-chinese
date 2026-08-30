"""不依赖 Cordis 的 UI 基元库入口。

对齐上游 `@deepseek-ai/dsh-client-ui-primitives`。公开面仅中文名。
"""
from .头尾封顶 import 头尾封顶#头尾封顶算术
from .剪贴板 import 写剪贴板#剪贴板
from .复制反馈 import 复制反馈,复制反馈毫秒#复制反馈
from .锚定最大高度 import 锚定最大高度,锚定边距#底锚夹高
from .按钮 import 按钮,变体表,尺寸表#按钮
from .模态 import 模态#模态
from .菜单 import 菜单,是分隔,是标题#菜单
from .输入 import 输入#输入
from .胶囊 import 胶囊#胶囊
from .吐司 import 吐司,保持毫秒,淡出毫秒#吐司
from .提示泡 import 提示泡,侧表#提示泡
from .状态点 import 状态点,状态表,矩阵格#状态点
from .指针宽限 import 指针宽限,指针宽限毫秒#指针宽限
from .连接横幅 import 连接横幅,默认标签 as 连接默认标签#连接横幅
from .引导面 import 引导面#引导面
from .风险确认 import 风险确认#风险确认
from .披露行 import 披露行#披露行
from .悬停卡 import 悬停卡,默认打开延迟毫秒#悬停卡
from .差异块 import 差异块,默认差异最大行#差异块
from .检索块 import 检索块,默认检索最大行#检索块
from .读块 import 读块,默认读最大行#读块
from .网页块 import 网页块,安全链接,链接标签#网页块
from .终端块 import 终端块,默认终端最大行#终端块
from .ansi import 解析ansi行,净文本#ANSI
from .Json树 import Json树,默认标签 as Json树默认标签#Json 树
from .鱼标 import 鱼标#鱼标
from .品牌字标 import 品牌字标#品牌字标
from .markdown import 消息文本,代码块,json块,Markdown文本#markdown

__all__=[#仅中文公开名
    '头尾封顶','写剪贴板','复制反馈','复制反馈毫秒','锚定最大高度','锚定边距',
    '按钮','变体表','尺寸表','模态','菜单','是分隔','是标题','输入','胶囊',
    '吐司','保持毫秒','淡出毫秒','提示泡','侧表','状态点','状态表','矩阵格',
    '指针宽限','指针宽限毫秒','连接横幅','连接默认标签','引导面','风险确认',
    '披露行','悬停卡','默认打开延迟毫秒','差异块','默认差异最大行',
    '检索块','默认检索最大行','读块','默认读最大行','网页块','安全链接','链接标签',
    '终端块','默认终端最大行','解析ansi行','净文本','Json树','Json树默认标签',
    '鱼标','品牌字标','消息文本','代码块','json块','Markdown文本',
]#公开面结束
