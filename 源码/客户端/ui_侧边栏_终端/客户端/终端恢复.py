__all__=['终端恢复']#仅中文公开名

class 终端恢复:#会话头恢复
    """显示 Session 时恢复终端；失败给重试。"""
    def __init__(自身,属性):#记下合成 props
        """记下 props 并立刻恢复。"""
        自身.属性=属性#合成
        自身.错误=None#错误消息
        自身.尝试=0#重试计数
        自身.存活=True#实例存活
        自身.恢复()#首轮

    def 更新(自身,属性):#props 变更
        """刷新合成 props。"""
        自身.属性=属性#最新

    def 卸载(自身):#卸载
        """标死。"""
        自身.存活=False#死

    def 恢复(自身):#调用 restore
        """失败记下英文 message。"""
        try:#调用
            自身.属性['restore']()#恢复
            if 自身.存活:#仍活
                自身.错误=None#清错
        except Exception as 错误:#失败
            if not 自身.存活:#已死
                return#丢弃
            自身.错误=str(错误)#消息

    def 重试(自身):#按钮
        """清错再恢复。"""
        自身.错误=None#清
        自身.尝试+=1#计数
        自身.恢复()#再来

    def 视图(自身):#投影
        """成功无节点；失败为重试按钮。"""
        if 自身.错误 is None:#无错
            return None#空
        翻译=自身.属性['t']#文案
        return {#按钮
            'tag':'button',#按钮
            'type':'button',#类型
            'title':翻译('recoveryFailed',{'message':自身.错误}),#提示
            'onClick':自身.重试,#重试
            'text':翻译('retryRecovery'),#文案
        }#结束

    def __call__(自身,属性=None):#组件调用
        """对齐 React 组件调用。"""
        if 属性 is not None:#有新 props
            自身.更新(属性)#刷新
        return 自身.视图()#视图
