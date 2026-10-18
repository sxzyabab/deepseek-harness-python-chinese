__all__=[]

#本文件对应上游 slot-contract。运行时没有值。
#别的插件用类型合并这份约定，经 slots 登记，运行时不导入本包。
#plugins.add.actions：添加菜单里安装项之后的行，业主 onDismiss。
#plugins.tab：已安装之后的页，label 与 order；业主 install、openPackage。
#plugins.bundle.activation：按包名，启用后的引导。
#plugins.item：官方插件卡片。view 为 summary 或 page。
#plugins.bundle.config：按包名，只画 page。
#plugins.row.config：键为 包名#行 id。
#plugins.detail.actions、plugins.detail.badge、plugins.detail.section：按打开页的 subject。
