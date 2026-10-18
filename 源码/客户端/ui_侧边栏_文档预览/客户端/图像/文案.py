'图片渲染器的文案。缩放词并进这张表'
from ..缩放.文案 import 中文 as 缩放中文,英文 as 缩放英文

__all__=['中文','英文']

中文={
    **缩放中文,
    'title':'图片',
    'preview':'图片预览：{name}',
    'loading':'文档渲染中...',
    'failed':'无法显示这张图片',
    'unsupported':'图片预览需要完整文件内容',
}

英文={
    **缩放英文,
    'title':'Image',
    'preview':'Image preview: {name}',
    'loading':'Rendering document...',
    'failed':'This image could not be displayed.',
    'unsupported':'Image preview requires the complete file contents.',
}
