'检查器自己的文档查找。只用已有的槽位和对话属性'

from ......客户端.模块.客户端.通告 import 取握手窗口

def 已显示(元素):
    '元素还在文档里，并且祖先没有被隐藏'
    if 元素 is None or not 元素.isConnected:#没挂上
        return False#不可见
    if 元素.closest('[hidden]') is not None:#自己或祖先标了 hidden
        return False#不可见
    窗口=取握手窗口()#当前页
    父=元素#从自己往上
    while 父 is not None:#还有祖先
        样式=窗口.getComputedStyle(父)#计算样式
        if 样式.display=='none' or 样式.visibility=='hidden':#不显示
            return False#不可见
        父=父.parentElement#上一层
    return True#看得到

def 主聊天根():
    '主对话的外层流列。侧栏和嵌套视图里的列不算'
    窗口=取握手窗口()#当前页
    文档=窗口.document#文档
    选择='[data-slot="main.conversation"] [data-slot="conversation.view"] [data-chat-flow]'#主区对话流
    for 元素 in 文档.querySelectorAll(选择):#每一个流列
        if 元素.closest('[data-sidebar-right-session], [data-step-process-body]') is not None:#侧栏或过程体
            continue#跳过
        if 已显示(元素):#当前看得到
            return 元素#主列
    return None#另一个视图正在显示

def 在聊天内(元素,根):
    '候选必须在这根列里，且属于同一块对话视图'
    if 元素 is None or 根 is None:#缺一边
        return False#不是
    if not 根.contains(元素):#不在这列里
        return False#不是
    if 元素.closest('[data-sidebar-right-session]') is not None:#跑进侧栏
        return False#不是
    return 元素.closest('[data-slot="conversation.view"]') is 根.closest('[data-slot="conversation.view"]')#同一块对话

def 查找聊天目标(根,目标列表):
    '按调用、节点、分组、回合收集候选，不改它们的显示状态'
    字段=('chatCallId','chatNodeKey','chatGroupKey','chatTurn')#属性到 dataset 名
    属性名={'chatCallId':'data-chat-call-id','chatNodeKey':'data-chat-node-key','chatGroupKey':'data-chat-group-key','chatTurn':'data-chat-turn'}#对应属性
    索引={名:{} for 名 in 字段}#值到元素列表
    选择='[data-chat-call-id], [data-chat-node-key], [data-chat-group-key], [data-chat-turn]'#带身份的元素
    for 元素 in 根.querySelectorAll(选择):#列里的候选
        if not 在聊天内(元素,根):#不属于这列
            continue#跳过
        for 名 in 字段:#四种身份
            值=元素.getAttribute(属性名[名])#属性值
            if 值 is None:#没有这种身份
                continue#下一种
            已有=索引[名].get(值)#同一值的元素
            if 已有 is None:#第一次
                索引[名][值]=[元素]#新建
            else:#已经有
                已有.append(元素)#接上
    找到=[]#按发现顺序去重
    见过=set()#元素身份

    def 加入(名,值,部位=None):
        '把这种身份下、部位相符的元素加进结果'
        if 值 is None:#没有这个值
            return#不加
        for 元素 in 索引[名].get(值) or []:#这个值的元素
            if 部位 is not None and 元素.getAttribute('data-chat-group-part')!=部位:#部位不同
                continue#跳过
            标识=id(元素)#元素身份
            if 标识 in 见过:#已经加过
                continue#不重复
            见过.add(标识)#记下
            找到.append(元素)#按第一次发现的顺序

    回合=set()#目标里出现过的回合
    优先回合=None#第一份带回合的目标
    for 目标 in 目标列表:#找优先回合
        if 目标.get('turn') is not None:#有回合
            优先回合=目标.get('turn')#用第一份
            break#停
    已加优先=False#优先回合是否已经插进去
    for 序号,目标 in enumerate(目标列表):#按偏好顺序
        if 序号>0 and 优先回合 is not None and 目标.get('turn')!=优先回合 and not 已加优先:#后面换成了别的回合
            加入('chatTurn',str(优先回合))#先补上优先回合
            已加优先=True#只补一次
        加入('chatCallId',目标.get('callId'))#调用
        加入('chatNodeKey',目标.get('nodeKey'),目标.get('groupPart'))#带部位的节点
        加入('chatNodeKey',目标.get('nodeKey'))#节点本身
        加入('chatCallId',目标.get('rootCallId'))#根调用
        加入('chatGroupKey',目标.get('groupKey'))#分组
        if 目标.get('turn') is not None:#有回合
            回合.add(目标.get('turn'))#记下来
    for 号 in 回合:#其余回合
        if not 已加优先 or 号!=优先回合:#还没作为优先回合加过
            加入('chatTurn',str(号))#回合上的元素
    return 找到#去重后的候选
