"""生效宿主目录上的命令身份与本地化输入拼写。

对齐上游 `ui-commands/src/client/resolution.ts`。公开面仅中文名。
描述符为跨包 dict；线协议包名原样英文。
"""
from .文案 import 中文,英文#中英权威词条

__all__=['第一方命令名','认领令牌','解析命令']#仅中文公开名

第一方定义={#第一方名 → 定义 id（包名，不译）
    'goal':'@deepseek-ai/dsh-command-goal',#目标命令包
    'plan':'@deepseek-ai/dsh-plan-mode',#计划模式包
    'feedback':'@deepseek-ai/dsh-command-feedback',#反馈命令包
    'compact':'@deepseek-ai/dsh-command-compact',#压缩命令包
    'permission':'@deepseek-ai/dsh-permission-presets',#权限预设包
    'export':'@deepseek-ai/dsh-session-log-export',#会话日志导出包
}#第一方定义结束

拼写别名={}#token → 第一方名
for 名 in 第一方定义:#每个第一方名
    拼写别名[中文['token.'+名]]=名#中文 token
    拼写别名[英文['token.'+名]]=名#英文 token

def 第一方命令名(描述符):
    """识别第一方定义，不解读展示文案。描述符为 dict。"""
    定义标识=描述符['definitionId'] if 'definitionId' in 描述符 else None#定义 id
    for 名,包名 in 第一方定义.items():#逐第一方
        if 定义标识==包名:#精确匹配
            return 名#第一方名
    return None#其它定义

def 认领令牌(描述符,翻译):
    """菜单点选的输入拼写。已知定义用本地化 token，否则用登记名。"""
    名=第一方命令名(描述符)#第一方名
    if 名 is None:#未知
        return 描述符['name']#登记名
    return 翻译('token.'+名)#译 token

def 解析命令(拼写,描述符表):
    """键入拼写对照当前会话生效定义。精确名优先；别名按 definitionId。"""
    for 描述符 in 描述符表:#先精确名
        if 描述符['name']==拼写:#命中
            return 描述符#描述符
    if 拼写 not in 拼写别名:#不是别名
        return None#缺席
    名=拼写别名[拼写]#第一方名
    包名=第一方定义[名]#定义 id
    for 描述符 in 描述符表:#按 definitionId
        if ('definitionId' in 描述符) and 描述符['definitionId']==包名:#命中
            return 描述符#描述符
    return None#目录里没有该第一方定义
