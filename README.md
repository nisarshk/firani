# firani

**Pre-Requisites**

​	Apache

​	MySQL

​	Setup of Project in Google console (https://console.developers.google.com/apis/credentials)



**Steps to setup firani :**

* Download and install Anaconda Python (latest version) as suggested by the setup process (https://www.anaconda.com/download/#windows)
* Then open Anaconda Python Application and install below dependencies through pip commands
  * pip install OAuth
  * pip install Flask-OAuthlib
  * pip install PyPDF2
  * pip install mysql-connector
  * pip install --upgrade google-api-python-client
  * pip install six
  * pip install --upgrade oauth2client
* In the Anaconda terminal, go to respective folder (where project setup needed) and clone the project using below command
  * git clone https://github.com/nisarshk/firani.git
* Once Project cloning is completed, 
  * Go to Google console, and select the project.
  * Copy the value from client_id and client_secret and set it as value in credit.py for the variables app.config['GOOGLE_ID'] & app.config['GOOGLE_SECRET'] respectively.
  * Download the JSON secret file to the project path config/client_secret.json (replace the existing file)
  * Edit the file in the path config/db.py for variable **dbConfigLocal** with required DB connection details.

After all the above steps, open terminal in project folder path and execute below command:

​		**python cred.py**

Now open browser and open URL http://127.0.0.1:5000 and login with required account.