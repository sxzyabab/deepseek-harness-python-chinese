'插件管理的显示句。界面只取中文表'
import urllib.parse
from .文案 import 中文句

__all__=['取中文','注册表文案对','管理文案','包文案','行文案','重启文案','提示文案']

注册表名称={
    'registry.npmmirror.com':'registryNpmmirror',
}
官方npm主机='registry.npmjs.org'
拒码键={
    'management-required':'reasonManagementRequired',
    'unaddressable':'reasonUnaddressable',
    'unknown-plugin':'reasonUnknownPlugin',
    'invalid-spec':'reasonInvalidSpec',
    'already-installed':'reasonAlreadyInstalled',
    'ambiguous-install':'reasonAmbiguousInstall',
    'not-bundle':'reasonNotBundle',
    'not-removable':'reasonNotRemovable',
    'stop-profile':'reasonStopProfile',
    'bundle-in-use':'reasonBundleInUse',
    'stale-approval':'reasonStaleApproval',
    'incompatible-version':'reasonIncompatibleVersionUnnamed',
    'operation-error':'reasonOperationError',
}
失败键={
    'enable':'failedEnable',
    'disable':'failedDisable',
    'uninstall':'failedUninstall',
    'rowEnable':'failedRowEnable',
    'rowDisable':'failedRowDisable',
}
重启原因键={
    'no-hmr':'restartReasonNoHmr',
    'package-moved':'restartReasonPackageMoved',
    'host-module':'restartReasonHostModule',
    'unmanaged-plugin':'restartReasonUnmanagedPlugin',
    'module-comparison':'restartReasonModuleComparison',
}
安装结果键={
    'done':'installBackgroundDone',
    'failed':'installBackgroundFailed',
    'unconfirmed':'installBackgroundUnconfirmed',
    'applying':'installBackgroundApplying',
    'unknown':'installBackgroundUnknown',
}

def 取中文(文本):
    '本地化对象取 zh。字符串原样。不读英文'
    if isinstance(文本,str):
        return 文本
    if isinstance(文本,dict) and isinstance(文本.get('zh'),str):
        return 文本['zh']
    return ''

def 注册表文案对(注册表,已解析):
    '官方源按名，已知镜像按名，其余按主机。pnpm 自有配置读它所命名的地址'
    网址=已解析 if 注册表 is None else 注册表
    if 网址 is None:
        return {'name':中文句('registryDefault'),'host':官方npm主机}
    try:
        解析=urllib.parse.urlparse(网址)
        主机=解析.hostname or 网址
        if 解析.port is not None:
            主机=主机+':'+str(解析.port)
    except ValueError:
        主机=网址
    if 主机==官方npm主机:
        键='registryOfficial'
    else:
        键=注册表名称.get(主机)
    名称=主机 if 键 is None else 中文句(键)
    return {'name':名称,'host':主机}

def 管理文案(错误):
    '拒码对应的中文句。不兼容时逐包一句再加补救。操作错误优先用 Host 诊断'
    if 错误['code']=='incompatible-version':
        点名=错误['incompatible'] if 'incompatible' in 错误 and 错误['incompatible'] is not None else []
        if len(点名)==0:
            句列=[中文句('reasonIncompatibleVersionUnnamed')]
        else:
            句列=[]
            for 插件 in 点名:
                要求=[]
                for 名,范围 in 插件['requirements'].items():
                    要求.append(名+' '+范围)
                句列.append(中文句('reasonIncompatibleVersion',{
                    'plugin':插件['name']+'@'+插件['version'],
                    'runtime':插件['runtimeVersion'],
                    'requirements':', '.join(要求),
                }))
        补救='reasonIncompatibleInstall' if 错误.get('installing') is True else 'reasonIncompatibleInstalled'
        return 中文句('sentenceSeparator').join(句列+[中文句(补救)])
    if 错误['code']!='operation-error':
        return 中文句(拒码键[错误['code']])
    诊断=错误.get('diagnostic')
    if 诊断 is None or 诊断=='':
        return 中文句('reasonOperationError')
    return 诊断

def 包文案(包,解析文本):
    '包的显示名、说明，以及是否实验包。技术名不变'
    元=包.get('meta')
    标题=包['name'] if 元 is None or 元.get('title') is None else 解析文本(元['title'])
    说明=None
    if 元 is not None and 元.get('description') is not None:
        解析=解析文本(元['description'])
        if 解析!='':
            说明=解析
    return {
        'title':标题,
        'description':说明,
        'beta':包['name'].startswith('@deepseek-ai/dsh-experimental-'),
    }

def 行文案(行,解析文本):
    '行的显示名和说明。没有标题时用完整模块名'
    元=行.get('meta')
    标题=行['moduleName'] if 元 is None or 元.get('title') is None else 解析文本(元['title'])
    说明=None
    if 元 is not None and 元.get('description') is not None:
        解析=解析文本(元['description'])
        if 解析!='':
            说明=解析
    return {'title':标题,'description':说明}

def 重启文案(键,原因):
    '重启提示带上原因。Host 没给原因时仍要求重启'
    原因句='' if 原因 is None else 中文句(重启原因键[原因])
    return 中文句(键,{'reason':原因句}).rstrip()

def 提示文案(提示):
    '一条提示对应的中文句'
    种类=提示['kind']
    if 种类=='restart':
        return 重启文案('restartNotice',提示.get('reason'))
    if 种类=='overridden':
        return 中文句('overriddenNotice',{'name':提示['packageName']})
    if 种类=='cancelled':
        return 中文句('installCancelled')
    if 种类=='refresh-failed':
        return 中文句('refreshError')
    if 种类=='install':
        return 中文句(安装结果键[提示['outcome']])
    if 提示.get('code') is None:
        原因=提示['reason']
    else:
        错误={'code':提示['code'],'diagnostic':提示['reason']}
        if 'incompatible' in 提示 and 提示['incompatible'] is not None:
            错误['incompatible']=提示['incompatible']
        原因=管理文案(错误)
    if 原因=='':
        原因=中文句('reasonOperationError')
    return 中文句(失败键[提示['action']],{'reason':原因})
