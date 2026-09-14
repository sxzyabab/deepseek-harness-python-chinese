__all__=(
    'PTC派发开始','PTC派发落定','派发开始字段','派发落定字段',
)#仅中文公开名

PTC派发开始='tool/ptc-dispatch-start'#子派发开始事件名
PTC派发落定='tool/ptc-dispatch'#子派发落定事件名
派发开始字段=('rootCallId','parentCallId','subCallId','name','arguments')#开始载荷字段键
派发落定字段=('rootCallId','parentCallId','subCallId','name','arguments','isError','content')#落定载荷字段键
