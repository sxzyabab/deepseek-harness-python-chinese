"""安装规格在交给 pnpm 之前的形态解析。"""
import os,re#绝对路径与规格形态

__all__=['非法安装规格错误','解析安装规格']#仅中文公开名

#pnpm 经 git 宿主解析的形态
GIT简写=re.compile(r'^(?:github|gitlab|bitbucket|gist):',re.IGNORECASE|re.ASCII)#宿主简写
GIT网址=re.compile(r'^git(?:\+[a-z]+)?:\/\/|^git@[^:]+:',re.IGNORECASE|re.ASCII)#git URL
托管仓库网址=re.compile(r'^https?:\/\/[^/]+\/[^/]+\/[^/#]+(?:\.git)?(?:#.*)?$',re.IGNORECASE|re.ASCII)#托管仓
TARBALL规格=re.compile(r'\.(?:tgz|tar\.gz)(?:#.*)?$',re.IGNORECASE|re.ASCII)#tarball
包名模式=re.compile(r'^(?:@[a-z0-9][a-z0-9._~-]*\/)?[a-z0-9][a-z0-9._~-]*$',re.ASCII)#npm 包名
包名最大长度=214#npm 包名上限

class 非法安装规格错误(Exception):
    """pnpm 与注册表都不会接受的规格；reason 给人读。"""
    def __init__(自身,规格,理由):
        """记下修剪后的规格与一句拒绝理由。"""
        super().__init__('plugin-manager: '+理由+': '+规格)#英文消息
        自身.name='InvalidInstallSpecError'#错误名
        自身.spec=规格#原规格
        自身.reason=理由#拒绝理由

def 构造非法(规格,理由):
    """构造拒绝。"""
    return 非法安装规格错误(规格,理由)#拒绝

def 解析安装规格(原始):
    """读出规格形态。路径必须绝对：浏览器工作目录对人不成立，相对路径若相对配置档会指进配置档内。"""
    规格=原始.strip()#修剪
    if 规格=='':#空
        raise 构造非法(规格,'the package spec must not be empty')#拒绝
    路径=re.sub(r'^(?:file|link):','',规格,count=1)#去掉 file/link 前缀
    if 路径!=规格 or os.path.isabs(路径):#带前缀或已绝对
        if not os.path.isabs(路径):#相对
            raise 构造非法(规格,'a local path must be absolute')#拒绝
        if TARBALL规格.search(路径) is not None:#tarball
            return {'kind':'tarball','spec':规格,'path':路径}#tarball
        return {'kind':'path','spec':规格,'path':路径}#路径
    if re.search(r'^\.{1,2}(?:[\\/]|$)',规格) is not None:#相对点路径
        raise 构造非法(规格,'a local path must be absolute')#拒绝
    是git=(GIT简写.search(规格) is not None) or (GIT网址.search(规格) is not None) or (托管仓库网址.search(规格) is not None)#git 形态
    if 是git and TARBALL规格.search(规格) is None:#纯 git
        return {'kind':'git','spec':规格}#git
    if re.search(r'^https?:\/\/',规格,re.IGNORECASE|re.ASCII) is not None:#http(s)
        if TARBALL规格.search(规格) is not None:#tarball URL
            return {'kind':'tarball','spec':规格}#tarball
        raise 构造非法(规格,'a URL must point at a git repository or a tarball')#拒绝
    艾特=规格.find('@',1)#scoped 后的 @
    名称=规格 if 艾特==-1 else 规格[:艾特]#包名
    范围=None if 艾特==-1 else 规格[艾特+1:]#版本范围
    if len(名称)>包名最大长度 or 包名模式.search(名称) is None:#非法名
        raise 构造非法(规格,'not a package name the registry accepts')#拒绝
    if 范围=='':#空范围
        raise 构造非法(规格,'a version after @ must not be empty')#拒绝
    if 范围 is None:#无范围
        return {'kind':'registry','spec':规格,'name':名称}#注册表
    return {'kind':'registry','spec':规格,'name':名称,'range':范围}#带范围
