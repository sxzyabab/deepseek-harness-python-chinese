"""可持久化工具事件词汇，供仅类型消费方共享。对齐上游 `tools/src/types.ts`。公开面仅中文名；事件名与字段键保持上游字面量。"""

__all__=(
    '代码派发开始','代码派发落定','派发开始字段','派发落定字段',
)#仅中文公开名

代码派发开始='tool/code-dispatch-start'#子派发开始事件名
代码派发落定='tool/code-dispatch'#子派发落定事件名
派发开始字段=('rootCallId','parentCallId','subCallId','name','arguments')#开始载荷字段键
派发落定字段=('rootCallId','parentCallId','subCallId','name','arguments','isError','content')#落定载荷字段键
