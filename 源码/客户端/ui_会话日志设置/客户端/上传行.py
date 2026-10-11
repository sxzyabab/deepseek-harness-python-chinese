'通用设置里的上传行，以及关掉设置后仍在的提示'

__all__=['上传行','上传提示']

class 上传行:
    '画出已接受的 API 上传状态'
    def __init__(自身,属性):
        '记下设置钩子、写入器和文案'
        自身.属性=属性

    def 快照(自身):
        '当前行要画的开关状态'
        上传=自身.属性['useUpload'](lambda 值:值)
        忙=自身.属性['useMutation'](lambda 值:值['busy'])
        return {
            '标题':自身.属性['t']('title'),
            '说明':自身.属性['t']('description'),
            '选中':(上传.get('value') or {}).get('enabled') is True if isinstance(上传,dict) else False,
            '禁用':忙 or (上传.get('status') if isinstance(上传,dict) else None)!='ready' or not (上传.get('writable') if isinstance(上传,dict) else False),
        }

    def 切换(自身,启用):
        '把开关交给写入器'
        自身.属性['setEnabled'](启用)

class 上传提示:
    '设置关掉后仍显示保存结果'
    def __init__(自身,属性):
        '记下变更钩子、关掉回调和文案'
        自身.属性=属性

    def 快照(自身):
        '没有提示时为空'
        状态=自身.属性['useMutation'](lambda 值:值)
        if 状态['notice'] is None:
            return None
        结果={'文本':自身.属性['t'](状态['notice']),'序号':状态['sequence'],'关掉':自身.属性['dismiss']}
        if 状态['notice']=='saved':
            结果['语气']='success'
        return 结果
