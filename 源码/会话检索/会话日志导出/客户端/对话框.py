'页眉下载项和 /export 共用的状态对话框'
from ....客户端.模块.客户端.通告 import 取握手窗口
from ....客户端.ui_基础界面组件 import 按钮,模态#关闭按钮和对话框


class 会话日志下载对话框:
    '按这一会话显示准备中、已开始或失败'
    def __init__(自身,属性):
        '记下份额。由页眉调用渲染'
        自身.属性=属性#props
        自身.模态=模态()#共享对话框
        自身.根=None#当前节点

    def 更新(自身,属性):
        '换成这一次的份额'
        自身.属性=属性#最新

    def 渲染(自身):
        '打开时画出标题、说明和关闭。关着则没有节点'
        属性=自身.属性#这一次
        if 'window' in 属性:#调用方带了窗口
            窗口=属性['window']#用它
        else:#槽位份额里没有窗口
            窗口=取握手窗口()#当前页
        会话标识=属性['sessionId']#这一会话

        def 选出(状态):
            '这一会话的下载条目'
            return 状态['bySession'].get(str(会话标识))#没有则是 None

        条目=属性['useSessionLogDownload'](选出)#当前条目
        状态=None if 条目 is None else 条目.get('status')#阶段
        打开=条目 is not None and 条目.get('open') is True#是否开着
        错误=None#失败说明
        if 状态=='error':#失败才有说明
            原文=None if 条目 is None else 条目.get('error')#控制器写下的句子
            if 原文:#空串也走文案
                错误=原文#原句
            else:#没有句子
                错误='无法启动 Session 导出。'#中文表 dialog.commandFailed
        if 状态=='downloading':#准备中
            标题='正在导出 Session'#dialog.preparingTitle
            说明='正在准备包含当前 Session、子 Session 和附件的 ZIP 文件。'#dialog.preparingDescription
        elif 状态=='success':#已开始
            标题='Session 导出已开始下载'#dialog.successTitle
            说明='浏览器正在下载 Session ZIP 文件。'#dialog.successDescription
        else:#失败或还没有条目
            标题='Session 导出失败'#dialog.errorTitle
            说明=错误 if 错误 is not None else '无法启动 Session 导出。'#失败句或兜底

        def 关闭():
            '关掉对话框，不取消在途下载'
            属性['dismiss'](会话标识)#只关这一会话

        自身.模态.更新({#对话框份额
            'window':窗口,#页面
            'open':打开,#开合
            'onClose':关闭,#关
            'title':标题,#标题
            'description':说明,#说明
            'closeLabel':'关闭',#dialog.close
            'footer':按钮({'variant':'primary','onClick':关闭,'children':'关闭'}),#页脚同一句
        })
        自身.根=自身.模态.渲染()#关着则为 None
        return 自身.根#节点或 None


__all__=['会话日志下载对话框']
