'安装规格在交给 pnpm 之前的形态解析'
import os,re

__all__=['非法安装规格错误','解析安装规格','git主机','依赖规格']

GIT简写=re.compile(r'^(?:github|gitlab|bitbucket|gist):',re.IGNORECASE|re.ASCII)
GIT网址=re.compile(r'^git(?:\+[a-z]+)?:\/\/|^git@[^:]+:',re.IGNORECASE|re.ASCII)
托管仓库网址=re.compile(r'^https?:\/\/[^/]+\/[^/]+\/[^/#]+(?:\.git)?(?:#.*)?$',re.IGNORECASE|re.ASCII)
GIT简写主机={'github':'github.com','gitlab':'gitlab.com','bitbucket':'bitbucket.org','gist':'gist.github.com'}
GIT简写捕获=re.compile(r'^([a-z]+):',re.IGNORECASE|re.ASCII)
GIT用户主机=re.compile(r'^git@([^:]+):',re.IGNORECASE|re.ASCII)
TARBALL规格=re.compile(r'\.(?:tgz|tar\.gz)(?:#.*)?$',re.IGNORECASE|re.ASCII)
包名模式=re.compile(r'^(?:@[a-z0-9][a-z0-9._~-]*\/)?[a-z0-9][a-z0-9._~-]*$',re.ASCII)
包名最大长度=214
非注册表值=re.compile(r'^(?!(?:npm|jsr|workspace|catalog):)[a-z][a-z0-9+.-]*:|^[^@/:\s]+@[^:/\s]+:',re.IGNORECASE|re.ASCII)
HTTP用户信息=re.compile(r'^((?:git\+)?https?://)[^/]*@',re.IGNORECASE|re.ASCII)

from .异常 import 非法安装规格错误#非法规格

def 构造非法(规格,理由):
    '构造拒绝'
    return 非法安装规格错误(规格,理由)

def git主机(规格):
    'git 规格克隆自的主机：简写主机、scp 形态或 URL 主机'
    from urllib.parse import urlparse
    简写=GIT简写捕获.match(规格)
    if 简写 is not None:
        名=简写.group(1).lower()
        if 名 in GIT简写主机:
            return GIT简写主机[名]
    scp=GIT用户主机.match(规格)
    if scp is not None:
        return scp.group(1).lower()
    return urlparse(re.sub(r'^git\+','',规格,count=1,flags=re.IGNORECASE|re.ASCII)).netloc

def 解析安装规格(原始):
    '读出规格形态。路径必须绝对：浏览器工作目录对人不成立，相对路径若相对配置档会指进配置档内'
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
        return {'kind':'git','spec':规格,'host':git主机(规格)}
    if re.search(r'^https?:\/\/',规格,re.IGNORECASE|re.ASCII) is not None:
        if TARBALL规格.search(规格) is not None:
            from urllib.parse import urlparse
            return {'kind':'tarball','spec':规格,'host':urlparse(规格).netloc}
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

def 依赖规格(名称,已记,配置目录,包名=None):
    '配置清单记下的依赖值收成 pnpm add 接受的规格'
    if 包名 is None:
        包名=名称
    本地=re.search(r'^(file|link):(.*)$',已记,re.DOTALL|re.ASCII)
    if 本地 is not None:
        路径=本地.group(2)
        if 路径=='~' or 路径.startswith('~/') or 路径.startswith('~\\'):
            路径=os.path.expanduser('~')+路径[1:]
        规格=本地.group(1)+':'+os.path.abspath(os.path.join(配置目录,路径))
    elif 非注册表值.search(已记) is not None:
        规格=HTTP用户信息.sub(r'\1',已记,count=1)
    else:
        return 名称+'@'+已记
    if 包名==名称:
        return 规格
    return 名称+'@'+规格
