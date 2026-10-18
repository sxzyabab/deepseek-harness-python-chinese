from .文案 import 中文,英文

__all__=['第一方定义','拼写别名','第一方命令名']

第一方定义={
    'goal':'@deepseek-ai/dsh-command-goal',
    'plan':'@deepseek-ai/dsh-plan-mode',
    'feedback':'@deepseek-ai/dsh-command-feedback',
    'compact':'@deepseek-ai/dsh-command-compact',
    'permission':'@deepseek-ai/dsh-permission-presets',
    'export':'@deepseek-ai/dsh-session-log-export',
}

拼写别名={}
for 名 in 第一方定义:
    拼写别名[中文['token.'+名]]=名
    拼写别名[英文['token.'+名]]=名

def 第一方命令名(描述符):
    '按 definitionId 认出第一方命令。对不上则 None'
    定义标识=描述符['definitionId'] if 'definitionId' in 描述符 else None
    for 名,包名 in 第一方定义.items():
        if 定义标识==包名:
            return 名
    return None
