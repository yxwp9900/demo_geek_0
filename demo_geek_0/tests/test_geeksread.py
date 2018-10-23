# from copy import deepcopy
# import datetime

# from nose import tools

# from tests import BaseTest, en_data
# from geek_digest.common.constant import RawArticleConstant
# from geek_digest.model import RawArticle
# from geek_digest.service.news import NewsService
# from geek_digest.service.translate import translate_articles


# class TestGeeksRead(BaseTest):
#     @classmethod
#     def setup_class(cls, language=RawArticleConstant.LANGUAGE_CN):
#         cls.day = datetime.datetime(2018, 8, 21)
#         cls.en_article = deepcopy(en_data)

#     @tools.nottest
#     def test_sava_to_raw(self, language):
#         """
#         测试保存文章到raw_article

#         1、保存十篇文章
#         2、再存十篇文章
#         3、测试文章的标题和正文是否保存成功
#         """
#         service = NewsService(day=self.day, language=language)
#         count = RawArticle.objects().count()
#         self.test_save(service, count)

#         self.test_save(service, count)
#         for article in RawArticle.objects():
#             if article.language == RawArticleConstant.LANGUAGE_CN:
#                 tools.assert_equals(article.en_title, '')
#                 tools.assert_equals(article.en_content, '')
#                 tools.assert_not_equals(article.cn_title, '')
#                 tools.assert_not_equals(article.cn_content, '')
#                 tools.assert_not_equals(article.cn_summary, '')
#             else:
#                 tools.assert_equals(article.cn_title, '')
#                 tools.assert_equals(article.cn_content, '')
#                 tools.assert_not_equals(article.en_title, '')
#                 tools.assert_not_equals(article.en_content, '')

#         self.delete_articles()

#     @tools.nottest
#     def test_save(self, service, count):
#         raw_article = service.get_news()
#         raw_article['data'] = raw_article['data'][:10]
#         service.save_news_to_db(raw_article)
#         tools.assert_equals(RawArticle.objects().count(),
#                             count + len(raw_article['data']))

#     def test_get_language(self):
#         self.test_sava_to_raw(language=RawArticleConstant.LANGUAGE_CN)
#         self.test_sava_to_raw(language=RawArticleConstant.LANGUAGE_EN)

#     def test_translate_article(self):
#         """
#         测试翻译功能

#         1、存入5篇未翻译的文章，检查能否get到
#         2、翻译存入的文章，检查翻译返回值是否正确
#         """
#         for i in range(5):
#             en_article = RawArticle(**self.en_article)
#             en_article.url = en_article.url + str(i)
#             en_article.save()

#         tools.assert_equals(
#             RawArticle.objects(is_translated=False).count(), 5)
#         en_news = RawArticle.objects(is_translated=False)
#         translate_articles(en_news)
#         for news in en_news:
#             tools.assert_true(news.is_translated)
#             tools.assert_not_equals(news.cn_title, '')
#             tools.assert_is_not_none(news.cn_content)
#             tools.assert_is_not_none(news.cn_summary)
#             news.save()

#         self.delete_articles()
