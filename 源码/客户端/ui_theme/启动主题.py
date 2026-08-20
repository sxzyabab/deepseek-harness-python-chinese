"""宿主渲染的主题引导，覆盖浏览器插件树尚未激活的间隔。

每次 index 响应都嵌入当前持久化的内置偏好；浏览器只解析 `system`，
然后写入与客户端插件树激活后 ui-layout 的 ThemePresenter 所拥有的相同 DOM 字段。

对齐上游 `ui-theme/src/boot-theme.ts`。公开面仅中文名。
"""
import json,re#JSON 嵌入与开 body 定位
from .主题设置 import 默认偏好#默认跟随系统

__all__=['注入启动主题']#仅中文公开名

开体标签=re.compile(r'<body(?:\s[^>]*)?>',re.I)#定位开 body 标签

def 启动主题脚本(偏好):#按偏好拼立即执行脚本
    """为一条已经过模式校验的内置偏好生成内联脚本。"""
    return (#立即执行，避免污染全局
        '<script>(() => {'#开脚本
        +'const preference = '+json.dumps(偏好,ensure_ascii=False)+';'#嵌入当前内置偏好
        +'const systemDark = preference === \'system\''#偏好为跟随系统
        +' && typeof matchMedia !== \'undefined\''#且存在 matchMedia
        +' && matchMedia(\'(prefers-color-scheme: dark)\').matches;'#且系统为暗色
        +'const dark = preference === \'dark\' || systemDark;'#显式暗色或系统暗色
        +'document.documentElement.style.colorScheme = dark ? \'dark\' : \'light\';'#根节点配色方案
        +'document.body.toggleAttribute(\'data-ds-dark-theme\', dark);'#同步 body 暗色属性
        +'})()</script>'#内联 IIFE
    )#脚本结束

def 注入启动主题(网页,偏好=None):#把引导脚本插入 index HTML
    """把主题引导立刻插在开 body 标签之后、外壳挂载与模块脚本之前。无 body 的片段接到末尾。"""
    if 偏好 is None:#缺省用默认
        偏好=默认偏好#跟随系统
    脚本=启动主题脚本(偏好)#按偏好生成内联脚本
    命中=开体标签.search(网页)#定位开 body 标签
    if 命中 is None:#无 body 则追加到末尾
        return 网页+脚本#追加
    位置=命中.end()#开标签之后的插入点
    return 网页[:位置]+脚本+网页[位置:]#紧挨开 body 后插入
