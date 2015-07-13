#coding:utf-8
from flask import Flask, session, redirect, url_for, request, flash, render_template, Markup, g, jsonify, stream_with_context, Response
from backtask.download import upload_and_db, soup_pic
from model import *


app = Flask(__name__)
app.secret_key = 'ddddddaaaaaaaaaaaaa---11111111'


@app.teardown_request
def handle_teardown_request(excetion):
    db_session.remove()


@app.route('/', methods=['GET', 'POST'])
def index():
    pictures = db_session.query(Picture).limit(100)
    return render_template('index.html', pictures=pictures)


@app.route('/item/<int:picture_id>', methods=['POST', 'GET'])
def item(picture_id):
    picture = db_session.query(Picture).get(picture_id)
    if request.method == 'GET':
        all_tags = db_session.query(Tag).all()
        left_tags = list(set(all_tags) - set(picture.tag))
        return render_template('item.html', picture=picture, left_tags=left_tags)
    elif request.method == 'POST':
        """
        1是为图片组加标签
        2是为图片组删去标签
        3是like
        """
        data = request.get_json()
        if '1' in data.keys():
            for tag_id in data['1']:
                tag_ = db_session.query(Tag).get(int(tag_id))
                picture.tag.append(tag_)
        elif '2' in data.keys():
            for tag_id in data['2']:
                tag_ = db_session.query(Tag).get(int(tag_id))
                picture.tag.remove(tag_)
        elif '3' in data.keys():
            picture.like += 1
        db_session.commit()
        return jsonify({'success': 1})



@app.route('/additem', methods=['POST', 'GET'])
def add_item():
    if request.method == 'GET':
        return render_template('additem.html')
    elif request.method == 'POST':
        url = request.get_json()['url']
        try:
            title, imgs = soup_pic(url)
            picture_id = upload_and_db(title, imgs)
        except:
            return jsonify({'good': '2'})
        return jsonify({'good': '1', 'picture_id': picture_id})


@app.route('/tag', methods=['POST', 'GET'])
def tag():
    if request.method == 'GET':
        tags = db_session.query(Tag).all()
        return render_template('tag.html', tags=tags)
    elif request.method == 'POST':
        tag = request.form['tag']
        db_session.add(Tag(name=tag))
        db_session.commit()
        return redirect(url_for('tag'))



@app.route('/setting/<int:picture_id>', methods=['POST', 'GET'])
def setting(picture_id):
    if request.method == 'GET':
        picture = db_session.query(Picture).get(picture_id)
        return render_template('setting.html', picture=picture)
    elif request.method == 'POST':
        print "pic_index:" + request.form['pic_index']
        print "path_active:" + request.form['path_active']
        print "del_pic:" + request.form['del_pic']
        return redirect(url_for('index'))

'''
@app.route('/picture/<int:path_id>')
def show_picture(path_id):
    path_ = db_session.query(Path).get(path_id).path_
    img = Image.open(path_)
    stream = StringIO.StringIO()
    img.save(stream, "JPEG")
    buf_str = stream.getvalue()
    response = app.make_response(buf_str)
    response.headers['Content-Type'] = 'image/jpg'
    return response
'''


@app.route('/type/<int:type_id>')
def show_type(type_id):
    pictures = db_session.query(Picture).filter(and_(Picture.type == type_id, Picture.path != None, Picture.title != None)).limit(10)
    return render_template('type.html', pictures=pictures)

if __name__ == '__main__':
    app.run(debug=True)
