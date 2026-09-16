__all__=['省略最旧图片']#仅中文公开名

def 省略最旧图片(会话,源事件序号表,张数):#按请求顺序省略最旧保留出现
    """记下一次省略最旧保留输入图片出现的决定。助手节点排除。返回是否还有可省略出现。"""
    目标表=[]#选中目标
    剩余=张数#还需省略张数
    for 序号 in 源事件序号表:#按请求顺序
        if 剩余==0:#已够
            break#停
        事件=会话.events[序号]#按下标取事件
        类型=事件['type']#事件类型
        if 类型!='user/message' and 类型!='tool/result':#只看输入节点
            continue#跳过
        消息=会话.派生事件消息(事件)#派生消息
        图片下标表=[]#本消息选中下标
        图片下标=0#深度优先计数
        def 访问(块列表):#深度优先选图
            """在块树里选出未省略图片。"""
            nonlocal 剩余,图片下标#改外层计数
            for 块 in 块列表:#逐块
                if 剩余==0:#已够
                    break#停
                if 块['type']=='image':#图片块
                    if 'offloaded' not in 块 or 块['offloaded'] is not True:#尚未省略
                        图片下标表.append(图片下标)#选中
                        剩余-=1#少一张
                    图片下标+=1#计数所有出现
                elif 块['type']=='tool-result':#嵌套
                    访问(块['content'])#递归
        访问(消息['content'])#走内容
        if len(图片下标表)>0:#本消息有选中
            目标表.append({'seq':序号,'imageIndexes':图片下标表})#记下
    if len(目标表)==0:#无可省略
        return False#没有进展
    会话.追加('image/offload',{'targets':目标表})#耐久决定
    return True#有省略
