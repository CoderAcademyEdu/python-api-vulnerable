from dotenv import load_dotenv, find_dotenv
from flask import Flask, request, g
from flask_restful import abort, Resource, Api
from peewee import *
from playhouse.shortcuts import model_to_dict
import psycopg2
import logging
import os

# Log the SQL
logger = logging.getLogger('peewee')
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

# Database config
db = SqliteDatabase('api.db')

application = Flask(__name__)
api = Api(application)

# Database models
class BaseModel(Model):
    class Meta:
        database = db

class User(BaseModel):
    username = CharField()
    password = CharField()

class Task(BaseModel):
    title = CharField()
    complete = BooleanField()
    user_id = IntegerField()

# Connect to database and create tables
db.connect()
db.create_tables([Task, User])

# Create an admin account
User.get_or_create(username='admin', password='Doggo123!')

# Lookup task by ID
def get_task_by_id(task_id):
    try:
        return Task.get(id=task_id)
    except:
        abort(404, message='Task not found')

# GET & POST /tasks
class API_Tasks(Resource):
    def get(self):
        tasks = Task.select().where(Task.user_id == g.user_id)
        return [model_to_dict(task) for task in tasks]

    def post(self):
        if 'title' not in request.json.keys():
            abort(400, message='Please include a title')
        task = Task.create(title=request.json['title'], complete=False, user_id=g.user_id)
        return model_to_dict(task)

# GET, PUT, DELETE /tasks/:id
class API_Task(Resource):
    def get(self, task_id):
        task = get_task_by_id(task_id)
        application.logger.debug(task)
        return model_to_dict(task)

# Authenticate at the beginning of each request
@application.before_request
def before_request():
    try:
        if request.path != '/':
            username = request.headers['username']
            password = request.headers['password']
            cursor = db.execute_sql("select * from user where username='" + username + "'")
            user = cursor.fetchone()
            user_id = user[0]
            user_password = user[2]
            if password == user_password:
                g.user_id = user_id
            application.logger.info('Found user: ', g.user_id)
    except:
        abort(401)

@application.route('/')
def hello():
    return 'Hello World!'

# Routes
api.add_resource(API_Tasks, '/tasks')
api.add_resource(API_Task, '/tasks/<int:task_id>')

if __name__ == '__main__':
    application.run(debug=True)
