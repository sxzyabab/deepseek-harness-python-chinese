__all__=['加载中','就绪','不可用','空表单快照']

加载中='loading'#尚未接受节
就绪='ready'#已有接受节
不可用='unavailable'#未暴露或 memory

def 空表单快照(持久化):
    """host 先 loading；memory 不可写。"""
    return {#同步快照
        'status':加载中 if 持久化=='host' else 不可用,#初态
        'value':None,#尚未接受
        'base':None,#组合层
        'user':None,#用户层
        'revision':None,#尚无修订
        'writable':False,#memory 永不写
        'mode':持久化,#host 或 memory
    }
