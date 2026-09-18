__all__=['装载文案','短名','包文案','提示文案']#仅中文公开名

内置文案={#官方包精确 npm 名 → 文案键与 beta
    '@deepseek-ai/dsh-experimental-agent-team-profile':{'title':'builtinAgentTeamTitle','description':'builtinAgentTeamDescription','beta':True},
    '@deepseek-ai/dsh-experimental-agent-team-web-profile':{'title':'builtinAgentTeamWebTitle','description':'builtinAgentTeamWebDescription','beta':True},
    '@deepseek-ai/dsh-experimental-auto-review':{'title':'builtinAutoReviewTitle','description':'builtinAutoReviewDescription','beta':True},
}#内置结束

拒码键={#Host 拒因码 → 文案键
    'management-required':'reasonManagementRequired',
    'unaddressable':'reasonUnaddressable',
    'unknown-plugin':'reasonUnknownPlugin',
    'invalid-spec':'reasonInvalidSpec',
    'ambiguous-install':'reasonAmbiguousInstall',
    'not-bundle':'reasonNotBundle',
    'not-removable':'reasonNotRemovable',
    'stop-profile':'reasonStopProfile',
    'bundle-in-use':'reasonBundleInUse',
    'stale-approval':'reasonStaleApproval',
    'operation-error':'reasonOperationError',
}#拒码结束

失败键={#失败动作 → 文案键
    'enable':'failedEnable',
    'disable':'failedDisable',
    'uninstall':'failedUninstall',
    'rowEnable':'failedRowEnable',
    'rowDisable':'failedRowDisable',
}#失败结束

def 装载文案(错误,翻译):
    """管理错误读作：码对应句，或操作错误时 Host 诊断原样。"""
    if 错误['code']!='operation-error':#非操作错误
        return 翻译(拒码键[错误['code']])#码句
    诊断=错误['diagnostic'] if 'diagnostic' in 错误 else None#诊断
    if 诊断 is None or 诊断=='':#无诊断
        return 翻译('reasonOperationError')#通用
    return 诊断#原样

def 短名(名称):
    """压缩包名为人读短名。"""
    去作用域=名称[名称.index('/')+1:] if 名称.startswith('@') else 名称#去作用域
    if 去作用域.startswith('dsh-host-'):#宿主前缀
        return 去作用域[9:]#去
    if 去作用域.startswith('dsh-client-'):#客户端前缀
        return 去作用域[11:]#去
    if 去作用域.startswith('dsh-'):#通用
        return 去作用域[4:]#去
    return 去作用域#原样

def 包文案(包,翻译):
    """渲染时按精确 npm 名本地化已知官方包。"""
    键=内置文案[包['name']] if 包['name'] in 内置文案 else None#键
    if 键 is None:#未知
        描述=包['description'] if 'description' in 包 else None#描述
        return {'title':短名(包['name']),'description':描述,'beta':False}#短名
    return {'title':翻译(键['title']),'description':翻译(键['description']),'beta':键['beta']}#本地化

def 提示文案(提示,翻译):
    """一条提示读作的句子。"""
    种=提示['kind']#种类
    if 种=='restart':#重启
        return 翻译('restartNotice')#句
    if 种=='overridden':#覆盖
        return 翻译('overriddenNotice',{'name':提示['packageName']})#句
    if 种=='cancelled':#取消
        return 翻译('installCancelled')#句
    原因=装载文案({'code':提示['code'],'diagnostic':提示['reason']},翻译) if 'code' in 提示 else 提示['reason']#原因
    if 原因=='':#空
        原因=翻译('reasonOperationError')#通用
    return 翻译(失败键[提示['action']],{'reason':原因})#失败句
