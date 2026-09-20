"""安装规格在交给 pnpm 之前的形态解析。"""
import os,re

__all__=['非法安装规格错误','解析安装规格']

GIT简写=re.compile(r'^(?:github|gitlab|bitbucket|gist):',re.IGNORECASE|re.ASCII)
GIT网址=re.compile(r'^git(?:\+[a-z]+)?:\/\/|^git@[^:]+:',re.IGNORECASE|re.ASCII)
托管仓库网址=re.compile(r'^https?:\/\/[^/]+\/[^/]+\/[^/#]+(?:\.git)?(?:#.*)?$',re.IGNORECASE|re.ASCII)
TARBALL规格=re.compile(r'\.(?:tgz|tar\.gz)(?:#.*)?$',re.IGNORECASE|re.ASCII)
包名模式=re.compile(r'^(?:@[a-z0-9][a-z0-9._~-]*\/)?[a-z0-9][a-z0-9._~-]*$',re.ASCII)
包名最大长度=214

class 非法安装规格错误(Exception):
    """pnpm 与注册表都不会接受的规格；reason 给人读。"""
    def __init__(自身,规格,理由):
        """记下修剪后的规格与一句拒绝理由。"""
        super().__init__('plugin-manager: '+理由+': '+规格)
        自身.name='InvalidInstallSpecError'
        自身.spec=规格
        自身.reason=理由

def 构造非法(规格,理由):
    """构造拒绝。"""
    return 非法安装规格错误(规格,理由)

def 解析安装规格(原始):
    """读出规格形态。路径必须绝对：浏览器工作目录对人不成立，相对路径若相对配置档会指进配置档内。"""
    规格=原始.strip()
    if 规格=='':
        raise 构造非法(规格,'包规格不能为空')
    路径=re.sub(r'^(?:file|link):','',规格,count=1)
    if 路径!=规格 or os.path.isabs(路径):
        if not os.path.isabs(路径):
            raise 构造非法(规格,'本地路径必须是绝对路径')
        if TARBALL规格.search(路径) is not None:
            return {'kind':'tarball','spec':规格,'path':路径}
        return {'kind':'path','spec':规格,'path':路径}
    if re.search(r'^\.{1,2}(?:[\\/]|$)',规格) is not None:
        raise 构造非法(规格,'本地路径必须是绝对路径')
    是git=(GIT简写.search(规格) is not None) or (GIT网址.search(规格) is not None) or (托管仓库网址.search(规格) is not None)
    if 是git and TARBALL规格.search(规格) is None:
        return {'kind':'git','spec':规格}
    if re.search(r'^https?:\/\/',规格,re.IGNORECASE|re.ASCII) is not None:
        if TARBALL规格.search(规格) is not None:
            return {'kind':'tarball','spec':规格}
        raise 构造非法(规格,'URL 必须指向 git 仓库或 tarball')
    艾特=规格.find('@',1)
    名称=规格 if 艾特==-1 else 规格[:艾特]
    范围=None if 艾特==-1 else 规格[艾特+1:]
    if len(名称)>包名最大长度 or 包名模式.search(名称) is None:
        raise 构造非法(规格,'不是注册表接受的包名')
    if 范围=='':
        raise 构造非法(规格,'@ 后面的版本不能为空')
    if 范围 is None:
        return {'kind':'registry','spec':规格,'name':名称}
    return {'kind':'registry','spec':规格,'name':名称,'range':范围}
