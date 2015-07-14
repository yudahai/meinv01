#coding:utf-8
import threading

import requests
from bs4 import BeautifulSoup
from qiniu import Auth, put_data

from model import Picture, Path, db_session
from conf.util import bucket_name, key_upload, qiniu_url, access_key, secret_key, headers


def produce_consume(threads, MAX_THREADS=50):
    """
    #生产者，消费者模型
    """
    running_threads = []
    condition = threading.Condition()

    def produce():
        while threads:
            condition.acquire()
            if len(running_threads) > MAX_THREADS:
                condition.wait()
            t = threads.pop()
            t.start()
            running_threads.append(t)
            condition.release()

    def consume():
        while True:
            condition.acquire()
            [running_threads.remove(t) for t in running_threads if not t.isAlive()]
            if len(running_threads) < MAX_THREADS:
                condition.notify()
            condition.release()
            if len(running_threads) == 0:
                break

    t_produce = threading.Thread(target=produce)
    t_consume = threading.Thread(target=consume)

    t_produce.start()
    t_consume.start()

    t_produce.join()
    t_consume.join()


def soup_pic(url):
    dispitch = {
        "4493": soup_4493,
        "yesky": soup_yesky,
        "xiaodaimeng": soup_xiaodaimeng
    }

    mid_word = url.split('//')[1].split('/')[0].split('.')[1]
    if mid_word in dispitch.keys():
        return dispitch[mid_word](url)
    else:
        raise AttributeError(u'输入的网址暂时不能解析')


def soup_4493(url):
    """
    http://www.4493.com/的处理过程
    """
    url = '/'.join(url.split('/')[:-1]) + '.htm'
    data = requests.get(url, headers=headers).content.decode('gb2312', errors='ignore')
    soup = BeautifulSoup(data, from_encoding="GBK")
    title = soup.find('div', class_='picmainer').h1.text
    imgs = []
    for img in soup.find('div', class_='picsbox').find_all('img'):
        imgs.append(img['src'])
    return title, imgs


def soup_yesky(url):
    """
    http://pic.yesky.com/的处理过程
    """
    data = requests.get(url, headers=headers).content.decode('gb2312', errors='ignore')
    soup = BeautifulSoup(data, from_encoding="GBK")
    title = soup.find('div', class_='ll_img').h2.text
    imgs = []
    for img in soup.find('div', class_='overview').find_all('img'):
        imgs.append(img['src'].split('_')[0]+'.jpg')
    return title, imgs


def soup_xiaodaimeng(url):
    """
    http://www.xiaodaimeng.net/的处理过程
    """
    data = requests.get(url, headers=headers).content.decode('utf-8', errors='ignore')
    soup = BeautifulSoup(data)
    title = soup.title.text.split('_')[0]
    imgs = []
    for img in soup.find('ul', class_='piclist').find_all('img'):
        if img.get('lazysrc'):
            imgs.append(img['lazysrc'])
    return title, imgs


def upload_and_db(title, imgs):
    """
    把得到的img的url和title上传到七牛，返回的url存入到数据库
    """
    q = Auth(access_key, secret_key)
    new_pic = Picture(title=title)
    db_session.add(new_pic)
    db_session.flush()
    picture_id = new_pic.id

    for img in imgs:
        print img
        data = requests.get(img).content
        new_path = Path(picture=new_pic)
        db_session.add(new_path)
        db_session.flush()
        key_path = key_upload + str(new_path.id)
        mime_type = "image/jpeg"
        token = q.upload_token(bucket_name, key_path)
        ret, info = put_data(token, key_path, data,  mime_type=mime_type, check_crc=True)
        new_path.path_ = qiniu_url + ret['key']

    db_session.commit()
    return picture_id


'''
def download_pic(x):
    """
    从http://www.duo-la.com/meinv/ 解析并存储
    """
    url = 'http://www.duo-la.com/meinv/%d.html' % x
    try:
        resp = urllib2.urlopen(url)
    except HTTPError:
        print url + '打开失败'
        return

    data = resp.read()
    soup = BeautifulSoup(data, 'html.parser')
    title = soup.title
    if title == u'找不到您需要的页面..现在为您返回主页..':
        print "页面为404，返回"
        return
    title = title.text.strip()
    type = soup.find('ul', class_='nav_btns').find('a', class_='on').text.strip()
    picture = Picture(title=title, type=type)
    db_session.add(picture)
    db_session.flush()
    picture_id = picture.id
    db_session.commit()
    download_dirname = os.path.join(download_path, str(picture_id))
    if not os.path.isdir(download_dirname):
        os.mkdir(download_dirname)

    imgs = soup.find('div', class_='img_show').find_all('img')
    x = 1
    for img in imgs:
        resp2 = urllib2.urlopen(img['src'])
        path_ = os.path.join(download_dirname, '%d.jpg') % x
        with open(path_, 'wb') as f:
            f.write(resp2.read())
        x += 1
        db_session.add(Path(picture=picture, path_=path_))
        db_session.commit()
'''


if __name__ == '__main__':
    title, imgs = soup_pic('http://www.xiaodaimeng.net/meit3444ong/5042.html')
    upload_and_db(title, imgs)
