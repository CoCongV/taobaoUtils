from flask_restful import Resource, reqparse
from taobaoutils.app import db
from taobaoutils.models import ProcessTask
import pandas as pd
from pathlib import Path
import os

class ProcessResource(Resource):
    def get(self):
        """获取所有处理任务"""
        parser = reqparse.RequestParser()
        parser.add_argument('status', type=str, help='Filter by status')
        args = parser.parse_args()
        
        if args['status']:
            tasks = ProcessTask.query.filter_by(status=args['status']).all()
        else:
            tasks = ProcessTask.query.all()
            
        return {'tasks': [task.to_dict() for task in tasks]}, 200
    
    def post(self):
        """创建新处理任务"""
        parser = reqparse.RequestParser()
        parser.add_argument('url', type=str, required=True, help='URL is required')
        parser.add_argument('status', type=str, default='pending')
        args = parser.parse_args()
        
        try:
            task = ProcessTask(
                url=args['url'],
                status=args['status']
            )
            
            db.session.add(task)
            db.session.commit()
            
            return {'message': 'Task created successfully', 'task': task.to_dict()}, 201
        except Exception as e:
            db.session.rollback()
            return {'message': f'Error creating task: {str(e)}'}, 500

class StatusResource(Resource):
    def get(self):
        """获取系统状态"""
        total_tasks = ProcessTask.query.count()
        completed_tasks = ProcessTask.query.filter_by(status='completed').count()
        pending_tasks = ProcessTask.query.filter_by(status='pending').count()
        
        return {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'pending_tasks': pending_tasks
        }, 200