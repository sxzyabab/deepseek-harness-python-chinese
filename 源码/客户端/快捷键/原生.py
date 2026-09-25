"""可信产品窗口与 Electron 顶层 preload 交换的输入。

桌面快捷键输入 dict 形：
- 共用：revision
- kind=='menu'：commandId
- kind in ('keyboard','iframe','webview')：frameName、code、可选 secondCode、
  control、alt、shift、meta、repeat

桌面键盘 API dict 形：
- subscribe(监听) -> 拆除器
- closeWindow(revision) -> None（同步完成）
"""

__all__=[]#纯约定模块，无运行时导出
