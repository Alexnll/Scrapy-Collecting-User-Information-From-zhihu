# Scrapy爬取知乎用户信息
### 目标
- 从一个大V用户开始，通过递归爬取粉丝列表和关注列表，以实现知乎所有用户详细信息的抓取。
- （可选）将抓取结果储存到数据库中，并进行去重操作。
### 环境需求
- Python3.6

通过miniconda创建python版本号为3.6的虚拟环境
> conda create -n spider python=3.6

> conda activate spider
- Scrapy
> pip install scrapy
>
注意，在安装scrapy框架前，还需安装下列库至虚拟环境中：
1. 安装lxml库(pip)
2. 安装pyOpenSSL库(pip)
3. 安装Twisted库(wheel+pip)
4. 安装PyWin32库(wheel+pip)


### 创建项目
在命令行通过以下命令创建一个项目：
> scrapy startproject zhihu_user

### 创建爬虫
通过命令行进入到项目中，运行genspider命令创建一个spider
> cd zhihu_user

> scrapy genspider zhihu www.zhihu.com

### 禁止ROBOTSTXT_OBEY
将settings.py中的ROBOTSTXT_OBEY设为False：
> ROBOTSTXT_OBEY = False

其默认为True，表示遵守robots.txt规则。 robots.txt 是遵循 Robot 协议的一个文件，它保存在网站的服务器中，它的作用是，告诉搜索引擎爬虫，本网站哪些目录下的网页**不希望**你进行爬取收录。在Scrapy启动后，会在第一时间访问网站的 robots.txt 文件，然后决定该网站的爬取范围。

### 尝试最初的爬取

### 爬取流程分析

### 生成第一步请求

### O Auth

### parse_user

### prase_follows

### followers

### 小结