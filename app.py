from sys import prefix

from flask import Flask, url_for, render_template, request, flash, redirect
from flask import escape
from flask_sqlalchemy import SQLAlchemy
import os
import click
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import *

app = Flask(__name__)

# 设置变量
app.config['SQLALCHEMY_DATABASE_URI'] = prefix + os.path.join(os.path.dirname(app.root_path), os.getenv('DATABASE_FILE', 'data.db'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 关闭对模型修改的监控
app.config['SECRET_KEY'] = ['SECRET_KEY', 'dev']  # flash用密钥
# instance of extend
login_manager = LoginManager(app)
login_manager.login_view = 'login'
db = SQLAlchemy(app)


# 注册命令
@app.cli.command()
@click.option('--drop', is_flag=True, help='Create after drop.')
def initdb(drop):
    if drop:
        db.drop_all()
    db.create_all()
    click.echo('Initialized database.')  # 输出提示信息


# 命令，创建虚拟数据
@app.cli.command()
def forge():
    name = 'Mogu'
    movies = [
        {'title': 'My Neighbor Totoro', 'year': '1988'},
        {'title': 'Dead Poets Society', 'year': '1989'},
        {'title': 'A Perfect World', 'year': '1993'},
        {'title': 'Leon', 'year': '1994'},
        {'title': 'Mahjong', 'year': '1996'},
        {'title': 'Swallowtail Butterfly', 'year': '1996'},
        {'title': 'King of Comedy', 'year': '1999'},
        {'title': 'Devils on the Doorstep', 'year': '1999'},
        {'title': 'WALL-E', 'year': '2008'},
        {'title': 'The Pork of Music', 'year': '2012'},
    ]
    user = User(name=name)
    db.session.add(user)
    for m in movies:
        movie = Movie(title=m['title'], year=m['year'])
        db.session.add(movie)

    db.session.commit()
    click.echo('Done.')


# 设置管理员用户
@app.cli.command()
@click.option('--username', prompt=True, help='The username used to login.')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='The password used to login.')
def admin(username, password):
    db.create_all()

    user = User.query.first()
    if user is not None:
        click.echo('正在更新用户...')
        user.name = username
        user.set_password(password)
    else:
        click.echo('创建用户...')
        user = User(name=username)
        user.set_password(password)
        db.session.add(user)
    db.session.commit()
    click.echo('Done.')


# 继承自db的model，表示一个表
# 继承UserMixin，拥有判断用户状态的很多函数
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def valid_password(self, password):
        return check_password_hash(self.password_hash, password)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(60))
    year = db.Column(db.String(4))


@login_manager.user_loader
# 根据id加载用户
def load_user(user_id):
    user = User.query.get(int(user_id))
    return user


# 模版上下文处理函数
# 这个函数返回的变量（以字典键值对的形式）
# 将会统一注入到每一个模板的上下文环境中，因此可以直接在模板中使用。
@app.context_processor
def inject_user():
    user = User.query.first()
    return dict(user=user)


# 渲染index页面，模版文件名是必须传入参数，其他两个参数为了正确渲染。
# 默认只接收GET，需要扩展POST接收表单
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':

        if not current_user.is_authenticated:
            flash('当前用户未认证')
            return redirect(url_for('index'))

        title = request.form.get('title')
        year = request.form.get('year')
        # 重回主页
        if not title or not year or len(year) != 4 or len(title) > 60:
            flash('错误的输入')
            return redirect(url_for('index'))
        # 保存到数据库
        movie = Movie(title=title, year=year)
        db.session.add(movie)
        db.session.commit()
        flash('创建成功')
        return redirect(url_for('index'))
    # 查询数据库中记录
    # user = User.query.first()
    movies = Movie.query.all()
    return render_template('index.html', movies=movies)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.route('/hello')
@app.route('/home')
def hello_world():  # put application's code here
    return '<h1>Hello Totoro!</h1><img src="http://helloflask.com/totoro.gif">'


# 动态路由传入变量
@app.route('/user/<name>')
def user_page(name):
    # f代表格式化字符串， escape是常见的安全处理
    return f'user: {escape(name)}'


@app.route('/test')
def test_url_for():
    # 下面是一些调用示例（请访问 http://localhost:5000/test 后在命令行窗口查看输出的 URL）：
    print(url_for('hello_world'))  # 生成 hello 视图函数对应的 URL，将会输出：/
    # 注意下面两个调用是如何生成包含 URL 变量的 URL 的
    print(url_for('user_page', name='root'))  # 输出：/user/greyli
    print(url_for('user_page', name='mogu'))  # 输出：/user/peter
    print(url_for('test_url_for'))  # 输出：/test
    # 下面这个调用传入了多余的关键字参数，它们会被作为查询字符串附加到 URL 后面。
    print(url_for('test_url_for', num=2))  # 输出：/test?num=2
    return 'Test page'


# if __name__ == '__main__':
#     app.run()

# 编辑movies
@app.route('/movie/edit/<int:movie_id>', methods=['GET', 'POST'])
@login_required
def edit(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    if request.method == 'POST':
        title = request.form.get('title')
        year = request.form.get('year')
        if not title or not year or len(year) != 4 or len(title) > 60:
            flash('错误的输入')
            return redirect(url_for('edit', movie_id=movie_id))  # 重定向回对应的编辑页面
        movie.title = title  # 更新标题
        movie.year = year  # 更新年份
        db.session.commit()  # 提交数据库会话
        flash('更新成功')
        return redirect(url_for('index'))  # 重定向回主页
    return render_template('edit.html', movie=movie)


@app.route('/movie/delete/<int:movie_id>', methods=['GET', 'POST'])
@login_required
def delete(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    db.session.delete(movie)
    db.session.commit()
    flash('删除成功')
    return redirect(url_for('index'))


# 登陆界面
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.first()

        # 验证
        if user.name == username and user.valid_password(password):
            login_user(user)
            flash('Login success.')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.')
            return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/logout')
@login_required  # 装饰器 view保护
def logout():
    logout_user()
    flash('Goodbye.')
    return redirect(url_for('index'))


@app.route('/setting', methods=['POST', 'GET'])
@login_required
def setting():
    if request.method == 'POST':
        name = request.form['name']

        if len(name) > 20 or not name:
            flash('用户名过长或为空')
            return redirect(url_for('setting'))

        current_user.name = name
        # current_user 会返回当前登录用户的数据库记录对象
        # 等同于下面的用法
        # user = User.query.first()
        # user.name = name
        db.session.commit()
        flash('用户名更新成功')
        return redirect(url_for('index'))
    return render_template('setting.html')
