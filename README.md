# Real Time Project

# Directory Structure

  - **real-time/glove/**
    - **bno055_cal.dat** - IMU calibration data.
    - **cal_test.py** - Utility script used to get and test calibration data.
    - **collect_training_data.py** - Utility script used to gather training data for random forest classifier.
    - **demo1_glove.py** - Demo 1 glove script.
    - **demo2_glove.py** - Demo 2 glove script.
    - **demo3_glove.py** - Final demo script. Gathers and pre-processes sensor data from the glove then publishes it when commanded. Uses AWS IoT to subscribe to control topic and publish data topic.
    - **get_avg_flex_val.py** - Utility script used to get average resistance at various states of flexion for mapping function.
    - **glove_start.py** - Test script that sends glove control topic with start command.
    - **glove_stop.py** - Test script that sends glove control topic with stop command.
  - **real-time/learn/**
    - **cloud_start.py** - Test script that sends cloud control topic command.
    - **demo_cloud.py** - Cloud demo script. Builds a random forest classifier with optimized hyperparameters on the training data, classifies incoming glove data, sends classified result to the frontend over AWS IOT.
    - **hyperparameter_optimization.py** - Utility script that performs hyperparameter optimization on training data for random forest classifier and k-nearest neighbors.
    - **training data/** - Contains glove training data csv files for random forest classifier.
  - **real-time/web-app/**
    - **real-time/webapp/backend/**
      - **backend.py** - Flask server that publishes and subscribes to topics based on requests from frontend.
      - **backend_sub.py** - Subscription script called by backend.py which runs on a separate thread.
    - **real-time/webapp/public/**
      - **css/**
        - **styles.css** - Custom styles outside Bootstrap library.
      - **js/**
        - **index.js** - Javascript functions called from the HTML.
      - **index.html** - Main UI webpage.
      - ***hand_data.txt*** - Temp file written to during the subscription process. Not included in repository.
    - **.eslintrc.json, package-lock.json, package.json** - Specify configuration information that is read automatically on build/boot.
    - **server.js** - Node.js launches this script which creates a node for the app to run on.

# Dependencies

## Cloud
 - python 3
 - `pip install sklearn`
 - `pip install AWSIoTPythonSDK`
 - AWS EC2 Instance

## Front End

### Front End UI
  - Node.js
  - `npm install jquery semantic-ui-css handlebars vanilla-router express dotenv axios`

### Backend Server
   - python 3
   - `pip install flask flask-cors AWSIoTPythonSDK`
   
## Glove
  - python 3
  - `pip install adafruit-circuitpython-mcp3xxx AWSIoTPythonSDK gpiozero`
  - Adafruit's old BNO055 python library. Install instructions can be found [here](https://learn.adafruit.com/bno055-absolute-orientation-sensor-with-raspberry-pi-and-beaglebone-black/software).

# Starting Up

## Cloud
 - `cd <PATH_TO_REPO>/learn`
 - For hyperparameter search
   ```
   python3 hyperparameter_optimization.py
   ```
 - To start the Random Forest and subscribe to the glove data
   ```
   python3 demo_cloud.py
   ```

## Front End

### Front End UI
  - Run the below commands
   ```
   cd <PATH_TO_REPO>/web-app
   node server.js OR npm start
   ```
  - App will run on http://localhost:8080/
 
### Backend Server
  - Run the below commands
  ```
  cd <PATH_TO_REPO>/web-app/backend
  set FLASK_APP=backend.py
  flask run
  ```
  - Server will run on http://localhost:5000/

## Glove
  - `python3 demo3_glove.py`
  - This can be run from any folder so long as the path to the script is correct.
