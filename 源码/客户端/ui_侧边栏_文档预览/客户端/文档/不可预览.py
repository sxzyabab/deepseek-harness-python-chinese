from .后缀 import 文档文件名,匹配后缀长度#文件名与后缀长度

__all__=['不可预览二进制扩展名','不可预览二进制路径']#仅中文公开名

不可预览二进制扩展名=(#无渲染器的已知二进制容器后缀
    'mp4','mov','avi','mkv','webm','flv','wmv','m4v',#视频
    'mp3','wav','flac','ogg','m4a','aac','wma','opus',#音频
    'zip','gz','tgz','bz2','xz','zst','7z','rar','tar','jar',#归档
    'doc','docx','xls','xlsx','ppt','pptx','odt','ods','odp','pages','numbers',#办公文档；key 不列入以免撞密钥文本
    'exe','dll','so','dylib','bin','o','class','pyc','wasm',#可执行与编译物
    'ttf','otf','woff','woff2','eot',#字体
    'dmg','iso','img','sqlite','db',#磁盘镜像与数据库
    'psd','ai','sketch','tiff','tif','heic','heif','avif',#设计稿与无渲染器图像
)#后缀结束

def 不可预览二进制路径(路径):
    """文件名后缀是否落在无渲染器认领的二进制容器表上。"""
    return 匹配后缀长度(文档文件名(路径),不可预览二进制扩展名)>0#有命中
