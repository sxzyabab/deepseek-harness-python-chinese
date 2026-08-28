"""模型选择座位的注入面。

对齐上游 `ui-model-selection/src/client/slots.ts`。公开面仅中文名。
目标槽位 `conversation.input.model` 由 ui-conversation 的 composer-bar 入口声明；本包只贡献这一条占用方，因此这里没有 SlotMap 合并。
"""

__all__=['模型选择注入面']#仅中文公开名

#撰写器模型座位的注入业务面（字段名对齐上游 inject）
模型选择注入面={#注入业务面模板
    'available':False,#本会话是否支持 Agent 绑定的模型检视与选定
    'directory':None,#共享目录 store（与 /model 弹出层同一实例）
    'load':None,#刷新建议目录（发出即忘；错误落到 store）
    'select':None,#选定完整提供方/模型/推理；宿主是否接受
}#注入面结束
