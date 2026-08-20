"""框架中立的槽位与快照约定的 React 绑定库入口。

对齐上游 `@deepseek-ai/dsh-client-web-react`。公开面仅中文名。

上游导出 createSlotRenderer / SessionProvider / useInvoke 等 React 粘合；React/CSS 半按迁移政策跳过。本宿主面迁入快照选择器绑定契约与不变量配套。
"""
from .绑定 import 绑定快照选择器#再导出快照选择器绑定

__all__=['绑定快照选择器']#仅中文公开名
