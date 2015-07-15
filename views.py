#coding:utf-8
from flask import Flask, session, redirect, url_for, request, flash, render_template, Markup, g, jsonify, \
    stream_with_context, Response, abort
from backtask.download import upload_and_db, soup_pic
from model import *
from wtforms import Form, BooleanField, TextField, PasswordField, validators, StringField, SelectField, RadioField


app = Flask(__name__)
app.secret_key = 'ddddddaaaaaaaaaaaaa---11111111'


@app.teardown_request
def handle_teardown_request(excetion):
    db_session.remove()


@app.route('/', methods=['GET', 'POST'])
def index():
    pictures = db_session.query(Picture).filter(Picture.index).limit(100)
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
        except AttributeError as e:
            return jsonify({'good': '2', 'msg': e.message})
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
    picture = db_session.query(Picture).get(picture_id)
    types = db_session.query(PicType).all()
    class SettingForm(Form):
        del_pic = BooleanField(u'是否删除本页面？', [validators.required()], default=False)
        index_pic = BooleanField(u'设置本组图片首页？', [validators.required()], default=picture.index)
        active_path = RadioField(u'选择一个图片作为前台',[validators.required()],
                                 choices=[(path.id, "<img src="+path.path_+"?imageView2/2/w/80/h/80>") for path in picture.path],
                                 default=picture.active_path_id if picture.active_path_id else picture.path[0].id)
        pic_type = RadioField(u'选择图片组类型', [validators.required()],
                              choices=[(_pic_type.id, _pic_type.name) for _pic_type in types],
                              default=picture.pic_type_id if picture.pic_type_id else types[0].id)
    if request.remote_addr != '127.0.0.1':
        abort(404)
    else:
        form = SettingForm(request.form)
        if request.method == 'GET':
            return render_template('setting.html', picture=picture, form=form)
        elif request.method == 'POST':
            if form.del_pic.data:
                db_session.query(Path).filter(Path.picture_id == picture_id).delete()
                db_session.query(Picture).filter(Picture.id == picture_id).delete()
            else:
                picture.index = form.index_pic.data
                picture.active_path_id = form.active_path.data
                picture.pic_type_id = form.pic_type.data
            db_session.commit()
            return redirect(url_for('index'))



@app.route('/type', methods=['POST', 'GET'])
def type_():
    types = db_session.query(PicType).all()
    if request.method == 'GET':
        return render_template('type.html', types=types)
    elif request.method == 'POST':
        del_type_ids = request.get_json()['2']
        for del_type_id in del_type_ids:
            db_session.query(PicType).filter(PicType.id == del_type_id).delete()
        db_session.commit()
        return redirect(url_for('type_'))


@app.route('/addtype', methods=['POST'])
def addtype():
    if request.method == 'GET':
        abort(404)
        redirect(url_for('index'))
    elif request.method == 'POST':
        new_type = request.form['type']
        db_session.add(PicType(name=new_type))
        db_session.commit()
        return redirect(url_for('type_'))


@app.route('/showtype/<int:type_id>')
def showtype(type_id):
    pictures = db_session.query(Picture).filter(Picture.pic_type_id == type_id).all()
    return render_template('showtype.html', pictures=pictures)


if __name__ == '__main__':
    app.run(debug=True)
