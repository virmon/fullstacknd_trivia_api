import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from  sqlalchemy.sql.expression import func
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  CORS(app, resources={r"%/api/%": {"origins": "*"}})

  @app.after_request
  def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,DELETE,OPTIONS')
    return response

  # pagination
  def paginate(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * 10
    end = start + 10

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]
    
    return current_questions

  # get all categories
  @app.route('/categories', methods=['GET'])
  def get_categories():
    categories = Category.query.order_by(Category.type).all()

    if len(categories) == 0:
      not_found(404)

    return jsonify({
      'success': True,
      'categories': Category.toDict(categories)
    })

  #  get all questions
  @app.route('/questions', methods=['GET'])
  def get_questions():
    selection = Question.query.all()
    questions = paginate(request, selection)
    categories = Category.query.order_by(Category.type).all()

    if len(questions) == 0:
      not_found(404)
      
    return jsonify({
      'success': True,
      'questions': questions,
      'total_questions': len(selection),
      'categories': Category.toDict(categories)
    })

  # delete question
  @app.route('/questions/<int:question_id>', methods=['DELETE'])
  def delete_question(question_id):
    question = Question.query.filter(Question.id == question_id).one_or_none()

    if question is None:
      unprocessable(422)
    else:
      question.delete()
      return jsonify({
        'success': True,
        'deleted': question_id
      })
      
  # create new question
  @app.route('/questions', methods=['POST'])
  def create_question():
    post = request.get_json()

    if post.get('searchTerm') is None:
      
      new_question = Question(
        post.get('question'),
        post.get('answer'),
        post.get('difficulty'),
        post.get('category')
      )
      
      new_question.insert()

      return jsonify({
        'success': True
      })

    else:
      search_term = post.get('searchTerm')
      questions = Question.query.filter(Question.question.ilike("%" + search_term + "%")).all()

      return jsonify({
        'success': True,
        'questions': paginate(request, questions),
        'total_questions': len(questions),
      })
  
  # get questions by category
  @app.route('/categories/<int:category_id>/questions', methods=['GET'])
  def get_questions_by_category(category_id):
    selection = Question.query.filter(Question.category == category_id).all()
    questions = paginate(request, selection)

    return jsonify({
      'success': True,
      'questions': questions,
      'total_questions': len(selection),
      'current_category': category_id
    })

  @app.route('/quizzes', methods=['POST'])
  def play():
    post = request.get_json()
    previous_questions = post.get('previous_questions')
    category = post.get('quiz_category')

    if (category['id'] == 0):
      question = Question.query.filter(~Question.id.in_(previous_questions)).first()
    else:
      question = Question.query.order_by(func.random()).filter(Question.category == category['id'], ~Question.id.in_(previous_questions)).first()
      
    if question is None:
      return jsonify({
        'success': True
      })

    return jsonify({
      'success': True,
      'question': question.format()
    })


  # error handlers
  @app.errorhandler(400)
  def bad_request(error):
    return jsonify({
      'success': False,
      'error': 400,
      'message': 'bad request'
    }), 400

  @app.errorhandler(404)
  def not_found(error):
    return jsonify({
      'success': False,
      'error': 404,
      'message': 'resource not found'
    }), 404

  @app.errorhandler(405)
  def method_not_allowed(error):
    return jsonify({
      'success': False,
      'error': 405,
      'message': 'method not allowed'
    }), 405
  
  @app.errorhandler(422)
  def unprocessable(error):
    return jsonify({
      'success': False,
      'error': 422,
      'message': 'unprocessable'
    }), 422

  @app.errorhandler(500)
  def server_error(error):
    return jsonify({
      'success': False,
      'error': 500,
      'message': 'internal server error'
    }), 500

  return app

    