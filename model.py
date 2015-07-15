#coding:utf-8
from sqlalchemy import create_engine, ForeignKey, Column, Integer, String, \
    SmallInteger, Table, and_, Enum, Boolean
from sqlalchemy.orm import relationship, backref, sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from conf.util import sql_user, sql_password


engine = create_engine('mysql://%s:%s@127.0.0.1:3306/meinv?charset=utf8' % (sql_user, sql_password))
Base = declarative_base()


picture_tag = Table("picture_tag", Base.metadata,
                    Column('picture_id', Integer, ForeignKey('picture.id')),
                    Column('tag_id', Integer, ForeignKey('tag.id'))
                    )


class Picture(Base):
    __tablename__ = 'picture'

    id = Column(Integer, primary_key=True)
    title = Column(String(50), index=True)
    pic_type_id = Column(Integer, ForeignKey('pic_type.id'))
    like = Column(Integer, index=True, default=0)
    click = Column(Integer, index=True, default=0)
    tag = relationship("Tag", secondary=picture_tag, backref="picture")
    active_path_id = Column(Integer, ForeignKey('path.id'))
    index = Column(Boolean, index=True, default=0)
    active_path = relationship("Path", foreign_keys=[active_path_id])


class PicType(Base):
    __tablename__ = 'pic_type'

    id = Column(Integer, primary_key=True)
    name = Column(String(20), index=True)

    picture = relationship("Picture", backref=backref("pic_type"))


class Tag(Base):
    __tablename__ = 'tag'

    id = Column(Integer, primary_key=True)
    name = Column(String(40), index=True)


class Path(Base):
    __tablename__ = 'path'

    id = Column(Integer, primary_key=True)
    path_ = Column(String(80), index=True)
    picture_id = Column(Integer, ForeignKey('picture.id'))

    picture = relationship("Picture", foreign_keys=[picture_id], backref=backref("path"))


db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))

Base.query = db_session.query_property()

if __name__ == '__main__':
    #Base.metadata.create_all(engine)
    new_pic = Picture(title=100, pic_type_id=900)
    db_session.add(new_pic)
    db_session.commit()
