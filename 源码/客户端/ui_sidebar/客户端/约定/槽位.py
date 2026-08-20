"""侧栏槽位约定：根注入面与子槽声明形状。

对齐上游 `ui-sidebar/src/client/contract/slots.ts` 的可序列化约定面。
公开面仅中文名。根组件见 `侧栏根.py`。
"""

__all__=['侧栏槽名','侧栏子槽','侧栏词表命名空间']#仅中文公开名

侧栏槽名='sidebar'#侧栏槽名
侧栏词表命名空间='sidebar'#词表命名空间
侧栏子槽={#子槽：工作区浏览区、设置、页脚动作
    'sidebar.workspaces':{'kind':'single','scope':'root'},#工作区浏览区
    'sidebar.settings':{'kind':'single','scope':'root'},#设置面
    'sidebar.footer.action':{'kind':'list','scope':'root'},#页脚动作
}#结束
