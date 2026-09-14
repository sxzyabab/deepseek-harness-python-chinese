__all__=['槽名输入叠层','输入叠层槽形','菜单视图注入']#仅中文公开名

槽名输入叠层='conversation.input.overlay'#输入栏浮动叠层列表槽

#输入叠层槽形：InputBar 浮动叠层锚点
#MenuView（本包）与 popupSelect 壳（ui-commands）贡献列表条目
输入叠层槽形={'kind':'list','scope':'session'}#叠层槽声明形

#菜单视图注入：MenuView 叠层条目的注入业务面（文案走标准 locale 席）
#字段 menu（服务的菜单状态 store，只读订阅）
#方法 onPick(source,index) / onDismiss()
菜单视图注入=dict#菜单视图注入面形
