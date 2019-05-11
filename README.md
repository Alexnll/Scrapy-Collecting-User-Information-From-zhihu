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
```python
ROBOTSTXT_OBEY = False
```
其默认为True，表示遵守robots.txt规则。 robots.txt 是遵循 Robot 协议的一个文件，它保存在网站的服务器中，它的作用是，告诉搜索引擎爬虫，本网站哪些目录下的网页**不希望**你进行爬取收录。在Scrapy启动后，会在第一时间访问网站的 robots.txt 文件，然后决定该网站的爬取范围。

### 加入请求头
未加入请求头headers中的User-Agent。访问知乎域名下的网页必须指定User-Agent，否则会被服务器检测为爬虫而遭封杀
添加方案：
1. 在settings.py文件中设置，取消DEFAULT_REQUEST_HEADERS的注释，加入如下内容（全局设置）：
```python
DEFAULT_REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
}
```
2. 在创建spider中加入：
```python
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36',
}
```
3. 在Request的参数中加入。

本次爬取使用方案一。添加后在命令行中运行如下命令：
> scrapy crawl zhihu

即可得到返回（200）的结果。未添加时，则会出现返回状态码出错的问题。
同时会出现重定向状态码（301）/（302），这是由于自动创建的爬虫的url开头为http而非https。

### 爬取流程分析
为探寻获取用户详细信息和关注列表的接口，回到网页并检查网页，打开控制台切换到Network模式。


选取一个知乎大V作为爬取开头，如：
> https://www.zhihu.com/people/excited-vczh

通过观察个人信息页面，确定需要爬取的基本信息，如：姓名，签名，职业，关注数，赞同数等。
> 注：Ajax，即Asynchronous JavaScript and XML，指异步的JavaScript和XML，指利用JavaScript在保证页面不被刷新、页面链接不改变的情况下与服务器交换数据并更新部分网页的技术。

点击页面内选项卡中的关注，再翻页，可在控制台中发现出现了相应的Ajax请求。这个就是获取关注列表的接口。其形式如：
> followees?include=data...

观察其请求结构（headers），请求方法为GET，URL为https://www.zhihu.com/api/v4/members/excited-vczh/followees?...，后跟了三个参数，分别为include，offset，limit。可以发现，offset为偏移量，limit表示每页数量，结合这两项即可表示当前的页数。include中则是查询参数。

接下来查看返回结果（Preview），包括有data和paging两个字段。data中包含了关注列表的用户信息，每页有20个内容。paging内容中的字段则可用于请求下一页，其中is_end表示当前翻页是否结束，next则是下一页的链接。

由上，我们即可通过接口获取到获取关注列表了。

若将鼠标放在关注列表中的任意一个头像上，则又会出现新的Ajax请求。可以通过Network控制台中看到该次请求的链接为：
> https://www.zhihu.com/api/v4/members/...

后面同样跟了一个include参数，其包含了一些查询参数。在该请求的返回结果（Preview）中几乎可以获得所有详情。因此我们可以通过该接口获取关注列表中的用户的详细信息。

总结：
- 通过请求 https://www.zhihu.com/api/v4/members/{user}/followees?include={include}&offset={offset}&limit={limit} 这样的接口以获取用户的关注列表，其中user为该用户的url_token。
- 通过请求 https://www.zhihu.com/api/v4/members/{user}?include={include} 这样的接口获取用户的详细信息，其中user同样为该用户的url_token。

有了上两条爬取逻辑后，即可开始构造请求。

### 构造请求
##### 1.生成第一步请求
第一步即为请求起始用户（excited-vczh）的基本信息，然后再获取其关注列表。首先在之前创建的spider中删除原本的start_urls，新构造一个格式化的url，将其中一些可变参数提取出来，然后重写start_requsets方法，以生成第一步的请求。

同时，还需要实现两个解析方法parse_user和parse_follow。修改后代码如下：
```python
import scrapy


class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    user_url = 'https://www.zhihu.com/api/v4/members/{user}?include={include}'
    follows_url = 'https://www.zhihu.com/api/v4/members/{user}/followees?include={include}&amp;offset={offset}&amp;limit={limit}'
    
    start_user = 'exicted-vczh'
    user_query = 'locations,employments,gender,educations,business,voteup_count,thanked_Count,follower_count,following_count,cover_url,following_topic_count,following_question_count,following_favlists_count,following_columns_count,answer_count,articles_count,pins_count,question_count,commercial_question_count,favorite_count,favorited_count,logs_count,marked_answers_count,marked_answers_text,message_thread_token,account_status,is_active,is_force_renamed,is_bind_sina,sina_weibo_url,sina_weibo_name,show_sina_weibo,is_blocking,is_blocked,is_following,is_followed,mutual_followees_count,vote_to_count,vote_from_count,thank_to_count,thank_from_count,thanked_count,description,hosted_live_count,participated_live_count,allow_message,industry_category,org_name,org_homepage,badge[?(type=best_answerer)].topics'
    follows_query = 'data[*].answer_count,articles_count,gender,follower_count,is_followed,is_following,badge[?(type=best_answerer)].topics'

    def start_requests(self):
        yield scrapy.Request(self.user_url.format(user=self.start_user, include=self.user_query), self.parse_user)
        yield scrapy.Request(self.follows_url.format(user=self.start_user, include=self.follows_query, limit=20, offset=0), self.parse_follows)

    def parse_user(self, response):
        print(response.text)
    
    def parse_follows(self, response):
        print(response.text)

```
修改完后即可通过在命令行运行下属命令运行，并观察结果：
> scrapy crawl zhihu
##### 2.解决O Auth问题

##### 3.parse_user

##### 4.prase_follows

##### 5.prase_followers

### 小结