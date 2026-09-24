__all__=['槽名产出文件动作','槽名审阅文件动作','文件动作属主']

槽名产出文件动作='deliverables.file.actions'#经会话事件坐标打开一份文件
槽名审阅文件动作='deliverables.review.file.actions'#改动审阅标签上的同一套动作
文件动作属主={#属主份额
    'actionUrl':'',#已认证文档相对动作路由
    'available':False,
    'pending':False,
    'onAction':None,#执行所选原生动作并在文件面上发布状态
}
