from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def hello():
    return render_template('index.html')


@app.route('/page1')
def hello_sur():
    name = 'Surmayi'
    return render_template('page1.html', name = name)

@app.route('/bootstrap')
def bootstrap():
    return render_template('bootstrap.html')


#app.run(debug=True)