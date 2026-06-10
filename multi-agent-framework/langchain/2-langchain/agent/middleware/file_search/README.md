# FilesystemFileSearchMiddleware

"""Provides Glob and Grep search over filesystem files."""

顾名思义，为filesystem files.提供检索工具

## premable

初始化给了三个参数，文件路径，是否用 rg 命令， max_file_size_mb: int = 10, 能搜索的最大文件

## 规定的工具

### def glob_search(pattern: str, path: str = "/") -> str:


### def grep_search(pattern: str,path: str = "/",include: str | None = None,output_mode: Literal["files_with_matches", "content", "count"] = "files_with_matches",) -> str:

看下来也没撒好说的

