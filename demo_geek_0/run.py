from threading import Timer

import mongoengine
from flask_script import Manager
from flask_apidoc import ApiDoc
from flask_apidoc.commands import GenerateApiDoc
from apscheduler.schedulers.background import BackgroundScheduler

from geek_digest import app, settings
from geek_digest.api import v1  # noqa: F401
from geek_digest.service.translate import translate_all
from geek_digest.service.news import (
    save_geeks_read, delete_aritcles, save_skr_news)
app.config['DEBUG'] = None

# 连接MongoDB
mongoengine.connect(settings.DB_NAME,
                    host=settings.DB_HOST,
                    port=settings.DB_PORT)

# 定义APIdoc
ApiDoc(app=app,
       url_path='/api/docs',
       folder_path='.',
       dynamic_url=False)

manager = Manager(app)
manager.add_command('apidoc',
                    GenerateApiDoc(output_path='./geek_digest/static'))

# 定时翻译文章Service
# Timer(10, translate_all).start()

# 创建后台执行的 schedulers
sched = BackgroundScheduler()

# 添加调度任务
# 添加save_geeks_read任务，触发器选择 cron(周期性)，间隔时长为 20 秒
sched.add_job(save_geeks_read, 'cron', minute=20)
# 添加save_skr_news任务，触发器选择 cron(周期性)，间隔时长为 30 秒
sched.add_job(save_skr_news, 'cron', minute=30)
# 添加delete_aritcles任务，触发器选择 cron(周期性)，间隔时长为 23 秒
sched.add_job(delete_aritcles, 'cron', day_of_week=6, hour=23)

sched.start()

if __name__ == '__main__':
    manager.run()
