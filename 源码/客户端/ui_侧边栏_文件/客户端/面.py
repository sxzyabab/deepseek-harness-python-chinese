import re
import threading

__all__=[
    '已中止','创建列举','子路径','文件面',
]

#常量
#路径键统一用 `/`，先剥掉尾部分隔，避免 `a/` 与 `a` 分成两桶
_尾部分隔=re.compile(r'[/\\]+\Z')

#工具


def 已中止(信号):
    """无信号视为未中止。信号为 threading.Event。"""
    if 信号 is None:
        return False
    return 信号.is_set()


def 子路径(父,名):
    """子条目的绝对路径键。父路径分隔符不保留，一律用 `/` 拼接。"""
    return _尾部分隔.sub('',父)+'/'+名


def 创建列举(远程):
    """绑到一份 Remote。失败原样返回；成功只留 entries 与 truncated。"""

    def 列举(会话标识,路径,信号):
        """调用 list。远程须带 workspaceFiles.list。"""
        结果=远程.workspaceFiles.list(会话标识,路径,信号)
        if not 结果['ok']:
            return 结果
        值=结果['value']
        return {'ok':True,'value':{'entries':值['entries'],'truncated':值['truncated']}}

    return 列举


#
#同一级后发的请求覆盖先发的
def 文件面(列举):

    def 工厂(会话标识,动作):
        """构造 start / load / toggle。代次按标签再按路径计。"""
        代次表={}

        def 下一代(标签标识,路径):
            """推进该级代次。旧请求结算时对不上就丢弃。"""
            按路径=代次表[标签标识] if 标签标识 in 代次表 else {}
            代次表[标签标识]=按路径
            代次=(按路径[路径] if 路径 in 按路径 else 0)+1
            按路径[路径]=代次
            return 代次

        def 加载(标签标识,路径,信号):
            """把一级列进存储。记录已结束则不发请求。"""
            if 已中止(信号):
                return
            代次=下一代(标签标识,路径)
            动作['loading'](标签标识,路径)

            def 结算():
                """后台列举。代次失配或桶已忘则不写。"""
                结果=列举(会话标识,路径,信号)
                按路径=代次表[标签标识] if 标签标识 in 代次表 else None
                if 按路径 is None or (路径 not in 按路径) or 按路径[路径]!=代次:
                    return
                if 结果['ok']:
                    动作['loaded'](标签标识,路径,结果['value'])
                else:
                    动作['failed'](标签标识,路径,结果['error'])

            线=threading.Thread(target=结算,daemon=True,name='dsh-sidebar-files-list')
            线.start()

        def 启动(标签标识,根,信号):
            """播种本 tab 树并列举根。信号中止后清掉代次账并遗忘桶。"""
            动作['start'](标签标识,根)

            def 等待结算后清登记():
                """信号置位则清代次并遗忘桶。"""
                while not 已中止(信号):
                    信号.wait(0.05)
                if 标签标识 in 代次表:
                    del 代次表[标签标识]
                动作['forget'](标签标识)

            if 已中止(信号):
                if 标签标识 in 代次表:
                    del 代次表[标签标识]
                动作['forget'](标签标识)
            else:
                线=threading.Thread(target=等待结算后清登记,daemon=True,name='dsh-sidebar-files-abort')
                线.start()
            加载(标签标识,根,信号)

        def 切换(标签标识,路径,已加载,信号):
            """展开或折叠。首次打开才列举，已有内容不再请求。"""
            动作['toggled'](标签标识,路径)
            if not 已加载:
                加载(标签标识,路径,信号)

        return {
            'start':启动,
            'load':加载,
            'toggle':切换,
        }

    return 工厂
