def 渲染会话区域(绑定,属性):
    '没有会话键时调用空分支，有键时返回调用方给的子树'
    if 绑定['key'] is None:#没有选中会话
        空=None#默认没有空分支
        if 'empty' in 属性:#调用方给了空分支
            空=属性['empty']#记下
        if 空 is None:#没有空分支
            return None#空
        结果=空()#调用空分支
        if 结果 is None:#空分支没有节点
            return None#空
        return 结果#空分支的节点
    return 属性['children']#选中会话的子树
