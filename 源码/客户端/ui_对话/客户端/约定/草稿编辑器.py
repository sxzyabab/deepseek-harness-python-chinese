__all__=[#公开面
    '裁决键','裁决结局','令牌跨度','引用插入','编辑选区','出现','撰写键盘',
]#公开面结束

裁决键=('up','down','enter','escape','tab')#弹出菜单拦截的键
裁决结局=('consumed','pick-highlighted','pass')#菜单键盘路由结局

#令牌跨度：start/end/draftRev，点选时由输入修订守卫
#引用插入：source/ref/label/clipboardText，可选 appearance=session|file|folder
#编辑选区：半开 [start, end) 探测坐标
#出现：occurrenceId/source/ref/offset/length/label/clipboardText，可选 appearance、invalid
#撰写键盘：snapshot/editor 与 submit/steerQueue/paste/caretSpan/arbitrate/space/dismissPopup/bindFilePicker

令牌跨度=dict#跨度形
引用插入=dict#插入形
编辑选区=dict#选区形
出现=dict#出现形
撰写键盘=dict#键盘面
