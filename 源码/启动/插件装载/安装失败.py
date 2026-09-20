"""按退出方式与输出尾部分类一次失败的 pnpm 运行。"""
import re

__all__=['分类安装失败']

#日志模式按判定顺序：具体码先于泛网络族
日志种类表=[
    ('build-blocked',re.compile(r'ERR_PNPM_IGNORED_BUILDS|Ignored build scripts',re.ASCII)),
    ('not-found',re.compile(r'ERR_PNPM_FETCH_404|\bE404\b|404 Not Found|Not Found - GET',re.ASCII)),
    ('no-matching-version',re.compile(r'ERR_PNPM_NO_MATCHING_VERSION|\bETARGET\b|No matching version',re.ASCII)),
    ('disk-full',re.compile(r'\bENOSPC\b|no space left on device',re.IGNORECASE|re.ASCII)),
    ('permission',re.compile(r'\bEACCES\b|\bEPERM\b|permission denied',re.IGNORECASE|re.ASCII)),
    ('integrity',re.compile(r'ERR_PNPM_TARBALL_INTEGRITY|ERR_PNPM_BAD_TARBALL_SIZE|\bEINTEGRITY\b',re.ASCII)),
    ('network',re.compile(r'\bENOTFOUND\b|\bECONNRESET\b|\bETIMEDOUT\b|\bECONNREFUSED\b|\bEAI_AGAIN\b|ERR_PNPM_META_FETCH_FAIL|ERR_PNPM_FETCH_5\d\d|ERR_PNPM_FETCH_TIMEOUT|socket hang up|Could not resolve host|unable to access',re.ASCII)),
]

def 分类安装失败(事实):
    """分类一次失败运行；事实是 dict，含 log 与可选 cause、timedOut。"""
    if 事实.get('timedOut') is True:
        return 'timeout'
    原因=事实.get('cause')
    if getattr(原因,'errno',None)==2 or getattr(原因,'winerror',None)==2:
        return 'pnpm-missing'
    if getattr(原因,'code',None)=='ENOENT':
        return 'pnpm-missing'
    日志=事实['log'] if 'log' in 事实 else ''
    for 种类,模式 in 日志种类表:
        if 模式.search(日志) is not None:
            return 种类
    return 'unknown'
