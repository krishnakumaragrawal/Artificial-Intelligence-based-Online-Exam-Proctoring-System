from flask import Flask, render_template, Response, request, jsonify
from flask_cors import CORS
from backend.db_helper import *
from main import *
import os
import sys

app = Flask(__name__)
CORS(app)

"""
Code for the database backend server. 
"""
#Receiving the sign_up data credientals 
@app.route('/signup_data', methods=['POST'])
def signup_data():
    data = request.get_json()
    # print(data)
    # print(insert_signup(data['signupEmail'], data['username'], data['signupPassword']))
    if((insert_signup(data['signupEmail'], data['username'], data['signupPassword'])) == 1):
        response_data = {'message': 'Data inserted successfully!'}
    else:
        response_data = {'message': 'Error in inserting the Data!'}
    return jsonify(response_data)


#Receiving the login_data credentials
@app.route('/login_data', methods=['POST'])
def login_data():
    data = request.get_json()
    print(data)
    response_data = search_login_credentials(data['email'], data['password'])
    if response_data:
        return jsonify(response_data)   
    return jsonify(response_data = {'message': 'Data not found!'})


#Router to render the index HTML template
@app.route('/')
def index_page():
    return render_template('index.html')


#Router to render the Main Quiz HTML template
@app.route('/quiz_html')
def quix_page():
    return render_template('quiz.html')


#Router to stream video frames
@app.route('/video_feed')
def video_feed():
    return Response(proctoringAlgo(), mimetype='multipart/x-mixed-replace; boundary=frame')


#Router to stop the camera and flask server
@app.route('/stop_camera')
def stop_camera():
    global running
    running = False
    main_app()
    print('Camera and Server stopping.....')
    os._exit(0) 
    return 


#main function
if __name__ == "__main__":
    print("Starting the Python Flask Server.....")
    app.run(port=5000, debug=True)