
__all__=['侧栏槽名','侧栏子槽','侧栏词表命名空间']#仅中文公开名

侧栏槽名='sidebar'#侧栏槽名
侧栏词表命名空间='sidebar'#词表命名空间
侧栏子槽={#子槽：品牌、全局面板、工作区浏览区、设置、页脚动作
    'sidebar.brand.mark':{'kind':'single','scope':'root'},#品牌标记
    'sidebar.brand.name':{'kind':'single','scope':'root'},#品牌名
    'sidebar.panellist':{'kind':'list','scope':'root'},#全局面板列表
    'sidebar.workspaces':{'kind':'single','scope':'root'},#工作区浏览区
    'sidebar.settings':{'kind':'single','scope':'root'},#设置面
    'sidebar.footer.action':{'kind':'list','scope':'root'},#页脚动作
}#结束
