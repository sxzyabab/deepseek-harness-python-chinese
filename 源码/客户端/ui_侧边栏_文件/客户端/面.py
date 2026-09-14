import re#去尾分隔符
import threading#列举线程与中止监视

__all__=[#仅中文公开名
    '已中止','创建列举','子路径','文件面',
]#公开面结束

_尾部分隔=re.compile(r'[/\\]+\Z')#去掉路径尾部分隔符


def 已中止(信号):
    """信号是否已中止。无信号视为未中止。信号为 threading.Event。"""
    if 信号 is None:#无
        return False#未中止
    return 信号.is_set()#Event 置位


def 子路径(父,名):
    """子条目的绝对路径键。

    无论父用何种分隔符都用 `/` 拼接：宿主接受混用，树只需稳定键。
    """
    return _尾部分隔.sub('',父)+'/'+名#拼接


def 创建列举(远程):
    """把列举绑到一份 Remote 面，只保留树所存的 entries / truncated。

    远程须带 `workspaceFiles.list`；返回 (会话标识, 路径, 信号) → RemoteResult dict。
    """

    def 列举(会话标识,路径,信号):
        """调用 list；失败原样透传；成功只留条目与截断标志。"""
        结果=远程.workspaceFiles.list(会话标识,路径,信号)#RemoteResult
        if not 结果['ok']:#失败
            return 结果#透传
        值=结果['value']#目录列举
        return {'ok':True,'value':{'entries':值['entries'],'truncated':值['truncated']}}#瘦身

    return 列举#绑定列举


def 文件面(列举):
    """把树的面绑到一份目录列举。

    返回槽位 `inject` 工厂：会话标识与已绑定动作进，注入面出。
    """

    def 工厂(会话标识,动作):
        """构造 start / load / toggle。"""
        代次表={}#标签标识 → {路径 → 代次}；最新请求胜出

        def 下一代(标签标识,路径):
            """推进该级代次并返回新值。"""
            按路径=代次表[标签标识] if 标签标识 in 代次表 else {}#取或空
            代次表[标签标识]=按路径#挂回
            代次=(按路径[路径] if 路径 in 按路径 else 0)+1#加一
            按路径[路径]=代次#记下
            return 代次#新代

        def 加载(标签标识,路径,信号):
            """把一级列进存储；已中止则不发。"""
            if 已中止(信号):#记录已结束
                return#停
            代次=下一代(标签标识,路径)#本请求代次
            动作['loading'](标签标识,路径)#先标加载中

            def 结算():
                """后台列举；代次失配或桶已忘则不写。"""
                结果=列举(会话标识,路径,信号)#同步列举
                按路径=代次表[标签标识] if 标签标识 in 代次表 else None#仍存活？
                if 按路径 is None or (路径 not in 按路径) or 按路径[路径]!=代次:#已过期
                    return#丢弃
                if 结果['ok']:#成功
                    动作['loaded'](标签标识,路径,结果['value'])#写入就绪
                else:#失败；跨包 RemoteFailure 为 dict
                    动作['failed'](标签标识,路径,结果['error'])#写入失败

            线=threading.Thread(target=结算,daemon=True,name='dsh-sidebar-files-list')#守护线程
            线.start()#启动

        def 启动(标签标识,根,信号):
            """播种本 tab 树并列举根；信号中止时遗忘。"""
            动作['start'](标签标识,根)#播种

            def 等待结算后清登记():
                """信号置位则清代次并遗忘桶。"""
                while not 已中止(信号):#未中止
                    信号.wait(0.05)#短等
                if 标签标识 in 代次表:#仍有账
                    del 代次表[标签标识]#忘掉代次
                动作['forget'](标签标识)#忘掉桶

            if 已中止(信号):#已结束则立刻遗忘
                if 标签标识 in 代次表:#有账
                    del 代次表[标签标识]#清
                动作['forget'](标签标识)#忘
            else:#监视一次
                线=threading.Thread(target=等待结算后清登记,daemon=True,name='dsh-sidebar-files-abort')#等待结算后清登记
                线.start()#启动
            加载(标签标识,根,信号)#列根

        def 切换(标签标识,路径,已加载,信号):
            """展开或折叠；首次打开时列举。"""
            动作['toggled'](标签标识,路径)#改展开
            if not 已加载:#尚无状态
                加载(标签标识,路径,信号)#列举

        return {#注入面
            'start':启动,#播种并列根
            'load':加载,#列一级
            'toggle':切换,#展开/折叠
        }#面结束

    return 工厂#inject 工厂
