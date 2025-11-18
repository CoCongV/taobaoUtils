from flask_restful import Resource, reqparse
from flask_praetorian import auth_required, current_user
from taobaoutils.app import db
from taobaoutils.models import ProcessTask
import pandas as pd
from pathlib import Path
import os


class ProcessResource(Resource):
    method_decorators = [auth_required]  # 为整个资源添加认证保护
    
    def get(self):
        """获取当前用户的所有处理任务"""
        parser = reqparse.RequestParser()
        parser.add_argument('status', type=str, help='Filter by status')
        args = parser.parse_args()
        
        # 只获取当前用户的任务
        user = current_user()
        query = ProcessTask.query.filter_by(user_id=user.id)
        
        if args['status']:
            query = query.filter_by(status=args['status'])
            
        tasks = query.all()
            
        return {'tasks': [task.to_dict() for task in tasks]}, 200
    
    def post(self):
        """创建新处理任务"""
        parser = reqparse.RequestParser()
        parser.add_argument('url', type=str, required=True, help='URL is required')
        parser.add_argument('status', type=str, default='pending')
        args = parser.parse_args()
        
        # 关联当前用户
        user = current_user()
        task = ProcessTask(
            url=args['url'],
            status=args['status'],
            user_id=user.id
        )
        
        db.session.add(task)
        db.session.commit()
        
        return {'message': 'Task created successfully', 'task': task.to_dict()}, 201


class StatusResource(Resource):
    method_decorators = [auth_required]  # 为整个资源添加认证保护
    
    def get(self):
        """获取当前用户系统状态"""
        user = current_user()
        
        # 只统计当前用户的任务
        total_tasks = ProcessTask.query.filter_by(user_id=user.id).count()
        completed_tasks = ProcessTask.query.filter_by(user_id=user.id, status='completed').count()
        pending_tasks = ProcessTask.query.filter_by(user_id=user.id, status='pending').count()
        
        return {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'pending_tasks': pending_tasks,
            'current_user': user.to_dict() if user else None
        }, 200
