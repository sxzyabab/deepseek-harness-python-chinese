__all__=['模型选择注入面']#仅中文公开名

#撰写器模型座位的注入业务面（字段名对齐上游 inject）
模型选择注入面={#注入业务面模板
    'available':False,#本会话是否支持 Agent 绑定的模型检视与选定
    'directory':None,#共享目录 store（与 /model 弹出层同一实例）
    'load':None,#刷新建议目录（发出即忘；错误落到 store）
    'select':None,#选定完整提供方/模型/推理；宿主是否接受
}#注入面结束
