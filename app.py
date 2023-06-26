from flask import Flask, url_for
from flask import escape

app = Flask(__name__)


@app.route('/')
@app.route('/hello')
@app.route('/home')
def hello_world():  # put application's code here
    return '<h1>Hello Totoro!</h1><img src="http://helloflask.com/totoro.gif">'


# 动态路由传入变量
@app.route('/user/<name>')
def user_page(name):
    #f代表格式化字符串， escape是常见的安全处理
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
